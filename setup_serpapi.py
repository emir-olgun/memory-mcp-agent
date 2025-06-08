#!/usr/bin/env python3
"""
Setup script for SerpAPI integration with ReAct Agent
"""

import os

def setup_serpapi():
    print("🔧 SerpAPI Setup for ReAct Agent")
    print("=" * 40)
    
    current_key = os.getenv('SERPAPI_KEY')
    if current_key:
        print(f"✅ SerpAPI key already configured: {current_key[:10]}...")
        response = input("Do you want to update it? (y/n): ").lower()
        if response != 'y':
            print("Setup cancelled.")
            return
    
    print("\n📝 To get a free SerpAPI key:")
    print("1. Go to https://serpapi.com/")
    print("2. Sign up for a free account")
    print("3. Copy your API key from the dashboard")
    print("4. You get 100 free searches per month!")
    
    api_key = input("\n🔑 Enter your SerpAPI key: ").strip()
    
    if not api_key:
        print("❌ No key provided. Setup cancelled.")
        return
    
    # Test the API key
    print("\n🧪 Testing API key...")
    try:
        import requests
        url = "https://serpapi.com/search"
        params = {
            'q': 'test',
            'api_key': api_key,
            'engine': 'google',
            'num': 1
        }
        
        response = requests.get(url, params=params, timeout=5)
        if response.status_code == 200:
            print("✅ API key is valid!")
        else:
            print(f"❌ API key test failed: {response.status_code}")
            return
            
    except Exception as e:
        print(f"❌ Error testing API key: {e}")
        return
    
    # Show how to set the environment variable
    print(f"\n🎯 To use this key, set the environment variable:")
    print(f"   Linux/Mac: export SERPAPI_KEY='{api_key}'")
    print(f"   Windows: set SERPAPI_KEY={api_key}")
    print(f"\n   Or add this to your ~/.bashrc or ~/.zshrc:")
    print(f"   export SERPAPI_KEY='{api_key}'")
    
    # Option to set it for current session
    set_now = input("\n🚀 Set for current session? (y/n): ").lower()
    if set_now == 'y':
        os.environ['SERPAPI_KEY'] = api_key
        print("✅ SerpAPI key set for current session!")
        print("   Run 'python react_agent.py' to test it")
    
    print("\n🎉 Setup complete! Your ReAct agent now has real-time web search!")

if __name__ == "__main__":
    setup_serpapi() 