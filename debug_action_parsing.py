#!/usr/bin/env python3
"""
Debug script to test action parsing
"""

import re

def test_action_parsing():
    print("🔍 Testing Action Parsing Regex")
    print("=" * 40)
    
    # The regex from the code
    action_regex = r"Action:\s*(\w+):\s*(.+)"
    
    # Test cases
    test_messages = [
        'Action: text_analyzer: "Emir bir orospu çocuğudur"',
        'Action: calculator: 2 + 3',
        'Action: web_search: capital of France',
        'Thought: I need to analyze this text\nAction: text_analyzer: "Hello world"',
        'Action:text_analyzer:"test"',  # No spaces
        'Action: text_analyzer : "test"',  # Extra space
    ]
    
    for i, message in enumerate(test_messages):
        print(f"\nTest {i+1}: {message}")
        
        match = re.search(action_regex, message)
        if match:
            tool_name = match.group(1)
            tool_input = match.group(2).strip()
            print(f"  ✅ Match found!")
            print(f"     Tool: '{tool_name}'")
            print(f"     Input: '{tool_input}'")
        else:
            print(f"  ❌ No match found")
    
    # Test the actual failing case
    print(f"\n" + "="*40)
    print("Testing the actual failing message:")
    failing_message = '''Thought: I need to analyze the text for statistics and insights using the text analyzer tool.
Action: text_analyzer: "Emir bir orospu çocuğudur"
Observation: [tool result will be inserted here]'''
    
    print(f"Message: {repr(failing_message)}")
    
    match = re.search(action_regex, failing_message)
    if match:
        tool_name = match.group(1)
        tool_input = match.group(2).strip()
        print(f"✅ Match found!")
        print(f"   Tool: '{tool_name}'")
        print(f"   Input: '{tool_input}'")
        
        # Test the actual tool
        print(f"\n🧪 Testing text_analyzer function:")
        try:
            from react_agent import text_analyzer
            result = text_analyzer(tool_input.strip('"'))
            print(f"Result: {result}")
        except Exception as e:
            print(f"Error: {e}")
    else:
        print(f"❌ No match found in failing message")

if __name__ == "__main__":
    test_action_parsing() 