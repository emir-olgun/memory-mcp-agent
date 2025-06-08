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
