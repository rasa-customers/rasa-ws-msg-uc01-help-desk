# Workshop Use Case 01 - IT Help Desk
An intelligent, Rasa IT support agent that guides users through VPN troubleshooting and automatically creates prioritized ServiceNow tickets when escalation is required.

**Workshop Action Items**
- [ ] Clone/Download this agent locally and run `rasa train`
- [ ] Complete the "happy path" conversation
- [ ] Try a conversation repair pattern
- [ ] Run the e2e tests
- [ ] Launch this agent in Hello Rasa

> [!TIP]
> There is a [**cheatsheet**](#cheatsheet) of Rasa commands at the bottom of this README.

## Clone/Download this agent locally and train your agent
- [ ] Clone or download this agent project locally into your IDE
- [ ] To train your agent, open a terminal window, go inside your project directory, and run `rasa train`
- [ ] The rasa model should train successfully

## Complete the "happy path" conversation
- [ ] Still inside your project directory, run `rasa inspect --debug`
- [ ] The built-in Rasa Inspector should launch and the agent should greet you
- [ ] Try to have the following conversation:

```
BOT:
USER: 
```

## Try a conversation repair pattern

## Run the e2e tests

## Launch this agent in Hello Rasa
- [ ] Create a new flow which handles a another type of IT issue.

[![Launch on Hello Rasa](https://hello.rasa.com/launch.svg)](https://hello.rasa.com/go?repo=rrasa-customers/rasa-ws-msg-uc01-help-desk)  

## Rasa commands

<a name="cheatsheet"></a>
```diff
@@ Cheatsheet @@

+ Train
rasa train
rasa train -c config.yml -d domain

+ Inspect
rasa inspect --debug
rasa inspect --debug --log-file logs.txt

+ Run
rasa run
rasa run actions --debug --auto-reload
rasa run --debug --log-file logs.txt --enable-api --cors "*"

+ Shell
rasa shell --debug

+ E2e
rasa test e2e tests/
```
