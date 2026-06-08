import os
import glob
from quill import api

def siphon_knowledge(context):
    """
    Scans a designated research folder and extracts lines containing keywords,
    then inserts them into the document as a structured list.
    """
    # In a real scenario, this path would be configured in the plugin settings
    research_dir = os.path.expanduser("~/quill_research")
    
    if not os.path.exists(research_dir):
        api.announce("Research directory not found. Please create ~/quill_research")
        return

    results = []
    try:
        # Find all text and markdown files
        files = glob.glob(f"{research_dir}/*.txt") + glob.glob(f"{research_dir}/*.md")
        
        for file_path in files:
            filename = os.path.basename(file_path)
            with open(file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    # Simple heuristic: find lines that look like "Key: Value" or start with bullets
                    stripped = line.strip()
                    if stripped.startswith(("-", "*", "Key:")):
                        results.append(f"[{filename}:{line_num}] {stripped}")

        if not results:
            api.announce("No research notes found in the directory.")
            return

        # Insert formatted list into document
        output = "\n".join([f"• {item}" for item in results])
        api.insert_text(f"\n--- Research Siphon Results ---\n{output}\n")
        api.announce(f"Siphoned {len(results)} items from {len(files)} files.")
        
    except Exception as e:
        api.announce(f"Siphon failed: {str(e)}")

# Register the command with the QUILL API
api.register_command("siphon_knowledge", siphon_knowledge)
