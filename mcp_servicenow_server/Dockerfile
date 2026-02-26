# Utiliser une image de base Python légère
FROM python:3.11-slim

# Définir le répertoire de travail dans le conteneur
WORKDIR /app

# Copier les dépendances et les installer
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code du serveur
COPY app.py .

# Exposer le port (pour la documentation/debug, mais la communication interne est par nom)
EXPOSE 8080

# Commande de démarrage du serveur MCP
CMD ["python", "app.py"]