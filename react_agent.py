import openai
import re
import requests
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class ReActAgent:
    def __init__(self, api_key: str):
        """Initialize the ReAct agent with OpenAI client."""
        self.client = openai.OpenAI(api_key=api_key)
        self.tools = {}  # We'll add tools here
        self.max_iterations = 10  # Prevent infinite loops
    
    def add_tool(self, name: str, func, description: str):
        """Add a tool that the agent can use."""
        self.tools[name] = {
            'function': func,
            'description': description
        }
    
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
- Only use tools when you need to: calculate, search for current info, or analyze text
- You generate the "Thought:" and "Action:" lines
- The system will automatically add the "Observation:" line with the tool result
- DO NOT write "Observation:" yourself - wait for the system to add it
- After each Action, STOP and wait for the Observation
- Only proceed with the next Thought after receiving an Observation

Available tools (use only when needed):
- calculator: [mathematical expression] - evaluates math expressions
- web_search: [query] - searches the web for current information
- text_analyzer: [text] - analyzes text statistics and provides insights

Examples:

Simple greeting:
Question: Hello
Thought: This is a simple greeting that doesn't require any tools.
Final Answer: Hello! I'm here to help you with questions, calculations, web searches, and text analysis. What can I assist you with?

Tool-requiring question:
Question: What is 15 * 7 + 22?
Thought: I need to calculate 15 * 7 + 22 using the calculator tool.
Action: calculator: 15 * 7 + 22

[System adds: Observation: 127]

Thought: The calculation is complete.
Final Answer: 15 * 7 + 22 equals 127.

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
                model="gpt-4o-mini",
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

def web_search(query: str) -> str:
    """A web search tool that uses SerpAPI with retry logic, or falls back to knowledge base."""
    serpapi_key = os.getenv('SERPAPI_KEY')
    
    if serpapi_key:
        return _search_with_serpapi_retry(query, serpapi_key)
    else:
        return _search_knowledge_base(query)

def _search_with_serpapi_retry(query: str, api_key: str, max_retries: int = 3) -> str:
    """Search using SerpAPI with multiple query formulations if needed."""
    
    # Generate different query variations
    query_variations = [
        query,
        f"{query} definition",
        f"what is {query}",
        f"{query} explained",
        query.replace("power of", "thrust").replace("power", "specifications")
    ]
    
    for attempt, search_query in enumerate(query_variations[:max_retries]):
        try:
            print(f"🔍 Searching: '{search_query}' (attempt {attempt + 1})")
            
            url = "https://serpapi.com/search"
            params = {
                'q': search_query,
                'api_key': api_key,
                'engine': 'google',
                'num': 3
            }
            
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            # Check for answer box first (direct answers)
            if 'answer_box' in data:
                answer_box = data['answer_box']
                if 'answer' in answer_box:
                    return f"Direct answer: {answer_box['answer']}"
                elif 'snippet' in answer_box:
                    return f"Answer: {answer_box['snippet']}"
            
            # Check for knowledge graph (facts about entities)
            if 'knowledge_graph' in data:
                kg = data['knowledge_graph']
                if 'description' in kg:
                    return f"Info: {kg['description']}"
            
            # Get organic search results
            if 'organic_results' in data and len(data['organic_results']) > 0:
                results = []
                for result in data['organic_results'][:2]:
                    if 'snippet' in result and len(result['snippet'].strip()) > 20:
                        results.append(f"• {result['snippet']}")
                
                if results:
                    return f"Search results:\n" + "\n".join(results)
            
            # If this attempt didn't yield good results, try next variation
            print(f"   No good results for '{search_query}', trying different approach...")
            
        except Exception as e:
            print(f"   Error with '{search_query}': {e}")
            continue
    
    # If all SerpAPI attempts failed, fall back to knowledge base
    print("🔄 SerpAPI didn't find good results, checking knowledge base...")
    return _search_knowledge_base(query)


def _search_knowledge_base(query: str) -> str:
    """Search the built-in knowledge base."""
    query_lower = query.lower()
    
    # Geography - capitals
    if "capital" in query_lower:
        capitals = {
            "nicaragua": "Managua",
            "france": "Paris", 
            "germany": "Berlin",
            "japan": "Tokyo",
            "brazil": "Brasília",
            "australia": "Canberra",
            "canada": "Ottawa",
            "italy": "Rome",
            "spain": "Madrid",
            "russia": "Moscow",
            "china": "Beijing",
            "india": "New Delhi",
            "mexico": "Mexico City",
            "argentina": "Buenos Aires",
            "egypt": "Cairo",
            "south africa": "Cape Town, Pretoria, and Bloemfontein",
            "united kingdom": "London",
            "united states": "Washington, D.C.",
            "uk": "London",
            "usa": "Washington, D.C."
        }
        
        for country, capital in capitals.items():
            if country in query_lower:
                return f"The capital of {country.title()} is {capital}."
    
    # Aviation and engines
    aviation_facts = {
        "ge90": "The GE90 is a family of turbofan engines. The GE90-115B variant produces up to 115,300 pounds of thrust, making it one of the most powerful jet engines in the world. It powers the Boeing 777-300ER and 777-200LR aircraft.",
        "boeing 777": "The Boeing 777 is a wide-body airliner powered by engines like the GE90, Pratt & Whitney PW4000, or Rolls-Royce Trent 800 series.",
        "airbus a380": "The Airbus A380 is powered by either Rolls-Royce Trent 900 or Engine Alliance GP7200 engines.",
        "jet engine": "Jet engines work by compressing air, mixing it with fuel, igniting it, and expelling the exhaust to create thrust.",
        "turbofan": "A turbofan engine uses a fan to accelerate air around the engine core, providing most of the thrust efficiently."
    }
    
    for topic, info in aviation_facts.items():
        if topic in query_lower:
            return info
    
    # Science facts
    science_facts = {
        "speed of light": "The speed of light in vacuum is approximately 299,792,458 meters per second.",
        "boiling point water": "Water boils at 100°C (212°F) at standard atmospheric pressure.",
        "freezing point water": "Water freezes at 0°C (32°F) at standard atmospheric pressure.",
        "value of pi": "Pi (π) is approximately 3.14159265359...",
        "gravity earth": "Earth's gravity is approximately 9.8 m/s².",
        "distance earth sun": "The average distance from Earth to the Sun is about 150 million kilometers (93 million miles).",
        "mount everest": "Mount Everest is 8,848.86 meters (29,031.7 feet) tall.",
        "speed of sound": "The speed of sound in air at room temperature is approximately 343 meters per second (1,125 feet per second)."
    }
    
    for topic, fact in science_facts.items():
        topic_words = topic.split()
        if all(word in query_lower for word in topic_words):
            return fact
    
    # Technology facts
    tech_facts = {
        "artificial intelligence": "AI is a field of computer science focused on creating systems that can perform tasks typically requiring human intelligence.",
        "machine learning": "Machine learning is a subset of AI where algorithms learn from data to make predictions or decisions.",
        "neural network": "Neural networks are computing systems inspired by biological neural networks, used in machine learning.",
        "internet": "The Internet is a global network of interconnected computers that communicate using standardized protocols."
    }
    
    for topic, fact in tech_facts.items():
        if topic in query_lower or any(word in query_lower for word in topic.split()):
            return fact
    
    # Current date
    if "today" in query_lower or "current date" in query_lower:
        return f"Today's date is {datetime.now().strftime('%B %d, %Y')}."
    
    return f"I don't have specific information about '{query}' in my knowledge base. Try asking about geography, science, aviation, or technology topics."

def text_analyzer(text: str) -> str:
    """Analyzes text and provides statistics and insights."""
    try:
        # Basic text analysis
        words = text.split()
        sentences = text.split('.')
        
        # Count different elements
        word_count = len(words)
        sentence_count = len([s for s in sentences if s.strip()])
        char_count = len(text)
        char_count_no_spaces = len(text.replace(' ', ''))
        
        # Find longest word
        longest_word = max(words, key=len) if words else ""
        
        # Count uppercase and lowercase letters
        uppercase_count = sum(1 for c in text if c.isupper())
        lowercase_count = sum(1 for c in text if c.islower())
        
        # Basic readability (average words per sentence)
        avg_words_per_sentence = round(word_count / sentence_count, 1) if sentence_count > 0 else 0
        
        analysis = f"""Text Analysis Results:
- Word count: {word_count}
- Sentence count: {sentence_count}
- Character count: {char_count} (without spaces: {char_count_no_spaces})
- Longest word: "{longest_word}" ({len(longest_word)} characters)
- Uppercase letters: {uppercase_count}
- Lowercase letters: {lowercase_count}
- Average words per sentence: {avg_words_per_sentence}
- Text starts with: "{text[:50]}{'...' if len(text) > 50 else ''}"
"""
        
        return analysis
        
    except Exception as e:
        return f"Analysis error: {str(e)}"

if __name__ == "__main__":
    # Test the calculator first
    print("Testing calculator:")
    print(f"2 + 3 = {calculator('2 + 3')}")
    print(f"10 * 5 = {calculator('10 * 5')}")
    print(f"Invalid: {calculator('import os')}")  # Should error
    
    print("\n" + "="*60)
    print("🤖 ReAct Agent - Interactive Demo")
    print("="*60)
    print("Available tools: Calculator, Web Search (SerpAPI/Fallback), Text Analyzer")
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
        # Create agent and add all tools
        agent = ReActAgent(api_key)
        agent.add_tool("calculator", calculator, "Evaluates mathematical expressions")
        agent.add_tool("web_search", web_search, "Searches the web for current information")
        agent.add_tool("text_analyzer", text_analyzer, "Analyzes text statistics and insights")
        
        print("✅ Agent initialized with all tools!")
        print("\n💡 Example questions you can ask:")
        print("📊 Math: 'What is 25 * 17 + 48?'")
        print("🌍 Geography: 'What is the capital of Nicaragua?'")
        print("📰 Current Events: 'Latest news about AI' (requires SerpAPI)")
        print("🔬 Science: 'What is the speed of light?'")
        print("📝 Text: 'Analyze this text: Hello world!'")
        print("🧮 Mixed: 'Calculate 15% of 250 and tell me about percentages'")
        
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