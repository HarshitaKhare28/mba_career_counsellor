#!/usr/bin/env python3
"""
Simple search script to demonstrate MBA data similarity search
This script loads the embeddings and allows you to search for similar content
"""

import json
import numpy as np
from azure_embeddings import AzureEmbeddings
import pandas as pd
from typing import List, Tuple
import argparse

class MBASearchEngine:
    def __init__(self, embeddings_file="results/embeddings.json", 
                 scraped_content_file="results/scraped_content.json",
                 csv_file="Online MBA Website with All Data.csv"):
        """Initialize the search engine with embeddings and content"""
        self.model = AzureEmbeddings()
        print("Using Azure OpenAI Embeddings (text-embedding-ada-002)")
        
        # Load embeddings
        print("Loading embeddings...")
        with open(embeddings_file, 'r', encoding='utf-8') as f:
            self.embeddings_data = json.load(f)
        
        # Load scraped content
        with open(scraped_content_file, 'r', encoding='utf-8') as f:
            self.scraped_content = json.load(f)
        
        # Load CSV data
        self.df = pd.read_csv(csv_file)
        
        # Prepare embeddings for search
        self.embeddings = {}
        self.content_map = {}
        
        for content_type, embeddings in self.embeddings_data.items():
            for key, embedding_info in embeddings.items():
                full_key = f"{content_type}_{key}"
                self.embeddings[full_key] = np.array(embedding_info['embedding'])
                
                # Map content for display
                if content_type == 'webpage':
                    university_name = key.replace('_webpage', '')
                    self.content_map[full_key] = {
                        'type': 'webpage',
                        'university': university_name,
                        'content': self.scraped_content.get(university_name, '')[:300] + '...'
                    }
                elif content_type == 'brochure':
                    university_name = key.replace('_brochure', '')
                    self.content_map[full_key] = {
                        'type': 'brochure',
                        'university': university_name,
                        'content': f'Brochure content for {university_name}'
                    }
                elif content_type == 'csv_data':
                    university_name = key.replace('_info', '')
                    row_data = self.df[self.df['Brand University'] == university_name]
                    if not row_data.empty:
                        row = row_data.iloc[0]
                        content = f"Fees: {row.get('Course Fees', 'N/A')} | Specialization: {row.get('Specialization', 'N/A')} | Accreditations: {row.get('Accredations', 'N/A')}"
                    else:
                        content = f'Information for {university_name}'
                    
                    self.content_map[full_key] = {
                        'type': 'university_info',
                        'university': university_name,
                        'content': content
                    }
        
        print(f"Loaded {len(self.embeddings)} embeddings from {len(set(item['university'] for item in self.content_map.values()))} universities")
    
    def search(self, query: str, top_k: int = 5) -> List[Tuple[str, float, dict]]:
        """Search for similar content based on query"""
        print(f"\nSearching for: '{query}'")
        
        # Create query embedding
        query_embedding = self.model.encode(query)
        
        # Calculate similarities
        similarities = []
        for key, embedding in self.embeddings.items():
            # Cosine similarity
            similarity = np.dot(query_embedding, embedding) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(embedding)
            )
            similarities.append((key, similarity, self.content_map[key]))
        
        # Sort by similarity (descending)
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        return similarities[:top_k]
    
    def display_results(self, results: List[Tuple[str, float, dict]]):
        """Display search results in a formatted way"""
        print("\n" + "="*80)
        print("SEARCH RESULTS")
        print("="*80)
        
        for i, (key, similarity, content_info) in enumerate(results, 1):
            print(f"\n{i}. {content_info['university']} ({content_info['type'].upper()})")
            print(f"   Similarity: {similarity:.4f}")
            print(f"   Content: {content_info['content']}")
            print("-" * 80)
    
    def get_university_info(self, university_name: str):
        """Get all available information for a specific university"""
        print(f"\n{'='*80}")
        print(f"DETAILED INFORMATION FOR: {university_name}")
        print(f"{'='*80}")
        
        # Get CSV info
        row_data = self.df[self.df['Brand University'].str.contains(university_name, case=False)]
        if not row_data.empty:
            row = row_data.iloc[0]
            print(f"\n📊 BASIC INFORMATION:")
            print(f"   University: {row.get('Brand University', 'N/A')}")
            print(f"   Specialization: {row.get('Specialization', 'N/A')}")
            print(f"   Course Fees: {row.get('Course Fees', 'N/A')}")
            print(f"   Subsidy/Cashback: {row.get('Subsidy Cashback on Full Payment', 'N/A')}")
            print(f"   Accreditations: {row.get('Accredations', 'N/A')}")
            print(f"   Website: {row.get('Website', 'N/A')}")
        
        # Get webpage content
        webpage_content = self.scraped_content.get(university_name)
        if webpage_content:
            print(f"\n🌐 WEBSITE CONTENT PREVIEW:")
            print(f"   {webpage_content[:500]}...")

def main():
    parser = argparse.ArgumentParser(description='MBA University Search Engine')
    parser.add_argument('--query', '-q', type=str, help='Search query')
    parser.add_argument('--university', '-u', type=str, help='Get detailed info for specific university')
    parser.add_argument('--top', '-t', type=int, default=5, help='Number of top results to show')
    parser.add_argument('--interactive', '-i', action='store_true', help='Interactive mode')
    
    args = parser.parse_args()
    
    # Initialize search engine
    try:
        search_engine = MBASearchEngine()
    except FileNotFoundError as e:
        print(f"Error: Required files not found. Please run the scraper first.")
        print(f"Missing file: {e}")
        return
    
    if args.university:
        search_engine.get_university_info(args.university)
    elif args.query:
        results = search_engine.search(args.query, args.top)
        search_engine.display_results(results)
    elif args.interactive:
        print("🔍 MBA University Search Engine - Interactive Mode")
        print("Type your search queries or 'quit' to exit")
        print("Examples: 'affordable MBA', 'finance specialization', 'AICTE accredited'")
        
        while True:
            query = input("\nSearch> ").strip()
            if query.lower() in ['quit', 'exit', 'q']:
                break
            if query:
                results = search_engine.search(query, args.top)
                search_engine.display_results(results)
    else:
        # Demo searches
        demo_queries = [
            "affordable MBA with low fees",
            "finance specialization programs",
            "AICTE accredited universities",
            "online MBA with good placement",
            "business analytics program"
        ]
        
        print("🚀 MBA University Search Engine - Demo Mode")
        print("Running sample searches...")
        
        for query in demo_queries:
            results = search_engine.search(query, 3)
            search_engine.display_results(results)
            print("\n" + "="*80 + "\n")

if __name__ == "__main__":
    main()