#!/usr/bin/env python3
"""
Simple test script to debug SerpAPI functionality
"""

import os
import requests
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def test_serpapi():
    print("🧪 Testing SerpAPI Connection")
    print("=" * 40)
    
    # Check if API key exists
    api_key = os.getenv('SERPAPI_KEY')
    if not api_key:
        print("❌ No SERPAPI_KEY environment variable found")
        print("Set it with: export SERPAPI_KEY='your-key-here'")
        return
    
    print(f"✅ API Key found: {api_key[:10]}...")
    
    # Test simple query
    test_query = "what is python programming"
    print(f"\n🔍 Testing query: '{test_query}'")
    
    try:
        url = "https://serpapi.com/search"
        params = {
            'q': test_query,
            'api_key': api_key,
            'engine': 'google',
            'num': 3
        }
        
        print(f"📡 Making request to: {url}")
        print(f"📝 Parameters: {params}")
        
        response = requests.get(url, params=params, timeout=10)
        print(f"📊 Response status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"Response text: {response.text}")
            return
        
        data = response.json()
        print(f"✅ Response received, parsing JSON...")
        
        # Show what we got
        print(f"\n📋 Available keys in response:")
        for key in data.keys():
            print(f"  - {key}")
        
        # Check for different result types
        if 'answer_box' in data:
            print(f"\n🎯 Answer Box found:")
            print(json.dumps(data['answer_box'], indent=2))
        
        if 'knowledge_graph' in data:
            print(f"\n🧠 Knowledge Graph found:")
            kg = data['knowledge_graph']
            if 'description' in kg:
                print(f"Description: {kg['description']}")
        
        if 'organic_results' in data:
            print(f"\n📰 Organic Results found ({len(data['organic_results'])} results):")
            for i, result in enumerate(data['organic_results'][:3]):
                print(f"  Result {i+1}:")
                if 'title' in result:
                    print(f"    Title: {result['title']}")
                if 'snippet' in result:
                    print(f"    Snippet: {result['snippet'][:100]}...")
        
        if 'error' in data:
            print(f"❌ API Error: {data['error']}")
        
        # Check if we have any useful content
        has_content = (
            'answer_box' in data or 
            'knowledge_graph' in data or 
            ('organic_results' in data and len(data['organic_results']) > 0)
        )
        
        if has_content:
            print(f"\n✅ SerpAPI is working and returning content!")
        else:
            print(f"\n⚠️ SerpAPI responded but no useful content found")
            print("Full response:")
            print(json.dumps(data, indent=2))
            
    except requests.exceptions.Timeout:
        print("❌ Request timed out")
    except requests.exceptions.RequestException as e:
        print(f"❌ Request error: {e}")
    except json.JSONDecodeError as e:
        print(f"❌ JSON decode error: {e}")
        print(f"Raw response: {response.text}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    test_serpapi() 