import os
import pandas as pd
import argparse
from dotenv import load_dotenv

from utils import load_csv
from agent import DataCompletionAgent

def main():
    # Load environment variables
    load_dotenv()
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Complete missing data in import/export CSV files using LLM with explanations')
    parser.add_argument('--target', type=str, default='duimp_202502.csv', help='Path to the target CSV file with missing data')
    parser.add_argument('--reference', type=str, default='duimp_completa__202412.csv', help='Path to the reference CSV file')
    parser.add_argument('--output', type=str, default='duimp_completed_with_explanations.csv', help='Path to save the completed CSV file')
    parser.add_argument('--model', type=str, default='gpt-3.5-turbo', help='LLM model to use')
    parser.add_argument('--batch-size', type=int, default=10, help='Number of rows to process in each batch')
    parser.add_argument('--max-similar', type=int, default=5, help='Maximum number of similar rows to include in each prompt')
    
    args = parser.parse_args()
    
    # Check if files exist
    if not os.path.exists(args.target):
        raise FileNotFoundError(f"Target file not found: {args.target}")
    
    if not os.path.exists(args.reference):
        raise FileNotFoundError(f"Reference file not found: {args.reference}")
    
    # Check for OpenAI API key
    if not os.getenv("OPENAI_API_KEY"):
        raise EnvironmentError("OPENAI_API_KEY environment variable not set. Please set it in a .env file.")
    
    print(f"Loading target file: {args.target}")
    target_df = load_csv(args.target)
    
    print(f"Loading reference file: {args.reference}")
    reference_df = load_csv(args.reference)
    
    # Define columns to use for matching similar rows
    # Removed apenas yearmonth e source, mantendo as demais colunas para melhor correspondência
    match_columns = ["ncm_code", "country_origin_acronym", "transport_mode_pt", 
                    "clearance_place_entry", "consignee_code", "shipper_name"]
    
    # Initialize the agent
    agent = DataCompletionAgent(model_name=args.model)
    
    # Process the dataframe
    print("Processing dataframe to complete missing values with explanations...")
    completed_df = agent.process_dataframe(
        target_df,
        reference_df,
        match_columns,
        batch_size=args.batch_size,
        max_similar_rows=args.max_similar
    )
    
    # Save the completed dataframe
    print(f"Saving completed dataframe with explanations to {args.output}")
    completed_df.to_csv(args.output, index=False)
    
    print("Done!")

if __name__ == "__main__":
    main() 