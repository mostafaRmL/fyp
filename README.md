# Medical Assistant - AI-Powered Medicine Recommendations

An intelligent web application that analyzes user symptoms using AI and recommends appropriate medicines from pharmaceutical knowledge graphs.

## 🌟 Features

- **AI Symptom Analysis**: Uses Groq LLM (Llama 3.1-70B) to analyze natural language symptom descriptions
- **Knowledge Graph Integration**: Queries Wikidata SPARQL endpoint for pharmaceutical data
- **Medicine Recommendations**: Provides detailed medicine information including:
  - Chemical formula
  - Molecular mass
  - ATC classification codes
  - Medical conditions treated
- **Modern Web Interface**: Clean, responsive UI with real-time feedback
- **Production-Ready**: Robust error handling, validation, and logging

## 🏗️ Architecture

```
┌─────────────────────────────────────┐
│       Frontend (HTML/CSS/JS)        │
│         User Interface              │
└──────────────┬──────────────────────┘
               │ HTTP/JSON
┌──────────────▼──────────────────────┐
│      FastAPI Application            │
│    - Routes & Validation            │
│    - Error Handling                 │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│       Service Layer                 │
│  ┌────────────────────────────┐     │
│  │   LLM Service (Groq)       │     │
│  │   - Symptom Analysis       │     │
│  └────────────┬───────────────┘     │
│               │                     │
│  ┌────────────▼───────────────┐     │
│  │   SPARQL Service           │     │
│  │   - Wikidata Queries       │     │
│  └────────────────────────────┘     │
└─────────────────────────────────────┘
```

## 📁 Project Structure

```
fyp/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app
│   ├── config.py               # Configuration
│   ├── models/
│   │   └── schemas.py          # Pydantic models
│   ├── services/
│   │   ├── llm_service.py      # Groq AI integration
│   │   ├── sparql_service.py   # Wikidata SPARQL
│   │   └── medicine_service.py # Main orchestration
│   ├── api/
│   │   └── routes.py           # API endpoints
│   └── utils/
│       ├── logger.py           # Logging
│       └── validators.py       # Validation
├── static/
│   ├── index.html              # Frontend
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── app.js
├── .env                        # Environment variables
├── requirements.txt            # Dependencies
└── run.py                      # Application runner
```

## 🚀 Installation

### Prerequisites

- Python 3.10 or higher
- Virtual environment (recommended)
- Groq API key (free from https://console.groq.com)

### Setup Steps

1. **Clone or navigate to the project**
   ```bash
   cd fyp
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv venv
   .\venv\Scripts\Activate.ps1  # Windows
   # or
   source venv/bin/activate      # Linux/Mac
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   
   The `.env` file should already contain your Groq API key. Verify it:
   ```
   GROQ_API_KEY=gsk_...
   ```

5. **Run the application**
   ```bash
   python run.py
   ```

6. **Open in browser**
   ```
   http://localhost:8000
   ```

## 🔑 API Endpoints

### Main Endpoints

- **POST `/api/analyze`** - Analyze symptoms and get recommendations
  ```json
  {
    "symptoms": "I have a headache and fever"
  }
  ```

- **GET `/api/search?name=aspirin`** - Search medicines by name

- **GET `/api/medicine/{drug_id}`** - Get medicine details

- **GET `/api/health`** - Health check

- **GET `/docs`** - Interactive API documentation (Swagger)

## 🛠️ Technology Stack

**Backend:**
- FastAPI - Modern web framework
- Pydantic - Data validation
- Groq SDK - LLM integration
- Requests - HTTP client
- Python-dotenv - Environment management

**Frontend:**
- Vanilla HTML/CSS/JavaScript
- Responsive design
- Modern UI/UX

**External Services:**
- Groq AI (Llama 3.1-70B) - Symptom analysis
- Wikidata SPARQL - Pharmaceutical data

## 📊 How It Works

1. **User Input**: User describes symptoms in natural language
2. **AI Analysis**: Groq LLM analyzes symptoms and identifies medical conditions
3. **Data Query**: SPARQL queries Wikidata for medicines treating those conditions
4. **Results**: Display medicines with detailed information
5. **Disclaimer**: Always remind users to consult healthcare professionals

## ⚙️ Configuration

Key settings in `.env`:

```env
# Groq API
GROQ_API_KEY=your_key_here
GROQ_MODEL=llama-3.1-70b-versatile
GROQ_TEMPERATURE=0.3

# Server
HOST=0.0.0.0
PORT=8000
DEBUG=True

# Logging
LOG_LEVEL=INFO
```

## 🧪 Testing

Test API connection:
```bash
curl -X POST http://localhost:8000/api/test-connection
```

Test symptom analysis:
```bash
curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"symptoms": "headache and fever"}'
```

## 📝 Development

**Running in development mode:**
```bash
# With auto-reload
uvicorn app.main:app --reload

# Or
python run.py
```

**View logs:**
- Colored console output in development
- Info/Error/Warning levels
- Request/response tracking

## 🔒 Security Features

- Input validation and sanitization
- XSS protection
- CORS configuration
- Rate limiting ready
- Error handling without exposing internals
- Environment variable protection

## 📋 Medical Disclaimer

**IMPORTANT**: This application is for educational and informational purposes only. It should NOT be used as a substitute for professional medical advice, diagnosis, or treatment. Always consult with a qualified healthcare provider for medical concerns.

## 🤝 Contributing

This is a Final Year Project (FYP). For questions or suggestions, contact the project team.

## 📄 License

Educational project - All rights reserved.

## 🙏 Acknowledgments

- **Wikidata** - Open knowledge graph for pharmaceutical data
- **Groq** - Fast LLM inference
- **FastAPI** - Modern Python web framework

---

**Built with ❤️ for better healthcare information access**