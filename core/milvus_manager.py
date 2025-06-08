from pymilvus import MilvusClient, DataType, MilvusException
from core.config import settings
import time

class MilvusManager:
    """
    This class encapsulates all operations related to Milvus, including:
    - Client initialization
    - Collection setup (schema creation and index creation)
    - Inserting documents
    - Searching, querying, and deleting documents
    """

    def __init__(self, collection_name: str = "client_documents", dim: int = 1536):
        """
        Initialize the Milvus client and set up the collection.

        Parameters:
        - collection_name: The name of the Milvus collection.
        - dim: Dimensionality of the embedding vectors.
        """
        print(f"Initializing MilvusManager with collection: {collection_name}, dim: {dim}")
        
        # Initialize the Milvus client using configuration settings
        try:
            self.milvus_client = MilvusClient(uri=settings.MILVUS_ENDPOINT)
            self.collection_name = collection_name
            self.dim = dim

            # Log the connection status
            connection_msg = f"Connected to Milvus at: {settings.MILVUS_ENDPOINT}"
            print(f"[MilvusManager] {connection_msg}")

            # Ensure that the collection exists and is configured correctly
            self.setup_collection()
        except Exception as e:
            error_msg = f"Failed to initialize Milvus client: {str(e)}"
            raise Exception(error_msg)

    def setup_collection(self):
        """
        Check whether the collection exists. If not, create it with the proper schema and index configuration.
        """
        print(f"Setting up collection: {self.collection_name}")
        try:
            if not self.milvus_client.has_collection(self.collection_name):
                print(f"Collection {self.collection_name} does not exist, creating it")
                
                # Create a new schema object
                schema = self.milvus_client.create_schema()
                # Add required fields along with their data types and metadata
                schema.add_field("vector_id", DataType.VARCHAR, max_length=255, is_primary=True, description="Unique vector ID")
                schema.add_field("user_id", DataType.VARCHAR, max_length=255, description="User ID")
                schema.add_field("document_id", DataType.VARCHAR, max_length=255, description="Unique document ID")
                schema.add_field("document_name", DataType.VARCHAR, max_length=255, description="Document name")
                schema.add_field("document_embeddings", DataType.FLOAT_VECTOR, dim=self.dim, description="Document embeddings")
                schema.add_field("upload_timestamp", DataType.INT64, description="Upload timestamp")
                schema.add_field("chunk_text", DataType.VARCHAR, max_length=2000, description="Chunk text")
                print("Schema created with all required fields")

                # Prepare index parameters (using the L2 metric for similarity)
                index_params = self.milvus_client.prepare_index_params()
                index_params.add_index("document_embeddings", metric_type="L2")
                print("Index parameters prepared")

                # Create the collection with the specified schema and index parameters
                self.milvus_client.create_collection(
                    self.collection_name,
                    dimension=self.dim,
                    schema=schema,
                    index_params=index_params
                )
                creation_msg = f"Created collection: {self.collection_name}"
                print(f"[MilvusManager] {creation_msg}")
            else:
                exists_msg = f"Collection {self.collection_name} already exists."
                print(f"[MilvusManager] {exists_msg}")
        except Exception as e:
            error_msg = f"Error setting up collection {self.collection_name}: {str(e)}"
            raise Exception(error_msg)

    def insert_documents(self, documents: list):
        """
        Insert a list of document rows into the collection.

        Parameters:
        - documents: A list of dictionaries where each dictionary represents a document.
        """
        print(f"Inserting {len(documents)} documents into collection {self.collection_name}")
        start_time = time.time()
        
        try:
            for i, row in enumerate(documents):
                # Insert each document row into the collection
                self.milvus_client.insert(self.collection_name, [row])
                if i % 10 == 0 and i > 0:  # Log progress for every 10 documents
                    print(f"Inserted {i}/{len(documents)} documents")
            self.milvus_client.flush(self.collection_name)
            
            elapsed_time = time.time() - start_time
            print(f"Successfully inserted {len(documents)} documents in {elapsed_time:.2f} seconds")
        except MilvusException as e:
            error_msg = f"Error inserting documents: {str(e)}"
            raise Exception(error_msg)

    def search(self, query_embedding: list, topk: int = 3, search_params: dict = None, anns_field: str = "document_embeddings", filter_expression: list[str] = None, filter_params: dict = None):
        """
        Search for similar documents using the provided query embedding.

        Parameters:
        - query_embedding: The embedding vector to search for.
        - limit: Number of top results to return.
        - search_params: Dictionary of search parameters.
        - anns_field: The collection field that holds the embeddings.

        Returns:
        - Search results from Milvus.
        """
        print(f"Searching collection {self.collection_name} for top {topk} results")
        if filter_expression:
            print(f"Using filter expression: {filter_expression}")
        
        try:
            start_time = time.time()
            results = self.milvus_client.search(
                self.collection_name,
                [query_embedding],
                limit=topk,
                search_params=search_params,
                anns_field=anns_field,
                filter=filter_expression,
                output_fields=["chunk_text", "document_id"]
            )
            elapsed_time = time.time() - start_time
            
            result_count = len(results) if results else 0
            print(f"Search completed in {elapsed_time:.2f} seconds, found {result_count} results")
            return results
        except MilvusException as e:
            error_msg = f"Error during search: {str(e)}"
            raise Exception(error_msg)

    def delete_by_filter(self, filter_expr: str):
        """
        Delete documents from the collection using a filter expression.

        Parameters:
        - filter_expr: The filter expression to identify documents for deletion.
        """
        print(f"Deleting documents from collection {self.collection_name} with filter: {filter_expr}")
        
        try:
            # Delete documents that match the filter expression
            start_time = time.time()
            delete_result = self.milvus_client.delete(collection_name=self.collection_name, filter=filter_expr)
            
            # Flush the collection to commit the deletion
            print("Flushing collection to commit deletion")
            self.milvus_client.flush(self.collection_name)
            
            elapsed_time = time.time() - start_time
            deleted_count = delete_result.get("delete_count", 0) if isinstance(delete_result, dict) else "unknown"
            print(f"Deleted {deleted_count} documents in {elapsed_time:.2f} seconds")
        except MilvusException as e:
            error_msg = f"Error deleting documents: {str(e)}"
            raise Exception(error_msg)

    def delete_all_records(self):
        """
        Delete ALL records from the collection without any filter.
        This will completely empty the collection but keep the schema intact.
        """
        print(f"Deleting ALL records from collection {self.collection_name}")
        
        try:
            start_time = time.time()
            
            # First, get the count of total records
            stats = self.milvus_client.get_collection_stats(self.collection_name)
            total_records = stats.get("row_count", 0)
            print(f"Total records to delete: {total_records}")
            
            # Delete all records using a filter that matches everything
            # Using a filter that will match all records with any vector_id
            filter_expr = "vector_id != ''"
            delete_result = self.milvus_client.delete(collection_name=self.collection_name, filter=filter_expr)
            
            # Flush the collection to commit the deletion
            print("Flushing collection to commit deletion")
            self.milvus_client.flush(self.collection_name)
            
            elapsed_time = time.time() - start_time
            deleted_count = delete_result.get("delete_count", 0) if isinstance(delete_result, dict) else "unknown"
            print(f"Deleted ALL {deleted_count} records from collection in {elapsed_time:.2f} seconds")
            
        except MilvusException as e:
            error_msg = f"Error deleting all records: {str(e)}"
            raise Exception(error_msg)

    def recreate_collection(self):
        """
        Completely drop and recreate the collection.
        This will delete everything and start fresh with the same schema.
        WARNING: This will permanently delete all data in the collection.
        """
        print(f"Recreating collection {self.collection_name} - ALL DATA WILL BE LOST")
        
        try:
            start_time = time.time()
            
            # Drop the existing collection if it exists
            if self.milvus_client.has_collection(self.collection_name):
                print(f"Dropping existing collection: {self.collection_name}")
                self.milvus_client.drop_collection(self.collection_name)
                print(f"Collection {self.collection_name} dropped successfully")
            
            # Recreate the collection with the same schema
            print(f"Recreating collection: {self.collection_name}")
            self.setup_collection()
            
            elapsed_time = time.time() - start_time
            print(f"Collection {self.collection_name} recreated successfully in {elapsed_time:.2f} seconds")
            
        except MilvusException as e:
            error_msg = f"Error recreating collection: {str(e)}"
            raise Exception(error_msg)

    def query_by_filter(self, filter_expr: str, output_fields: list):
        """
        Query the collection using a filter expression and return the specified fields.

        Parameters:
        - filter_expr: The filter expression (e.g., "client_id == 123").
        - output_fields: List of fields to include in the result.

        Returns:
        - A list of dictionaries containing the queried fields.
        """
        print(f"Querying collection {self.collection_name} with filter: {filter_expr}")
        print(f"Requesting output fields: {output_fields}")
        
        try:
            start_time = time.time()
            results = self.milvus_client.query(
                collection_name=self.collection_name,
                filter=filter_expr,
                output_fields=output_fields
            )
            elapsed_time = time.time() - start_time
            
            result_count = len(results) if results else 0
            print(f"Query completed in {elapsed_time:.2f} seconds, returned {result_count} results")
            return results
        except MilvusException as e:
            error_msg = f"Error querying documents: {str(e)}"
            raise Exception(error_msg) 