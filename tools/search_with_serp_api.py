import requests

def _search_with_serpapi(query: str, api_key: str, max_retries: int = 3) -> str:
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
                    return "Search results:\n" + "\n".join(results)
            
            # If this attempt didn't yield good results, try next variation
            print(f"   No good results for '{search_query}', trying different approach...")
            
        except Exception as e:
            print(f"   Error with '{search_query}': {e}")
            continue
    
    # If all SerpAPI attempts failed, return empty none
    print("🔄 SerpAPI didn't find good results, returning empty string")
    return None
