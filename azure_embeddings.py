"""
Azure OpenAI Embedding Utility
Replaces SentenceTransformers with Azure OpenAI text-embedding-ada-002
"""
import os
from typing import List, Union, Optional
from openai import AzureOpenAI
from dotenv import load_dotenv
import numpy as np

load_dotenv()

class AzureEmbeddings:
    """
    Wrapper for Azure OpenAI Embeddings API
    Compatible interface with SentenceTransformer
    """
    
    def __init__(self):
        """Initialize Azure OpenAI client for embeddings"""
        api_key = os.getenv('AZURE_OPENAI_API_KEY')
        api_version = os.getenv('AZURE_OPENAI_API_VERSION')
        azure_endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
        
        if not all([api_key, api_version, azure_endpoint]):
            raise ValueError("Missing Azure OpenAI credentials in .env file")
        
        self.client = AzureOpenAI(
            api_key=api_key,
            api_version=api_version,
            azure_endpoint=azure_endpoint
        )
        self.deployment = os.getenv('AZURE_OPENAI_EMBEDDING_DEPLOYMENT', 'text-embedding-ada-002')
        self.dimension = 1536  # text-embedding-ada-002 produces 1536-dimensional vectors
        
    def encode(self, texts: Union[str, List[str]], batch_size: int = 32, 
               show_progress_bar: bool = False, convert_to_numpy: bool = True) -> np.ndarray:
        """
        Encode texts into embeddings
        
        Args:
            texts: Single text or list of texts to encode
            batch_size: Number of texts to process at once (for API calls)
            show_progress_bar: Whether to show progress (kept for compatibility)
            convert_to_numpy: Whether to return as numpy array
            
        Returns:
            numpy array of embeddings
        """
        # Handle single string input
        if isinstance(texts, str):
            texts = [texts]
            single_input = True
        else:
            single_input = False
        
        embeddings = []
        
        # Process in batches to handle API rate limits
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            
            try:
                response = self.client.embeddings.create(
                    input=batch,
                    model=self.deployment
                )
                
                # Extract embeddings from response
                batch_embeddings = [item.embedding for item in response.data]
                embeddings.extend(batch_embeddings)
                
            except Exception as e:
                print(f"Error generating embeddings for batch {i//batch_size + 1}: {e}")
                # Return zero vectors for failed batches
                embeddings.extend([[0.0] * self.dimension] * len(batch))
        
        # Convert to numpy array if requested
        if convert_to_numpy:
            embeddings = np.array(embeddings)
        
        # Return single embedding if single input
        if single_input:
            return embeddings[0] if convert_to_numpy else embeddings[0]
        
        return embeddings
    
    def get_sentence_embedding_dimension(self) -> int:
        """Get the dimension of embeddings (for compatibility)"""
        return self.dimension


def get_embedding_model():
    """
    Factory function to get embedding model
    Returns AzureEmbeddings instance
    """
    return AzureEmbeddings()


# Backward compatibility: Allow importing as SentenceTransformer replacement
def SentenceTransformer(model_name: Optional[str] = None):
    """
    Backward compatibility wrapper
    Ignores model_name and returns Azure OpenAI embeddings
    """
    print(f"⚠️ Using Azure OpenAI Embeddings (text-embedding-ada-002) instead of {model_name}")
    return AzureEmbeddings()
