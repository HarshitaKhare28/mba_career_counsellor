# Simple demo script to test the scraper without database
# This will save embeddings to JSON files instead of PostgreSQL

import os
os.environ['SKIP_DATABASE'] = 'true'

from scraper import MBADataProcessor
import json
import numpy as np

class SimpleMBAProcessor(MBADataProcessor):
    def __init__(self, csv_file_path, brochures_folder="brochures"):
        super().__init__(csv_file_path, brochures_folder)
        self.skip_database = True
    
    def setup_database(self):
        print("Skipping database setup - using JSON files instead")
        pass
    
    def store_embeddings_in_database(self, all_embeddings, scraped_content, downloaded_files):
        """Store embeddings in JSON files instead of database"""
        print("Storing embeddings in JSON files...")
        
        # Create a results directory
        os.makedirs("results", exist_ok=True)
        
        # Save scraped content
        with open("results/scraped_content.json", "w", encoding='utf-8') as f:
            json.dump(scraped_content, f, indent=2, ensure_ascii=False)
        
        # Save downloaded files info
        with open("results/downloaded_files.json", "w", encoding='utf-8') as f:
            json.dump(downloaded_files, f, indent=2, ensure_ascii=False)
        
        # Save embeddings (convert numpy arrays to lists)
        embeddings_data = {}
        for content_type, embeddings in all_embeddings.items():
            embeddings_data[content_type] = {}
            for key, embedding in embeddings.items():
                embeddings_data[content_type][key] = {
                    'embedding': embedding.tolist(),
                    'shape': embedding.shape,
                    'dtype': str(embedding.dtype)
                }
        
        with open("results/embeddings.json", "w", encoding='utf-8') as f:
            json.dump(embeddings_data, f, indent=2)
        
        print(f"Results saved to 'results' directory:")
        print(f"- scraped_content.json: {len(scraped_content)} scraped pages")
        print(f"- downloaded_files.json: {len(downloaded_files)} brochures")
        print(f"- embeddings.json: {sum(len(emb) for emb in all_embeddings.values())} embeddings")

def main():
    print("🚀 Starting MBA Data Processing (Demo Mode - No Database)")
    print("=" * 60)
    
    processor = SimpleMBAProcessor("Online MBA Website with All Data.csv")
    processor.process_all_data()

if __name__ == "__main__":
    main()