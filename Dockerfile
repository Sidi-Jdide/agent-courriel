# --- Étape 1 : compiler l'application Vue ---
FROM node:22-alpine AS frontend
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# --- Étape 2 : image Python finale (API + fichiers Vue compilés) ---
FROM python:3.13-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY agent/ agent/
COPY api/ api/
COPY main.py connaissances.md ./
COPY --from=frontend /app/frontend/dist frontend/dist

RUN useradd --create-home agent && mkdir -p /app/donnees && chown agent /app/donnees
USER agent
EXPOSE 8000
# Par défaut : mode démo. Pour Gmail : voir docker-compose.yml
CMD ["python", "-m", "api", "--hote", "0.0.0.0", "--demo"]
