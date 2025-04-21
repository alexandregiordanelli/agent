import os
import subprocess
import argparse
from dotenv import load_dotenv

def check_api_key():
    """Check if the OpenAI API key is set in the .env file."""
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or api_key == "your_openai_api_key_here":
        print("\nERROR: OpenAI API key not set or is still the default value.")
        print("Please update the .env file with your API key.")
        set_api_key = input("Would you like to set your API key now? (y/n): ")
        if set_api_key.lower() == 'y':
            api_key = input("Enter your OpenAI API key: ")
            with open(".env", "w") as f:
                f.write(f"OPENAI_API_KEY={api_key}")
            print("API key saved to .env file.")
            return True
        return False
    return True

def run_analysis():
    """Run the analysis script."""
    print("\nRunning analysis of missing data patterns...")
    subprocess.run(["python", "analyze.py"])

def run_prompt_engineering():
    """Run the prompt engineering script."""
    print("\nGenerating prompt examples for LLM training...")
    subprocess.run(["python", "prompt_engineering.py"])

def run_main(args):
    """Run the main script with the provided arguments."""
    print("\nRunning data completion agent...")
    cmd = ["python", "main.py"]
    
    if args.target:
        cmd.extend(["--target", args.target])
    if args.reference:
        cmd.extend(["--reference", args.reference])
    if args.output:
        cmd.extend(["--output", args.output])
    if args.model:
        cmd.extend(["--model", args.model])
    if args.batch_size:
        cmd.extend(["--batch-size", str(args.batch_size)])
    if args.max_similar:
        cmd.extend(["--max-similar", str(args.max_similar)])
    
    subprocess.run(cmd)

def show_menu():
    """Display the main menu and get user choice."""
    print("\n===== Import Data Completion Agent =====")
    print("1. Run data completion agent (main.py)")
    print("2. Analyze missing data patterns (analyze.py)")
    print("3. Generate prompt examples (prompt_engineering.py)")
    print("4. Exit")
    choice = input("\nEnter your choice (1-4): ")
    return choice

def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description='Run Import Data Completion Agent')
    parser.add_argument('--target', type=str, help='Path to the target CSV file with missing data')
    parser.add_argument('--reference', type=str, help='Path to the reference CSV file')
    parser.add_argument('--output', type=str, help='Path to save the completed CSV file')
    parser.add_argument('--model', type=str, help='LLM model to use')
    parser.add_argument('--batch-size', type=int, help='Number of rows to process in each batch')
    parser.add_argument('--max-similar', type=int, help='Maximum number of similar rows to include in each prompt')
    parser.add_argument('--non-interactive', action='store_true', help='Run in non-interactive mode')
    
    return parser.parse_args()

def main():
    """Main entry point."""
    args = parse_args()
    
    # Check if the files exist
    required_files = ["main.py", "agent.py", "utils.py", "analyze.py", "prompt_engineering.py"]
    missing_files = [f for f in required_files if not os.path.exists(f)]
    
    if missing_files:
        print(f"ERROR: The following required files are missing: {', '.join(missing_files)}")
        print("Please make sure all project files are present before running this script.")
        return
    
    # Check if the OpenAI API key is set
    if not check_api_key():
        print("Exiting due to missing API key.")
        return
    
    # If non-interactive mode is specified, run the main script with the provided arguments
    if args.non_interactive:
        run_main(args)
        return
    
    # Interactive mode
    while True:
        choice = show_menu()
        
        if choice == '1':
            # Get parameters for main.py
            target = input("Enter path to target CSV file (default: duimp_202502.csv): ") or None
            reference = input("Enter path to reference CSV file (default: duimp_completa__202412.csv): ") or None
            output = input("Enter path for output CSV file (default: duimp_completed.csv): ") or None
            model = input("Enter LLM model to use (default: gpt-3.5-turbo): ") or None
            batch_size = input("Enter batch size (default: 10): ") or None
            max_similar = input("Enter maximum number of similar rows (default: 5): ") or None
            
            # Update args with user input
            if target:
                args.target = target
            if reference:
                args.reference = reference
            if output:
                args.output = output
            if model:
                args.model = model
            if batch_size:
                try:
                    args.batch_size = int(batch_size)
                except ValueError:
                    print("Invalid batch size. Using default.")
            if max_similar:
                try:
                    args.max_similar = int(max_similar)
                except ValueError:
                    print("Invalid max similar rows. Using default.")
            
            run_main(args)
        
        elif choice == '2':
            run_analysis()
        
        elif choice == '3':
            run_prompt_engineering()
        
        elif choice == '4':
            print("Exiting...")
            break
        
        else:
            print("Invalid choice. Please enter a number between 1 and 4.")

if __name__ == "__main__":
    main() 