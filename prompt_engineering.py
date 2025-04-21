import pandas as pd
import json
from typing import List, Dict, Any

from utils import load_csv, find_missing_data, find_similar_rows

def generate_prompt_examples(target_file: str, reference_file: str, num_examples: int = 5) -> List[Dict[str, Any]]:
    """
    Generate examples for prompt engineering by finding rows with missing data
    and creating examples of how the LLM should complete them.
    
    Args:
        target_file: Path to the CSV file with missing data
        reference_file: Path to the reference CSV file with complete data
        num_examples: Number of examples to generate
        
    Returns:
        List of example dictionaries for prompt engineering
    """
    # Load CSV files
    target_df = load_csv(target_file)
    reference_df = load_csv(reference_file)
    
    # Find rows with missing data
    missing_data_map = find_missing_data(target_df)
    
    # Columns typically used for matching
    match_columns = ["yearmonth", "ncm_code", "country_origin_acronym", "shipper_name"]
    
    examples = []
    count = 0
    
    for idx, missing_cols in missing_data_map.items():
        if count >= num_examples:
            break
            
        row = target_df.iloc[idx]
        
        # Find similar rows in the reference dataset
        similar_rows = find_similar_rows(row, reference_df, match_columns)
        
        if len(similar_rows) == 0:
            continue
            
        # Get the first similar row as an example of "correct" data
        example_row = similar_rows.iloc[0]
        
        # Create the example
        example = {
            "input": {
                "row_data": row.to_dict(),
                "missing_columns": missing_cols,
                "similar_rows": similar_rows.head(3).to_dict('records')
            },
            "expected_output": {
                col: example_row[col] for col in missing_cols if col in example_row
            }
        }
        
        examples.append(example)
        count += 1
    
    return examples

def create_few_shot_prompt(examples: List[Dict[str, Any]]) -> str:
    """
    Create a few-shot prompt for LLM training with examples of data completion.
    
    Args:
        examples: List of example dictionaries
        
    Returns:
        String containing the few-shot prompt
    """
    prompt = """
You are an expert data analyst working with import/export data. Your task is to infer missing values in import records.

Here are examples of how to analyze and infer missing values:

"""

    for i, example in enumerate(examples):
        prompt += f"Example {i+1}:\n"
        prompt += f"Row with missing data: {json.dumps(example['input']['row_data'], indent=2)}\n\n"
        prompt += f"Missing columns: {example['input']['missing_columns']}\n\n"
        prompt += f"Similar rows from historical data:\n{json.dumps(example['input']['similar_rows'], indent=2)}\n\n"
        prompt += f"Inferred values: {json.dumps(example['expected_output'], indent=2)}\n\n"
        prompt += "---\n\n"
    
    prompt += """
Now, I need you to infer the missing values for this new row:

Row with missing data: {row_data}

The missing columns that need to be filled are: {missing_columns}

Here are similar rows from our historical data that might help:
{similar_rows}

Based on the similar rows and patterns in the data, infer the most likely value for each missing column.
Provide your answer as a valid JSON object with only the missing column names and their inferred values.
Example format: {"column_name": "inferred_value"}
"""

    return prompt

def main():
    target_file = "duimp_202502.csv"
    reference_file = "duimp_completa__202412.csv"
    
    # Generate examples for prompt engineering
    examples = generate_prompt_examples(target_file, reference_file)
    
    # Create the few-shot prompt
    prompt = create_few_shot_prompt(examples)
    
    # Save the prompt to a file
    with open("few_shot_prompt.txt", "w") as f:
        f.write(prompt)
    
    print(f"Few-shot prompt saved to few_shot_prompt.txt")
    
    # Also save the examples as JSON for later use
    with open("prompt_examples.json", "w") as f:
        json.dump(examples, f, indent=2)
    
    print(f"Prompt examples saved to prompt_examples.json")

if __name__ == "__main__":
    main() 