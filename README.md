# 🤖 ReAct Agent (Reasoning + Acting)

A powerful AI agent that combines reasoning with action using the ReAct pattern. This agent can think through problems step-by-step and use external tools to gather information and solve complex tasks.

## 🎯 What is ReAct?

ReAct (Reasoning + Acting) is a pattern where AI agents:
1. **Think** - Reason about what to do next
2. **Act** - Use tools to gather information or perform actions  
3. **Observe** - Process the results
4. **Repeat** - Continue until the task is complete

## 🛠️ Available Tools

### 1. 🧮 Calculator
- Safely evaluates mathematical expressions
- Supports: `+`, `-`, `*`, `/`, `**`, `()`, and math functions

### 2. 🌐 Web Search  
- **SerpAPI** (when configured): Real-time Google search results
- **Fallback**: Built-in knowledge base for common questions
- Covers: Geography, science facts, current date, etc.

### 3. 📝 Text Analyzer
- Word count, sentence count, character analysis
- Longest word detection
- Readability metrics
- Case analysis (uppercase/lowercase)

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set OpenAI API Key
Edit `react_agent.py` and replace:
```python
api_key = "your-openai-api-key-here"
```

### 3. Run the Agent
```bash
python react_agent.py
```

## 🔧 Enhanced Web Search Setup (Optional)

For real-time web search capabilities:

### Option 1: Automatic Setup
```bash
python setup_serpapi.py
```

### Option 2: Manual Setup
1. Get free API key from [SerpAPI](https://serpapi.com/) (100 searches/month free)
2. Set environment variable:
   ```bash
   # Linux/Mac
   export SERPAPI_KEY='your-serpapi-key-here'
   
   # Windows
   set SERPAPI_KEY=your-serpapi-key-here
   ```

## 💡 Example Questions

### 📊 Mathematics
```
"What is 25 * 17 + 48?"
"Calculate 15% of 250"
"What's the square root of 144?"
```

### 🌍 Geography & Facts
```
"What is the capital of Nicaragua?"
"What's the speed of light?"
"What's the boiling point of water?"
```

### 📰 Current Information (requires SerpAPI)
```
"Latest news about artificial intelligence"
"Who won the 2024 Nobel Prize in Physics?"
"Current weather in Tokyo"
```

### 📝 Text Analysis
```
"Analyze this text: 'The quick brown fox jumps over the lazy dog.'"
"Count words in: 'Hello world, this is a test sentence.'"
```

### 🧮 Complex Multi-Tool Tasks
```
"Calculate 20% tip on $87.50 and tell me about tipping culture"
"What's 15 * 23, and what's the capital of the country with that area code?"
```

## 🏗️ Project Structure

```
ReAct/
├── react_agent.py      # Main ReAct agent implementation
├── setup_serpapi.py    # SerpAPI configuration helper
├── requirements.txt    # Python dependencies
└── README.md          # This file
```

## 🔍 How It Works

### 1. The ReAct Loop
```python
while not_finished:
    # 1. Model thinks about what to do
    thought = model.generate_thought(question, context)
    
    # 2. Model decides on an action
    action = model.choose_action(available_tools)
    
    # 3. Tool executes and returns result
    observation = tool.execute(action.input)
    
    # 4. Add observation to context and continue
    context.append(observation)
```

### 2. System Prompt Structure
The agent is taught to follow this exact format:
```
Thought: [reasoning about what to do next]
Action: [tool_name: tool_input]
Observation: [tool result will be inserted here]
... (repeat as needed)
Thought: [final reasoning]
Final Answer: [the answer to the question]
```

### 3. Tool Integration
Each tool is registered with:
- **Name**: How the model calls it
- **Function**: The actual implementation
- **Description**: What it does (for the model)

## 🎛️ Customization

### Adding New Tools
```python
def my_custom_tool(input_text: str) -> str:
    """Your tool implementation."""
    # Process input_text
    return "Tool result"

# Register the tool
agent.add_tool("my_tool", my_custom_tool, "Description of what it does")
```

### Modifying Behavior
- **Temperature**: Adjust creativity (0 = deterministic, 1 = creative)
- **Max iterations**: Prevent infinite loops
- **Model**: Switch between `gpt-4o-mini`, `gpt-3.5-turbo`, etc.

## 🐛 Troubleshooting

### Common Issues

**"No OpenAI API key"**
- Make sure you've set your OpenAI API key in the code

**"SerpAPI not working"**
- Check your API key with `python setup_serpapi.py`
- Verify you have remaining search credits

**"Calculator errors"**
- The calculator uses `eval()` safely - only math operations allowed
- Complex expressions might need parentheses

**"Agent loops infinitely"**
- Increase `max_iterations` if needed
- Check if the model is getting confused by ambiguous questions

## 🎓 Learning Objectives

This project teaches:
- **ReAct pattern implementation**
- **LLM prompt engineering**
- **Tool integration patterns**
- **Safe code execution**
- **API integration**
- **Error handling in AI systems**

## 🔗 Resources

- [ReAct Paper](https://arxiv.org/abs/2210.03629)
- [OpenAI API Docs](https://platform.openai.com/docs)
- [SerpAPI Documentation](https://serpapi.com/search-api)

## 📄 License

This project is for educational purposes. Please ensure you comply with the terms of service for OpenAI and SerpAPI.

---

**Happy building! 🚀**

Try asking complex questions that require multiple tools - watch how the agent reasons through the problem step by step! 