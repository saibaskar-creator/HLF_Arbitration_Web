import os

def load_prompt(prompt_filename):
    """
    Reads a text file from the 'prompts/' directory.
    """
    # Go up one level from 'src' to get to root, then into 'prompts'
    base_dir = os.path.dirname(os.path.dirname(__file__))
    prompt_path = os.path.join(base_dir, "prompts", prompt_filename)
    
    try:
        with open(prompt_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        print(f"⚠️ Warning: Prompt file '{prompt_filename}' not found. Using default.")
        return "You are a helpful assistant."