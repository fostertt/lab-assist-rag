import os
import sys
import re
from langchain_ollama import OllamaLLM

# --- CONFIGURATION ---
DOC_DIRS = [
    os.path.expanduser("~/projects/infrastructure"),
    os.path.expanduser("~/projects/planning")
]
MODEL_NAME = "llama3.1:8b"
TOP_K_DOCS = 3

# --- CHEAT SHEET (PRIORITY RULES) ---
# If query has these words, ONLY read these files.
PRIORITY_RULES = {
    "ip": "network_map.md",
    "address": "network_map.md",
    "subnet": "network_map.md",
    "vlan": "network_map.md",
    "port": "network_map.md",
    "hardware": "infrastructure_manifest.md",
    "specs": "infrastructure_manifest.md",
}

def rank_documents(query, file_paths):
    """
    Scans files for keywords.
    """
    clean_query = query.lower().replace("-", "").replace(" ", "")
    query_words = set(re.findall(r'\w+', query.lower())) - {'the', 'is', 'at', 'which', 'on', 'and', 'a', 'to', 'in'}
    
    scores = []
    
    for path in file_paths:
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read().lower()
                clean_content = content.replace("-", "").replace(" ", "")
                # Score logic: Exact Phrase (High) + Keyword Matches (Low)
                score = (clean_content.count(clean_query) * 10) + sum(content.count(word) for word in query_words)
                if score > 0:
                    scores.append((path, score))
        except Exception:
            pass

    return sorted(scores, key=lambda x: x[1], reverse=True)

def get_relevant_context(query):
    all_md_files = []
    
    # 1. Find all Markdown files
    for folder in DOC_DIRS:
        if os.path.exists(folder):
            for root, dirs, files in os.walk(folder):
                for file in files:
                    if file.endswith(".md"):
                        all_md_files.append(os.path.join(root, file))

    if not all_md_files:
        return "No markdown files found."

    # 2. Check Priority Rules (The "Sniper Mode")
    forced_files = []
    query_lower = query.lower()
    
    for keyword, target_file in PRIORITY_RULES.items():
        if keyword in query_lower:
            for path in all_md_files:
                if target_file in path:
                    print(f"   ⚡ SNIPER MODE: '{keyword}' detected -> EXCLUSIVELY reading '{target_file}'")
                    forced_files.append(path)
    
    # CRITICAL CHANGE: If we found a priority file, RETURN ONLY THAT. 
    # Do not read the other files. Do not pass go.
    if forced_files:
        final_selection = list(set(forced_files)) # remove duplicates
    else:
        # Standard Ranking if no priority rule matches
        print(f"   🔍 Scanning {len(all_md_files)} files for keywords...")
        ranked_files = rank_documents(query, all_md_files)
        final_selection = [path for path, score in ranked_files[:TOP_K_DOCS]]

    # 3. Read content
    context = ""
    print(f"   -> Reading {len(final_selection)} files:")
    for path in final_selection:
        print(f"      - {os.path.basename(path)}")
        try:
            with open(path, "r", encoding="utf-8") as f:
                context += f"\n\n--- FILE: {os.path.basename(path)} ---\n"
                context += f.read()
        except Exception as e:
            print(f"Error reading {path}: {e}")
            
    return context

def main():
    print(f"🚀 Lab Assistant RAG (Model: {MODEL_NAME})")
    print(f"📂 Monitoring: {DOC_DIRS}")
    print("--------------------------------------------------")

    llm = OllamaLLM(model=MODEL_NAME)
    history = ""

    while True:
        user_input = input("\nYou: ")
        if user_input.lower() in ["exit", "quit"]:
            print("Goodbye!")
            break

        context_data = get_relevant_context(user_input)

        # STRICTER SYSTEM PROMPT
        system_prompt = (
            "You are a strict technical assistant reading a specific documentation file.\n"
            "Your ONLY job is to extract facts from the Context below.\n"
            "DO NOT provide general advice (e.g. 'check your router').\n"
            "DO NOT make up information.\n"
            "If the exact IP/Port/Name is in the text, output it directly.\n"
            "If the info is not in the text, say 'Not found in the docs'.\n"
            "\n"
            f"--- CONTEXT ---\n{context_data}\n"
            f"--- HISTORY ---\n{history}\n"
        )

        full_prompt = f"{system_prompt}\nUser: {user_input}\nAssistant:"

        print("Assistant: ", end="", flush=True)
        response_buffer = ""
        try:
            for chunk in llm.stream(full_prompt):
                print(chunk, end="", flush=True)
                response_buffer += chunk
        except Exception as e:
            print(f"\nError communicating with Ollama: {e}")

        history += f"\nUser: {user_input}\nAssistant: {response_buffer}\n"

if __name__ == "__main__":
    main()