# ReAct Agent Chat API

A FastAPI-powered ReAct (Reasoning and Acting) Agent that uses OpenAI's API to automatically determine which tools to use for calculation, web search, and text analysis.

## Features

- **Intelligent Agent**: Automatically determines which tools to use based on your message
- **Multiple Tools**: Calculator, web search (with SerpAPI), and text analyzer
- **Simple API**: Single chat endpoint for all interactions
- **Interactive Documentation**: Automatic Swagger/OpenAPI docs
- **Environment Configuration**: Easy setup with environment variables

## Tools Available (Used Automatically)

The agent will automatically choose the appropriate tools based on your message:

1. **Calculator**: For mathematical expressions and calculations
2. **Web Search**: For real-time information or knowledge base queries  
3. **Text Analyzer**: For text statistics and analysis

## Quick Start

### 1. Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd memory-mcp-agent

# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Setup

Create a `.env` file in the project root:

```env
# Required
OPENAI_API_KEY=your-openai-api-key-here

# Optional (for real-time web search)
SERPAPI_KEY=your-serpapi-key-here
```

**Getting API Keys:**
- **OpenAI API Key**: Get from [OpenAI Platform](https://platform.openai.com/api-keys)
- **SerpAPI Key**: Get free key from [SerpAPI](https://serpapi.com/) (optional)

### 3. Running the Server

```bash
# Run with uvicorn
uvicorn main:app --reload

# Or run directly
python main.py
```

The server will start at `http://localhost:8000`

### 4. Access the API

- **Interactive Docs**: `http://localhost:8000/docs` (Swagger UI)
- **Alternative Docs**: `http://localhost:8000/redoc`
- **Health Check**: `http://localhost:8000/`

## API Endpoints

### POST `/chat`
Chat with the ReAct agent. The agent automatically determines which tools to use.

**Request:**
```json
{
  "message": "What is 25 * 17 + 48 and what is the capital of France?",
  "max_iterations": 10
}
```

**Response:**
```json
{
  "message": "What is 25 * 17 + 48 and what is the capital of France?",
  "response": "25 * 17 + 48 equals 473. The capital of France is Paris."
}
```

### GET `/`
Health check and configuration status

## Usage Examples

### Using cURL

```bash
# Chat with the agent
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "What is 15 * 7 and what is AI?"}'

# Mathematical question
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "Calculate the square root of 144 plus 10"}'

# Search question
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "What is the capital of Japan?"}'
```

### Using Python Requests

```python
import requests

# Chat with the agent
response = requests.post(
    "http://localhost:8000/chat",
    json={"message": "Calculate 25% of 200 and explain what percentages are"}
)
print(response.json())

# Another example
response = requests.post(
    "http://localhost:8000/chat", 
    json={"message": "Analyze this text: FastAPI is amazing for building APIs"}
)
print(response.json())
```

### Using JavaScript/Fetch

```javascript
// Chat with the agent
const response = await fetch('http://localhost:8000/chat', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    message: 'What is the speed of light and how long to travel 1 million meters?'
  })
});
const data = await response.json();
console.log(data);
```

## Example Messages

The agent will automatically determine which tools to use:

### Mathematical Questions
- "What is 15% of 750?"
- "Calculate the area of a circle with radius 5"  
- "What is 2^10 + 5*3?"

### Knowledge Questions
- "What is the capital of Japan?"
- "What is artificial intelligence?"
- "Tell me about the speed of light"

### Text Analysis
- "Analyze this text: 'FastAPI is a modern, fast web framework'"
- "Count the words in: 'Hello world, this is a test'"

### Complex Multi-tool Questions
- "Calculate 25% of 200 and tell me about percentages"
- "What is the capital of France and calculate the time difference if it's 3 PM there?"
- "Search for Python tutorials and analyze this text: 'Python is great'"

### Web Search (requires SerpAPI)
- "What are the latest developments in AI?"
- "Current weather in New York"
- "Latest news about space exploration"

## Project Structure

```
.
├── main.py              # FastAPI application (simplified)
├── react_agent.py       # Original ReAct agent implementation
├── requirements.txt     # Python dependencies
├── .env                # Environment variables (create this)
├── README.md           # This file
└── .gitignore          # Git ignore rules
```

## How It Works

1. **Send a message** to `/chat`
2. **Agent analyzes** your message using ReAct reasoning
3. **Agent determines** which tools are needed (calculator, search, text analyzer)
4. **Agent executes** the appropriate tools automatically
5. **Agent returns** a comprehensive response

## Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | Yes | Your OpenAI API key |
| `SERPAPI_KEY` | No | SerpAPI key for real-time web search |

### Default Behavior

- **Without SerpAPI**: Uses built-in knowledge base for searches
- **With SerpAPI**: Performs real-time web searches  
- **Max Iterations**: Default is 10, configurable per request

## Error Handling

The API includes comprehensive error handling:

- **500**: Server errors (missing API keys, agent failures)
- **422**: Validation errors (invalid request format)

## Development

### Running in Development Mode

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Testing the Original CLI Version

The original command-line interface is still available:

```bash
python react_agent.py
```

## Support

For issues and questions:
1. Check the interactive documentation at `/docs`
2. Review the example usage above
3. Ensure environment variables are properly set
4. Check the health endpoint at `/` for configuration status
