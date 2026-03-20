import os

def load_skill_prompt(skill_name: str) -> str:
    """
    Loads a skill instruction from a .md file in the prompts/ directory.
    
    Args:
        skill_name: Name of the file without extension (e.g., 'evaluacion_skill')
        
    Returns:
        The content of the markdown file as a string.
    """
    # Base directory for the agents package
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    prompt_path = os.path.join(base_dir, "prompts", f"{skill_name}.md")
    
    try:
        if not os.path.exists(prompt_path):
            # Fallback to .txt if .md doesn't exist yet (for transition)
            prompt_path = prompt_path.replace(".md", ".txt")
            
        with open(prompt_path, "r", encoding="utf-8") as file:
            return file.read()
    except Exception as e:
        print(f"[ERROR] Could not load skill prompt {skill_name}: {e}")
        return "You are a helpful AI assistant specialized in professional development."
