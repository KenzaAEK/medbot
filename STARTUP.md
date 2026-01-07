# 🚀 MedBot Startup Guide

This guide describes how to run the MedBot application using Docker.

## 📋 Prerequisites

- **Docker Desktop** installed and running
- **Git** (to clone the repository)

## 🐳 Quick Start with Docker

The application is containerized and ready to run. Environment variables are pre-configured in `docker-compose.yml`.

### 1. Start Services

Open a terminal in the project directory and run:

```powershell
docker-compose up -d
```

This starts:
- **Ollama Service** (LLM Backend) on port 11434
- **MedBot App** (Streamlit UI) on port 8501

### 2. Download LLM Model

**⚠️ Only required on first launch!**

The Ollama container needs the Mistral model to generate responses.

```powershell
docker exec medbot_ollama ollama pull mistral
```

*Note: This download is ~4.1GB and may take a few minutes depending on your internet connection.*

### 3. Access the Application

Open your browser and navigate to:
👉 **[http://localhost:8501](http://localhost:8501)**

---

## 🧪 Running Tests

MedBot comes with a comprehensive test suite (35 tests) to verify system integrity. You can run these directly inside the Docker container.

### Run All Unit Tests
Executes the full test suite (NLP, SPARQL, Integration).

```powershell
docker exec medbot_streamlit pytest tests/ -v
```

### Run Validation Check
Verifies the Knowledge Graph structure and data integrity.

```powershell
docker exec medbot_streamlit python /app/tests/validate_data.py
```

---

## 🛠️ Troubleshooting

**Issue**: "Ollama connection failed" in the app.
**Fix**: Ensure the model is pulled (`step 2`) and the container is running (`docker ps`).

**Issue**: "Model not found".
**Fix**: Run `docker exec medbot_ollama ollama list` to see if `mistral` is present. If not, pull it again.

**Issue**: "Docker volume permission errors".
**Fix**: Restart Docker Desktop.

---

## 🛑 Stopping the Application

To stop all services:

```powershell
docker-compose down
```
