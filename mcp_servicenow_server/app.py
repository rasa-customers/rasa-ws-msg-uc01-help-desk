#!/usr/bin/env python3
"""
MCP Server for ServiceNow Service Request Management using FastMCP

Provides tools to:
1. Route user requests to appropriate ServiceNow catalog items
2. Get required variables for catalog items
3. Create service requests in ServiceNow
"""

import os
import requests
import json
import logging
from dotenv import load_dotenv
from openai import OpenAI
from typing import List, Dict, Any
from fastmcp import FastMCP

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- SETUP AND CONFIGURATION ---
load_dotenv()

# Configuration variables loaded from .env
SN_INSTANCE_URL = os.getenv("SN_INSTANCE_URL")
SN_USERNAME = os.getenv("SN_USERNAME")
SN_PASSWORD = os.getenv("SN_PASSWORD")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Create FastMCP server
mcp = FastMCP("ServiceNow MCP Server")

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

# --- SNOW UTILITY FUNCTIONS ---

def get_service_catalog_items() -> List[Dict[str, str]]:
    """Retrieves a broad list of active Service Catalog items for LLM matching."""
    url = f"{SN_INSTANCE_URL}/api/now/table/sc_cat_item"
    params = {
        'sysparm_fields': 'sys_id,name,price,short_description',
    }
    
    logger.info(f"Fetching catalog items from ServiceNow: {url}")
    response = requests.get(url, auth=(SN_USERNAME, SN_PASSWORD), params=params)
    response.raise_for_status()
    items = response.json().get('result', [])
    logger.info(f"Retrieved {len(items)} catalog items from ServiceNow")
    return items

def get_item_variables(item_sys_id: str) -> List[Dict[str, Any]]:
    """
    Retrieves the required variables (fields) for a given catalog item
    by calling the ServiceNow Service Catalog API.
    """
    # ServiceNow endpoint to retrieve variables for a specific catalog item
    # This API returns variables, including their technical name and whether they are mandatory.
    url = f"{SN_INSTANCE_URL}/api/sn_sc/servicecatalog/items/{item_sys_id}/variables"
    
    logger.info(f"Fetching variables for item {item_sys_id} from: {url}")
    
    response = requests.get(url, auth=(SN_USERNAME, SN_PASSWORD), 
                            headers={"Accept": "application/json"})
    
    try:
        response.raise_for_status()
    except requests.HTTPError as e:
        logger.error(f"ServiceNow API Error ({response.status_code}): {response.text}")
        raise
    
    # The response often contains a list of variable objects
    variables_data = response.json().get('result', [])
    
    # Filter and format only the relevant data for LLM extraction
    required_vars = []
    for var in variables_data:
        # Use the technical name (name) and the label (question_text)
        required_vars.append({
            "name": var.get('name'), 
            "label": var.get('question_text'), 
            # Note: The "mandatory" field is often returned as "true" or "false" string
            "mandatory": var.get('mandatory') == 'true' 
        })
    
    return required_vars

def create_service_request_snow(item_sys_id: str, variables: Dict[str, str]) -> str:
    """Creates the Service Request (REQ/RITM) in ServiceNow."""
    url = f"{SN_INSTANCE_URL}/api/sn_sc/servicecatalog/items/{item_sys_id}/order_now"
    
    payload = {
        "sysparm_quantity": "1",
        "variables": variables
    }

    response = requests.post(
        url,
        auth=(SN_USERNAME, SN_PASSWORD),
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    
    response.raise_for_status()
    result = response.json().get('result', {})
    
    request_number = result.get('request_number')
    if request_number:
        return request_number
    else:
        raise Exception(f"Failed to retrieve request number from SNOW response. Details: {result}")

# --- LLM PROCESSING LOGIC ---

def llm_query_processor(prompt: str) -> Dict[str, Any]:
    """Central function to call the LLM and parse the structured JSON response."""
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini", # Use a robust model for reliable JSON output
            messages=[
                {"role": "system", "content": "You are a specialized ServiceNow catalog router and data extractor. Your output MUST be a single, valid JSON object."},
                {"role": "user", "content": prompt}
            ],
            response_format={ "type": "json_object" }
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        logger.error(f"LLM processing failed: {e}")
        raise Exception(f"LLM processing failed: {e}")

# --- TOOL 1: catalog_item_routing ---

@mcp.tool()
def catalog_item_routing(conversation_history: str = "") -> dict:
    """
    Return the list of all the available catalog items in service now.
    """
    catalog_items = get_service_catalog_items()
    return {
        "catalog_items": catalog_items
    }


def get_item_id_by_name(item_name: str) -> str:
    """Retrieves the sys_id of a catalog item by its name."""
    url = f"{SN_INSTANCE_URL}/api/now/table/sc_cat_item"
    params = {
        'sysparm_query': f'name={item_name}',
        'sysparm_fields': 'sys_id',
        'sysparm_limit': 1
    }
    response = requests.get(url, auth=(SN_USERNAME, SN_PASSWORD), params=params)
    response.raise_for_status()
    result = response.json().get('result', [])
    if result:
        return result[0]['sys_id']
    return None

# --- TOOL 2: get_variables ---

@mcp.tool()
def get_variables(catalog_item: str) -> dict:
    """
    Retrieves the required variables (fields) for a given catalog item.
    Args:
        catalog_item: The Name OR the sys_id of the catalog item.
    """
    logger.info(f"Received get_variables request for catalog_item: {catalog_item}")
    
    # Check if catalog_item is a sys_id (32 hex chars)
    import re
    is_sys_id = bool(re.match(r'^[0-9a-f]{32}$', catalog_item))
    
    item_sys_id = catalog_item
    if not is_sys_id:
        logger.info(f"'{catalog_item}' does not look like a sys_id, searching by name...")
        try:
            found_id = get_item_id_by_name(catalog_item)
            if found_id:
                logger.info(f"Found sys_id {found_id} for item '{catalog_item}'")
                item_sys_id = found_id
            else:
                logger.error(f"Could not find catalog item with name: {catalog_item}")
                return {"error": f"Catalog item '{catalog_item}' not found", "variables": []}
        except Exception as e:
             logger.error(f"Error searching for item by name: {str(e)}")
             return {"error": f"Error searching for item '{catalog_item}': {str(e)}", "variables": []}

    try:
        variables = get_item_variables(item_sys_id)
        return {
            "variables": variables
        }
    except Exception as e:
        logger.error(f"Error getting variables for id {item_sys_id}: {str(e)}")
        return {"error": f"Error getting variables: {str(e)}", "variables": []}



# --- TOOL 3: create_service_request ---

@mcp.tool()
def create_service_request(collected_data: str, catalog_item_sys_id: str = None) -> dict:
    """
    Creates the Service Request (REQ/RITM) in ServiceNow. Uses the dynamic sys_id.
    
    Args:
        collected_data: JSON string containing collected variable data
        catalog_item_sys_id: The Name OR the sys_id of the catalog item.
    
    Returns:
        Dictionary containing service_request_id and status
    """
    logger.info(f"Received create_service_request request for item: {catalog_item_sys_id}")
    
    # Parse collected_data if it's a string
    try:
        if isinstance(collected_data, str):
            collected_data_dict = json.loads(collected_data)
        else:
            collected_data_dict = collected_data
    except:
        logger.error("Failed to parse collected_data")
        return {
            "service_request_id": None,
            "status": "error",
            "error": "Failed to parse collected_data"
        }
    
    if collected_data_dict is None:
        logger.error("Failed to parse collected_data properly")
        return {
        "service_request_id": None,
        "status": "error",
        "error": "Invalid collected_data"
        }
    # 1. Retrieve the catalog item's sys_id
    # Check if it's passed as a parameter or in collected_data
    raw_item_id = catalog_item_sys_id or collected_data_dict.get("catalog_item_sys_id")
    
    if not raw_item_id:
        logger.error("Missing 'catalog_item_sys_id'")
        return {
            "service_request_id": None,
            "status": "error",
            "error": "Missing catalog_item_sys_id"
        }
        
    # Check if raw_item_id is a sys_id (32 hex chars) or a name
    import re
    is_sys_id = bool(re.match(r'^[0-9a-f]{32}$', raw_item_id))
    
    item_sys_id = raw_item_id
    if not is_sys_id:
        logger.info(f"'{raw_item_id}' does not look like a sys_id, searching by name...")
        try:
            found_id = get_item_id_by_name(raw_item_id)
            if found_id:
                logger.info(f"Found sys_id {found_id} for item '{raw_item_id}'")
                item_sys_id = found_id
            else:
                logger.error(f"Could not find catalog item with name: {raw_item_id}")
                return {
                    "service_request_id": None,
                    "status": "error",
                    "error": f"Catalog item '{raw_item_id}' not found"
                }
        except Exception as e:
             logger.error(f"Error searching for item by name: {str(e)}")
             return {
                 "service_request_id": None, 
                 "status": "error",
                 "error": f"Error searching for item '{raw_item_id}': {str(e)}"
             }
    
    # 2. Filter variables to keep only ServiceNow fields
    # First retrieve the list of actual technical variables
    try:
        actual_variables = [var['name'] for var in get_item_variables(item_sys_id)]
    except Exception as e:
        logger.error(f"Failed to get item variables: {str(e)}")
        return {
            "service_request_id": None,
            "status": "error",
            "error": f"Failed to get item variables: {str(e)}"
        }
    
    final_variables = {
        k: v for k, v in collected_data_dict.items() 
        if k in actual_variables
    }

    # 3. Call ServiceNow API
    try:
        request_number = create_service_request_snow(item_sys_id, final_variables)
        
        return {
            "service_request_id": request_number,
            "status": "success"
        }
    except requests.HTTPError as e:
        error_message = f"ServiceNow API failed to create request. Detail: {e.response.text[:200] if hasattr(e, 'response') else str(e)}"
        logger.error(error_message)
        return {
            "service_request_id": None,
            "status": "error",
            "error": error_message
        }
    except Exception as e:
        logger.error(f"Internal creation error: {str(e)}")
        return {
            "service_request_id": None,
            "status": "error",
            "error": f"Internal creation error: {str(e)}"
        }



if __name__ == "__main__":
    print("🚀 Starting FastMCP ServiceNow Server with HTTP Transport")
    print("📍 Server will start on http://0.0.0.0:8080")
    print("🔗 Using Streamable HTTP transport")
    print("📋 MCP endpoint: http://0.0.0.0:8080/")
    print("📋 Connect MCP clients to: http://0.0.0.0:8080/")
    
    # Run with streamable HTTP transport
    # Use "/" as path to match Rasa's expected endpoint
    mcp.run(transport="http", host="0.0.0.0", port=8080, path="/")
