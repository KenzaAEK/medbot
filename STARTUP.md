# MedBot Startup Guide

## Prerequisites

1. **Docker & Docker Compose** installed
2. **Or** Python 3.11+ with pip

---

## Option 1: Docker (Recommended)

### Step 1: Start Services

```powershell
# Build and start all services (Ollama + MedBot)
docker-compose up --build
```

This will:
- Start Ollama container on port 11434
- Build and start MedBot Streamlit app on port 8501

### Step 2: Download Mistral Model

In a new terminal:

```powershell
# Enter Ollama container
docker exec -it medbot_ollama bash

# Download Mistral model (inside container)
ollama pull mistral

# Exit container
exit
```

### Step 3: Access MedBot

Open your browser: **http://localhost:8501**

---

## Option 2: Local Development (Without Docker)

### Step 1: Install Ollama

Download and install from: https://ollama.ai

```powershell
# Start Ollama (in separate terminal)
ollama serve

# Download Mistral model (in another terminal)
ollama pull mistral
```

### Step 2: Install Python Dependencies

```powershell
# Create virtual environment (optional but recommended)
python -m venv venv
.\venv\Scripts\activate

# Install requirements
pip install -r requirements.txt

# Download spaCy models
python -m spacy download fr_core_news_sm
python -m spacy download en_core_web_sm
```

### Step 3: Set Environment Variables

Create a `.env` file in the project root:

```env
OLLAMA_BASE_URL=http://localhost:11434
MODEL_NAME=mistral
DEFAULT_LANGUAGE=fr
ONTOLOGY_PATH=data/ontology/medical_ontology.ttl
DATA_PATH=data/processed/consolidated_medical_data.json
```

### Step 4: Run Streamlit App

```powershell
streamlit run app/main.py
```

Access at: **http://localhost:8501**

---

## Testing Individual Components

### Test NLP Processor

```powershell
python src/nlp_processor.py
```

### Test Query Engine

```powershell
python src/query_engine.py
```

### Test LLM Engine

```powershell
python src/llm_engine.py
```

---

## Troubleshooting

### Issue: "Ollama connection failed"

**Solution:**
- Make sure Ollama is running: `docker ps` or check Ollama service
- Verify URL in `.env`: `OLLAMA_BASE_URL=http://localhost:11434`
- For Docker: use `http://ollama:11434` (service name)

### Issue: "Model not found"

**Solution:**
```powershell
# Pull the model
ollama pull mistral

# Or use a different model
ollama pull llama2
```

Then update MODEL_NAME in `.env`

### Issue: "spaCy model not found"

**Solution:**
```powershell
python -m spacy download fr_core_news_sm
python -m spacy download en_core_web_sm
```

### Issue: "Ontology file not found"

**Solution:**
Make sure you've run the data processing:

```powershell
# Process data
python src/data_processing.py

# Build knowledge graph
python src/build_graph.py
```

---

## Production Deployment

### Docker Compose Production

```yaml
# Use production-ready settings
environment:
  - LOG_LEVEL=WARNING
  - STREAMLIT_SERVER_HEADLESS=true
```

### Security Considerations

1. Don't expose Ollama port publicly
2. Add authentication to Streamlit (use streamlit-authenticator)
3. Use HTTPS in production
4. Regularly update dependencies

---

## Next Steps

1. ✅ Start the application
2. ✅ Test with sample symptoms
3. 📝 Complete validation notebook
4. 🧪 Run unit tests
5. 📚 Review documentation

---

## Support

For issues, check:
- Application logs in terminal
- Docker logs: `docker logs medbot_streamlit`
- Ollama logs: `docker logs medbot_ollama`
