
FROM python:3.12-slim

# Configuration Python
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Répertoire de travail
WORKDIR /app

# Création d'un utilisateur non-root
RUN groupadd --system appgroup \
    && useradd --system --gid appgroup appuser

# Copie des dépendances en premier pour profiter du cache Docker
COPY requirements.txt .

# Installation des dépendances
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copie du code de l'application
COPY --chown=appuser:appgroup app/ ./app/
COPY --chown=appuser:appgroup alembic/ ./alembic/
COPY --chown=appuser:appgroup alembic.ini .

# Passage à un utilisateur non privilégié
USER appuser

# Port de l'API
EXPOSE 8000

# Démarrage de FastAPI
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
