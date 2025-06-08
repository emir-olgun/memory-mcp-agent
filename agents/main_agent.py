import openai
import re
import os
from dotenv import load_dotenv
from tools.web_search import web_search
from tools.text_analyzer import text_analyzer
from tools.verify_result import verify_result

# Load environment variables from .env file
load_dotenv()

class ReActAgent:
    def __init__(self, api_key: str):
        """Initialize the ReAct agent with OpenAI client."""
        self.client = openai.OpenAI(api_key=api_key)
        self.tools = {}  # We'll add tools here
        self.max_iterations = 10  # Prevent infinite loops
        
        # Automatically register all available tools
        self._register_default_tools()
    
    def add_tool(self, name: str, func, description: str):
        """Add a tool that the agent can use."""
        self.tools[name] = {
            'function': func,
            'description': description
        }

    def _register_default_tools(self):
        """Automatically register all available tools."""
        # Register calculator
        self.add_tool("calculator", calculator, "Evaluates mathematical expressions")
        
        # Register web search
        self.add_tool("web_search", web_search, "Searches the web for current information")
        
        # Register text analyzer
        self.add_tool("text_analyzer", text_analyzer, "Analyzes text statistics and insights")
        
        # Register verification tool
        self.add_tool("verify_result", verify_result, "Verifies if results are reasonable and accurate")


    
    def run(self, question: str) -> str:
        """Main method to run the ReAct loop."""
        # Create system prompt explaining ReAct format
        system_prompt = """You are a helpful assistant that uses tools to answer questions.

You must follow this exact format:
Thought: [your reasoning about what to do next]
Action: [tool_name: tool_input] OR skip if no tool needed
Observation: [tool result will be inserted here by the system]
... (repeat Thought/Action/Observation as needed)
Thought: [final reasoning]
Final Answer: [your final answer to the question]

IMPORTANT RULES:
- For simple greetings, basic questions, or things you can answer directly: skip tools and go straight to Final Answer
- Only use tools when you need to: calculate, search for current info, analyze text, or verify results
- You generate the "Thought:" and "Action:" lines
- The system will automatically add the "Observation:" line with the tool result
- DO NOT write "Observation:" yourself - wait for the system to add it
- After each Action, STOP and wait for the Observation
- Only proceed with the next Thought after receiving an Observation

VERIFICATION GUIDELINES:
SINGLE VERIFICATION (verify once, then proceed):
- Numbers, measurements, statistics, percentages, quantities
- Technical specifications (engine power, performance data, dimensions)
- Historical dates, events, timelines
- Scientific data, research findings, formulas

DOUBLE VERIFICATION (verify twice for critical accuracy):
- Medical information, drug dosages, health claims
- Legal information, regulations, laws, court cases
- Financial data, investment advice, tax information
- Safety information, warnings, hazards, emergency procedures

NO VERIFICATION needed for:
- Simple greetings, basic conversations
- Well-known general knowledge
- Simple calculations with calculator tool

IMPORTANT: After completing the required verifications, accept the results and provide your final answer. Do not continue verifying beyond the specified level.

Available tools (use only when needed):
- calculator: [mathematical expression] - evaluates math expressions
- web_search: [query] - searches the web for current information
- text_analyzer: [text] - analyzes text statistics and provides insights
- verify_result: [description of result to verify] - REQUIRED for numbers, technical specs, legal/medical info, and other critical data

Examples:

Simple greeting:
Question: Hello
Thought: This is a simple greeting that doesn't require any tools.
Final Answer: Hello! I'm here to help you with questions, calculations, web searches, and text analysis. What can I assist you with?

Technical question (single verification):
Question: What is the power of a GE90 engine?
Thought: This asks for technical specifications, which requires single verification.
Action: web_search: GE90 engine horsepower power

[System adds: Observation: GE90 engines produce around 95,000 HP at takeoff]

Thought: I found a power figure. Since this is technical data, I need one verification then proceed.
Action: verify_result: GE90 engine produces 55,000 horsepower

[System adds: Observation: Verification shows values ranging from 55,000-62,000 HP depending on variant]

Thought: One verification complete. The range is 55,000-62,000 HP depending on variant.
Final Answer: GE90 engines produce approximately 55,000-62,000 horsepower depending on the specific variant.

Medical question (double verification):
Question: What is the safe dosage of ibuprofen?
Thought: This is medical information requiring double verification for safety.
Action: web_search: safe ibuprofen dosage adults

[System adds: Observation: 200-400mg every 4-6 hours, max 1200mg daily]

Thought: Found dosage info. Since this is medical, I need first verification.
Action: verify_result: ibuprofen safe dosage 200-400mg every 4-6 hours

[System adds: Observation: Multiple sources confirm 200-400mg range, some say max 3200mg daily]

Thought: First verification done. Need second verification for medical safety.
Action: verify_result: ibuprofen maximum daily dose 1200mg vs 3200mg

[System adds: Observation: OTC limit is 1200mg daily, prescription can go to 3200mg daily]

Thought: Double verification complete. Clear distinction between OTC and prescription limits.
Final Answer: For over-the-counter use, ibuprofen dosage is 200-400mg every 4-6 hours with a maximum of 1200mg per day. Higher doses require medical supervision.

Knowledge question:
Question: What is AI?
Thought: I can answer this directly without needing tools.
Final Answer: AI (Artificial Intelligence) refers to computer systems that can perform tasks typically requiring human intelligence, such as learning, reasoning, and problem-solving.
"""
        
        # Initialize conversation
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question}
        ]
        
        # Main ReAct loop
        for i in range(self.max_iterations):
            # Get response from OpenAI
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=messages,
                temperature=0
            )
            
            assistant_message = response.choices[0].message.content
            messages.append({"role": "assistant", "content": assistant_message})
            
            print(f"\n--- Iteration {i+1} ---")
            print(assistant_message)
            

            
            # Check if we have a final answer
            if "Final Answer:" in assistant_message:
                # Extract and return the final answer
                final_answer = assistant_message.split("Final Answer:")[-1].strip()
                return final_answer
            
            # Look for an action to execute
            action_match = re.search(r"Action:\s*(\w+):\s*(.+)", assistant_message)
            if action_match:
                tool_name = action_match.group(1)
                tool_input = action_match.group(2).strip()
                
                # Execute the tool
                if tool_name in self.tools:
                    observation = self.tools[tool_name]['function'](tool_input)
                    observation_text = f"Observation: {observation}"
                    
                    print(f"Executing {tool_name}: {tool_input}")
                    print(observation_text)
                    
                    # Add observation to conversation
                    messages.append({"role": "user", "content": observation_text})
                else:
                    error_msg = f"Observation: Error - Unknown tool '{tool_name}'"
                    print(error_msg)
                    messages.append({"role": "user", "content": error_msg})
            else:
                # No action found - check if model is trying to continue without tools
                if "Thought:" in assistant_message and "Final Answer:" not in assistant_message:
                    print("🤔 Model is thinking but no action specified. Continuing...")
                    # Let the loop continue to get the next response
                else:
                    print("⚠️ Unexpected response format. Continuing...")
                    # Let the loop continue
        
        return "Max iterations reached without final answer"

def calculator(expression: str) -> str:
    """A simple calculator tool that evaluates mathematical expressions."""
    try:
        # Only allow safe mathematical operations
        allowed_names = {
            '__builtins__': {},
            'abs': abs,
            'round': round,
            'min': min,
            'max': max,
            'pow': pow,
        }
        
        # Evaluate the expression safely
        result = eval(expression, allowed_names)
        return str(result)
        
    except Exception as e:
        return f"Error: {str(e)}"
    
if __name__ == "__main__":
    # Test the calculator first
    print("Testing calculator:")
    print(f"2 + 3 = {calculator('2 + 3')}")
    print(f"10 * 5 = {calculator('10 * 5')}")
    print(f"Invalid: {calculator('import os')}")  # Should error
    
    print("\n" + "="*60)
    print("🤖 ReAct Agent - Interactive Demo")
    print("="*60)
    print("Available tools: Calculator, Web Search, Text Analyzer, Verification")
    print("Type 'quit' to exit")
    
    # Check if SerpAPI is configured
    serpapi_key = os.getenv('SERPAPI_KEY')
    if serpapi_key:
        print("✅ SerpAPI configured - Real-time web search enabled!")
    else:
        print("⚠️  SerpAPI not configured - Using fallback knowledge base")
        print("   To enable real-time web search:")
        print("   1. Get free API key from: https://serpapi.com/")
        print("   2. Set environment variable: export SERPAPI_KEY='your-key-here'")
    
    print("="*60)
    
    # You need to set your OpenAI API key here
    api_key = os.getenv('OPENAI_API_KEY')
    
    if api_key == "your-openai-api-key-here":
        print("❌ Please set your OpenAI API key in the code!")
    else:
        # Create agent (tools are automatically registered)
        agent = ReActAgent(api_key)
        
        print("✅ Agent initialized with verification system!")
        print("\n💡 Example questions you can ask:")
        print("📊 Math: 'What is 25 * 17 + 48?'")
        print("🌍 Geography: 'What is the capital of Nicaragua?'")
        print("📰 Current Events: 'Latest news about AI' (requires SerpAPI)")
        print("🔬 Science: 'What is the speed of light?'")
        print("📝 Text: 'Analyze this text: Hello world!'")
        print("🧮 Mixed: 'Calculate 15% of 250 and tell me about percentages'")
        print("✅ Verification: Agent ALWAYS verifies numbers, technical specs, legal/medical info!")
        
        while True:
            print("\n" + "-"*50)
            question = input("🤔 Your question: ").strip()
            
            if question.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
                
            if not question:
                print("Please enter a question or 'quit' to exit.")
                continue
                
            print(f"\n🔄 Processing: {question}")
            print("="*50)
            
            try:
                answer = agent.run(question)
                print(f"\n🎯 Final Answer: {answer}")
            except Exception as e:
                print(f"❌ Error: {e}")
                print("Try rephrasing your question or check your internet connection.")