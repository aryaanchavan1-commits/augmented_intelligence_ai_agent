# Augmented Intelligence Agent (AugIntel)

A powerful augmented intelligence web application that leverages Groq's LLM API to provide intelligent assistance with workflow automation, featuring secure authentication and conversation history.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

---

## Features

- 🔐 **Secure Authentication** - Username/password login with bcrypt password hashing
- 🤖 **Groq AI Integration** - Powered by Groq's high-speed LLM API
- 💬 **Smart Chat Interface** - Streamed AI responses with conversation history
- ⚡ **Augmented Intelligence Workflow** - Multi-step processing pipeline
- 📊 **Persistent Storage** - SQLite database for conversations and user data
- 📝 **Comprehensive Logging** - Track all activities and errors

---

## Project Structure

```
augmented_intelligence/
├── app.py                 # Main Streamlit application
├── auth.py               # Authentication module
├── groq_agent.py         # Groq API integration
├── workflow.py           # Augmented intelligence workflow
├── database.py           # SQLite database operations
├── logger.py             # Logging configuration
├── requirements.txt      # Python dependencies
├── .env                  # Environment variables (API keys)
├── SPEC.md              # Detailed specification document
├── logs/
│   └── app.log          # Application logs
└── data/
    └── app.db           # SQLite database
```

---

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/aryaanchavan1-commits/augmented_intelligence_ai_agent.git
cd augmented_intelligence_ai_agent
```

### 2. Create Virtual Environment (Recommended)

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the project root with your Groq API key:

```env
GROQ_API_KEY=your_groq_api_key_here
```

> **Note:** Get your free Groq API key at [console.groq.com](https://console.groq.com)

---

## Running the Application

### Start the Application

```bash
streamlit run app.py
```

The application will open in your default browser at `http://localhost:8501`

---

## Default Credentials

| Username | Password |
|----------|----------|
| admin    | admin123 |


---

## How It Works

### Authentication Flow
1. Enter username and password on login page
2. Credentials are validated against hashed values in database
3. Session is created with 30-minute timeout

### Augmented Intelligence Workflow
The agent processes requests through 5 steps:

1. **Input Processing** - Parse and validate user input
2. **Context Gathering** - Retrieve relevant context from conversation history
3. **AI Analysis** - Generate response using Groq's LLM
4. **Workflow Execution** - Execute requested actions
5. **Result Formatting** - Present results with sources and suggestions

### Available Models

| Model | Description |
|-------|-------------|
| llama-3.3-70b-versatile | Latest Llama model, great for general tasks |
| llama-3.1-8b-instant | Fast, efficient for simple tasks |
| gemma2-9b-it | Google's efficient instruction model |
| llama-3.2-1b-instant | Ultra-fast model for simple tasks |
| llama-3.2-3b-instant | Fast model with good performance |

---

## Configuration

### Changing Settings
Access Settings from the sidebar to configure:
- Groq API Key
- Model selection
- Temperature (0.0 - 1.0)
- Max tokens (1 - 4096)

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GROQ_API_KEY` | Your Groq API key | Yes |

---

## Troubleshooting

### Common Issues

**"Groq client not initialized"**
- Make sure your API key is set in the `.env` file
- Configure API key in the app settings

**"I apologize, but I couldn't generate a response"**
- Check that your Groq API key is valid
- Verify you have API credits available

**Database errors**
- Ensure the `data/` directory exists and is writable

### Viewing Logs

```bash
# Windows
type logs\app.log

# Linux/Mac
cat logs/app.log
```

---

## Development

### Adding New Workflow Steps

Edit `workflow.py` and add new steps to the `AugmentedIntelligenceWorkflow` class:

```python
async def step_new_feature(context: WorkflowContext) -> Dict:
    """New workflow step"""
    # Your logic here
    return {"result": "success"}
```

### Adding New Models

Update the `GROQ_MODELS` dictionary in `groq_agent.py`:

```python
GROQ_MODELS = {
    "new-model-id": {
        "name": "New Model Name",
        "context_window": 128000,
        "description": "Model description"
    }
}
```

---

## License

MIT License - See LICENSE file for details

---

## Credits

- [Groq](https://groq.com) - LLM API
- [Streamlit](https://streamlit.io) - Web framework
