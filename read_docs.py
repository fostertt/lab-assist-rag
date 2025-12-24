import os
import glob
import ollama

# CONFIGURATION
# ----------------
# 1. Get the absolute path of the folder where this script lives
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# 2. Define paths relative to the script (Works from ANY terminal location)
SCAN_PATHS = [
    os.path.join(SCRIPT_DIR, "../infrastructure"),
    os.path.join(SCRIPT_DIR, "../planning")
]
MODEL_NAME = "llama3.1:8b"

# Global chat history (The "Short-term Memory")
conversation_history = []

def read_all_docs():
    """Reads ALL markdown files in the specified folders."""
    combined_context = ""
    total_files = 0
    
    print("📚 Scanning documentation...")
    
    for folder in SCAN_PATHS:
        files = glob.glob(os.path.join(folder, "*.md"))
        
        if not files:
            continue
            
        for file_path in files:
            try:
                with open(file_path, "r") as f:
                    filename = os.path.basename(file_path)
                    folder_name = os.path.basename(folder)
                    
                    # Debug print to confirm what we found
                    print(f"   found: {filename}")
                    
                    # Tagging the source so the AI knows where info comes from
                    combined_context += f"\n--- SOURCE: {folder_name}/{filename} ---\n"
                    combined_context += f.read()
                    combined_context += f"\n--- END SOURCE ---\n"
                    total_files += 1
            except Exception as e:
                print(f"Error reading {file_path}: {e}")

    print(f"✅ Loaded {total_files} files.")
    return combined_context

def ask_lab_assistant(question, system_context):
    """Sends question + history to Ollama."""
    
    # Add user's question to memory
    conversation_history.append({'role': 'user', 'content': question})
    
    # The Brain: Instructions on how to handle ambiguity
    messages = [
        {'role': 'system', 'content': f"""
        You are a Lab Assistant for Tyrrell's home server infrastructure.
        
        CORE RULES:
        1. Answer based ONLY on the provided documentation.
        2. **Inference vs Clarification:** - If a user uses a generic term (e.g. "the server") and the docs strongly imply a specific device (e.g. "Foster-Server"), you may INFER it and answer.
           - If it is ambiguous, ASK the user to clarify (e.g. "By 'server', do you mean Foster-Server or the Tailscale node?").
        3. Be concise and technical.
        
        DOCUMENTATION:
        {system_context}
        """}
    ]
    
    # Append the chat history so it remembers previous clarifications
    messages.extend(conversation_history)

    print(f"🤖 Asking {MODEL_NAME}...")

    try:
        response = ollama.chat(model=MODEL_NAME, messages=messages)
        answer = response['message']['content']
        
        print("\nAnswer:")
        print(answer)
        print("-" * 40) # Divider for readability
        
        # Add AI's answer to memory
        conversation_history.append({'role': 'assistant', 'content': answer})
        
    except Exception as e:
        print(f"Error communicating with Ollama: {e}")

if __name__ == "__main__":
    print("🤖 Lab Assistant is ready! (Type 'exit' to quit)")
    print("-----------------------------------------------")
    
    # Load docs once
    context_cache = read_all_docs()
    
    while True:
        try:
            user_input = input("\n👉 You: ")
            
            # Clean exit commands
            if user_input.lower().strip() in ['exit', 'quit', 'q']:
                print("👋 Goodbye!")
                break
                
            # Skip empty "Ghost" inputs (This fixes your double-print bug)
            if not user_input.strip():
                continue

            ask_lab_assistant(user_input, context_cache)
            
        except KeyboardInterrupt:
            # Handle Ctrl+C gracefully
            print("\n👋 Goodbye!")
            break