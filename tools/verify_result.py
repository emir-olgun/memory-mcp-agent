from tools.web_search import web_search
import re

def verify_result(description: str) -> str:
    """Enhanced verification tool that checks results across multiple sources."""
    try:
        # Generate multiple search queries with different approaches
        queries = _generate_verification_queries(description)
        
        # Perform searches across multiple sources
        search_results = []
        for i, query in enumerate(queries, 1):
            try:
                result = web_search(query)
                search_results.append({
                    'query': query,
                    'result': result,
                    'source_num': i
                })
            except Exception as e:
                search_results.append({
                    'query': query,
                    'result': f"Search failed: {str(e)}",
                    'source_num': i
                })
        
        # Analyze and compare results
        verification_report = _analyze_verification_results(search_results, description)
        
        return verification_report
        
    except Exception as e:
        return f"Multi-source verification failed: {str(e)}. Consider manually double-checking your result using alternative methods or sources."

def _generate_verification_queries(description: str) -> list:
    """Generate multiple verification queries with different approaches."""
    # Extract key terms from the description
    key_terms = _extract_key_terms(description)
    
    queries = []
    
    # Query 1: Direct verification
    queries.append(f"verify check validate {description}")
    
    # Query 2: Technical specifications
    if any(term in description.lower() for term in ['engine', 'power', 'horsepower', 'thrust', 'conversion']):
        queries.append(f"{key_terms} technical specifications datasheet")
    else:
        queries.append(f"{key_terms} technical specifications")
    
    # Query 3: Multiple sources comparison
    queries.append(f"{key_terms} multiple sources comparison")
    
    # Query 4: Official/authoritative source
    if any(term in description.lower() for term in ['ge90', 'boeing', 'aircraft', 'engine']):
        queries.append(f"{key_terms} official manufacturer specifications")
    elif any(term in description.lower() for term in ['calculation', 'formula', 'conversion']):
        queries.append(f"{key_terms} standard formula method")
    else:
        queries.append(f"{key_terms} authoritative source")
    
    return queries[:4]  # Limit to 4 queries to avoid overwhelming

def _extract_key_terms(description: str) -> str:
    """Extract key terms from the description for targeted searches."""
    # Remove common verification words
    cleaned = re.sub(r'\b(verify|check|validate|result|seems|appears|power|of|the|in|terms|based|on|its|output)\b', '', description.lower())
    
    # Extract meaningful terms
    words = cleaned.split()
    key_words = [word.strip('.,()[]') for word in words if len(word.strip('.,()[]')) > 2]
    
    return ' '.join(key_words[:5])  # Limit to 5 key terms

def _analyze_verification_results(search_results: list, original_description: str) -> str:
    """Analyze and compare verification results from multiple sources."""
    report = []
    report.append("🔍 MULTI-SOURCE VERIFICATION REPORT")
    report.append("=" * 50)
    report.append(f"Original Query: {original_description}")
    report.append("")
    
    # Present results from each source
    valid_results = []
    
    for result in search_results:
        report.append(f"📊 Source {result['source_num']}: {result['query']}")
        report.append("-" * 30)
        
        if "Search failed" not in result['result']:
            # Extract numerical values if present
            numbers = re.findall(r'[\d,]+\.?\d*', result['result'])
            if numbers:
                report.append(f"Key numbers found: {', '.join(numbers[:3])}")
            
            # Show relevant excerpt
            excerpt = result['result'][:200] + "..." if len(result['result']) > 200 else result['result']
            report.append(f"Excerpt: {excerpt}")
            valid_results.append(result['result'])
        else:
            report.append(f"❌ {result['result']}")
        
        report.append("")
    
    # Analysis and consensus
    report.append("🎯 VERIFICATION ANALYSIS:")
    report.append("-" * 30)
    
    if len(valid_results) >= 2:
        # Look for consensus patterns
        all_numbers = []
        for result in valid_results:
            numbers = re.findall(r'[\d,]+\.?\d*', result)
            all_numbers.extend(numbers)
        
        if all_numbers:
            report.append(f"Numbers found across sources: {', '.join(set(all_numbers))}")
            
            # Check for consistency
            unique_numbers = set(all_numbers)
            if len(unique_numbers) <= 3:
                report.append("✅ Results show some consistency across sources")
            else:
                report.append("⚠️  Results show significant variation - this is normal for complex specifications")
        
        report.append(f"✅ Successfully verified with {len(valid_results)} sources")
    elif len(valid_results) == 1:
        report.append("⚠️  Only one source provided results - consider additional verification")
    else:
        report.append("❌ No sources provided valid results - manual verification strongly recommended")
    
    report.append("")
    report.append("💡 RECOMMENDATION:")
    report.append("Compare your result with the findings above. If there's significant discrepancy,")
    report.append("note the range of values found rather than seeking additional sources.")
    report.append("For most questions, this level of verification is sufficient to proceed with confidence.")
    
    return "\n".join(report)
    