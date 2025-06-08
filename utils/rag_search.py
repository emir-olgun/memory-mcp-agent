from core.milvus_manager import (
    MilvusManager,
)  # Use MilvusManager for all Milvus operations
import openai
from core.config import settings  # Application settings and configuration
from utils.helpers import extract_chunk_texts

openai.api_key = settings.OPENAI_API_KEY

def get_relevant_documents(prompt: str, user_id: str):
    """
    Retrieves relevant document chunks from Milvus based on the provided prompt.
    
    Args:
        prompt: The user query or prompt text
        user_id: The ID of the user to filter documents by
        
    Returns:
        A string containing the concatenated text chunks from relevant documents
    """
    print(f"Retrieving relevant documents for user_id: {user_id}")
    print(f"Prompt length: {len(prompt)} characters")
    
    # Initialize the MilvusManager instance to encapsulate all Milvus operations
    milvus_manager = MilvusManager()
    print("Initialized MilvusManager")

    # Initialize LangChain embeddings with the OpenAI API key from settings
    try:
        embeddings = openai.embeddings.create(input=prompt, model="text-embedding-3-small")
        print("Initialized OpenAI embeddings")
    except Exception as e:
        print(f"Failed to initialize OpenAI embeddings: {str(e)}")
        return ""

    # Generate an embedding vector for the provided prompt text.
    try:
        prompt_embedding = embeddings.embed_query(prompt)
        print("Generated embedding for prompt")
    except Exception as e:
        print(f"Failed to generate embedding for prompt: {str(e)}")
        return ""

    # Define search parameters for Milvus query using the L2 metric with a depth level of 2.
    search_params = {"metric_type": "L2", "params": {"level": 2}}
    topk = 3  # Limit the search to the top 3 nearest documents.
    print(f"Search parameters: {search_params}, topk: {topk}")

    # Use filter expression templating for better performance.
    # The filter expression uses the 'document_id' field and replaces {document_ids} with
    # the provided list from filter_params.
    filter_expression = f'user_id == "{user_id}"'
    print(f"Filter expression: {filter_expression}")

    try:
        # Execute the Milvus search.
        # Note: Milvus returns a list of lists (one sub-list per query vector even if only one vector is provided).
        print("Executing Milvus search")
        results = milvus_manager.search(
            query_embedding=prompt_embedding,
            topk=topk,
            search_params=search_params,
            anns_field="document_embeddings",  # Field containing the stored vectors.
            filter_expression=filter_expression,
        )
        print("Milvus search completed successfully")
    except Exception as e:
        print(f"Error during Milvus search: {str(e)}")
        import traceback
        print(traceback.format_exc())
        results = []  # Fallback to an empty list on error.

    # Flatten the result list because Milvus returns a list of lists.
    flattened_results = []
    for res_group in results:
        if isinstance(res_group, list):
            flattened_results.extend(res_group)
        else:
            flattened_results.append(res_group)
    
    print(f"Flattened results contain {len(flattened_results)} items")

    # Extract relevant text chunks from the flattened search results.
    relevant_texts = extract_chunk_texts(flattened_results)
    print(f"Extracted {len(relevant_texts)} characters of relevant text")
    
    return relevant_texts