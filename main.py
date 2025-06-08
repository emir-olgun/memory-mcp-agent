from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import os
from agents.main_agent import ReActAgent, calculator, web_search, text_analyzer
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI(
    title="ReAct Agent Chat API",
    description="A FastAPI wrapper for the ReAct (Reasoning and Acting) Agent that automatically determines which tools to use",
    version="1.0.0"
)

# Pydantic models for request/response
class ChatRequest(BaseModel):
    message: str
    max_iterations: Optional[int] = 10

class ChatResponse(BaseModel):
    message: str
    response: str

class HealthResponse(BaseModel):
    status: str
    message: str
    serpapi_configured: bool
    openai_configured: bool
    available_tools: list

# Initialize the agent
agent = None

def get_agent():
    global agent
    if agent is None:
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise HTTPException(status_code=500, detail="OpenAI API key not configured")
        
        agent = ReActAgent(api_key)
        agent.add_tool("calculator", calculator, "Evaluates mathematical expressions")
        agent.add_tool("web_search", web_search, "Searches the web for current information")
        agent.add_tool("text_analyzer", text_analyzer, "Analyzes text statistics and insights")
    
    return agent

@app.get("/", response_model=HealthResponse)
async def root():
    """Health check endpoint with configuration status"""
    serpapi_configured = bool(os.getenv('SERPAPI_KEY'))
    openai_configured = bool(os.getenv('OPENAI_API_KEY'))
    
    return HealthResponse(
        status="healthy",
        message="ReAct Agent Chat API is running",
        serpapi_configured=serpapi_configured,
        openai_configured=openai_configured,
        available_tools=["calculator", "web_search", "text_analyzer"]
    )

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat with the ReAct agent. The agent will automatically determine which tools 
    to use (calculator, web search, text analyzer) based on your message.
    
    Examples:
    - "What is 25 * 17 + 48?" (will use calculator)
    - "What is the capital of France?" (will use web search or knowledge base)
    - "Analyze this text: Hello world" (will use text analyzer)
    - "Calculate 15% of 200 and tell me about percentages" (will use multiple tools)
    """
    try:
        agent = get_agent()
        if request.max_iterations:
            agent.max_iterations = request.max_iterations
        
        response = agent.run(request.message)
        
        return ChatResponse(
            message=request.message,
            response=response
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing message: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 