import os
import sys
import re
import subprocess
import platform
from langchain_ollama import OllamaLLM

# --- CONFIGURATION ---
DOC_DIRS = [
    os.path.expanduser("~/projects/infrastructure"),
    os.path.expanduser("~/projects/planning")
]
MODEL_NAME = "llama3.1:8b"
TOP_K_DOCS = 3

# --- CHEAT SHEET (PRIORITY RULES) ---
# MAP KEYWORDS TO SPECIFIC FILES
PRIORITY_RULES = {
    # Network Terms
    "ip": "network_map.md",
    "address": "network_map.md",
    "subnet": "network_map.md",
    "vlan": "network_map.md",
    "port": "network_map.md",
    "online": "network_map.md",  # If asking if something is online, we need IPs
    "status": "network_map.md",
    
    # Specific Devices (Add your own here!)
    "pihole": "network_map.md",
    "pi-hole": "network_map.md",
    "server": "network_map.md",
    "foster": "network_map.md",
    "router": "network_map.md",
    "proxmox": "network_map.md",
    
    # Hardware/Planning
    "hardware": "infrastructure_manifest.md",
    "specs": "infrastructure_manifest.md",
    "plan": "PROJECT_MASTER_LIST.md",
    "todo": "PROJECT_MASTER_LIST.md",
}

# --- TOOLS REGISTRY (Safe Commands) ---
def run_ping(target):
    """Pings a target 3 times and returns the result."""
    # Safety: Basic sanity check to prevent command injection
    if not re.match(r"^[a-zA-Z0-9\.\-]+$", target):
        return "Error: Invalid target format."
    
    param = "-n" if platform.system().lower() == "windows" else "-c"
    print(f"   [System] Pinging {target}...") # Feedback for user
    command = ["ping", param, "3", target]
    
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=10)
        return result.stdout
    except Exception as e:
        return f"Ping failed: {e}"

def run_system_check(arg=None):
    """Checks basic system stats (uptime, disk usage)."""
    try:
        print("   [System] Checking local stats...")
        uptime = subprocess.check_output("uptime", shell=True).decode()
        disk = subprocess.check_output("df -h /", shell=True).decode()
        return f"--- UPTIME ---\n{uptime}\n--- DISK ---\n{disk}"
    except Exception as e:
        return f"Check failed: {e}"

AVAILABLE_TOOLS = {
    "ping": run_ping,
    "check_server": run_system_check
}

# --- RAG ENGINE (Sniper Mode) ---
def rank_documents(query, file_paths):
    clean_query = query.lower().replace("-", "").replace(" ", "")
    query_words = set(re.findall(r'\w+', query.lower())) - {'the', 'is', 'at', 'which', 'on', 'and', 'a', 'to', 'in'}
    scores = []
    
    for path in file_paths:
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read().lower()
                clean_content = content.replace("-", "").replace(" ", "")
                score = (clean_content.count(clean_query) * 10) + sum(content.count(word) for word in query_words)
                if score > 0:
                    scores.append((path, score))
        except Exception:
            pass

    return sorted(scores, key=lambda x: x[1], reverse=True)

def get_relevant_context(query):
    all_md_files = []
    for folder in DOC_DIRS:
        if os.path.exists(folder):
            for root, dirs, files in os.walk(folder):
                for file in files:
                    if file.endswith(".md"):
                        all_md_files.append(os.path.join(root, file))

    forced_files = []
    query_lower = query.lower()
    
    # Check strict matches from PRIORITY_RULES
    for keyword, target_file in PRIORITY_RULES.items():
        if keyword in query_lower:
            for path in all_md_files:
                if target_file in path:
                    print(f"   ⚡ SNIPER MODE: '{keyword}' detected -> EXCLUSIVELY reading '{target_file}'")
                    forced_files.append(path)
    
    if forced_files:
        final_selection = list(set(forced_files))
    else:
        print(f"   🔍 Scanning {len(all_md_files)} files for keywords...")
        ranked_files = rank_documents(query, all_md_files)
        final_selection = [path for path, score in ranked_files[:TOP_K_DOCS]]

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

# --- MAIN APP ---
def main():
    print(f"🚀 Lab Assistant RAG + Tools (Model: {MODEL_NAME})")
    print(f"🛠️  Tools Enabled: {list(AVAILABLE_TOOLS.keys())}")
    print("--------------------------------------------------")

    llm = OllamaLLM(model=MODEL_NAME)
    history = ""

    while True:
        user_input = input("\nYou: ")
        if user_input.lower() in ["exit", "quit"]:
            print("Goodbye!")
            break

        context_data = get_relevant_context(user_input)

        system_prompt = (
            "You are a Lab Assistant capable of running diagnostics.\n"
            "You have access to the following TOOLS:\n"
            "- ping <ip_address>: Check if a device is online.\n"
            "- check_server: Check local server uptime and disk space (no arguments needed).\n"
            "\n"
            "INSTRUCTIONS:\n"
            "1. If the user asks to check a status, YOU MUST USE A TOOL.\n"
            "2. To use a tool, output strictly: [TOOL: tool_name argument]\n"
            "3. Look for the IP address of the device in the provided CONTEXT.\n"
            "4. If you find the IP, use it. If not, ask the user for it.\n"
            "\n"
            f"--- CONTEXT ---\n{context_data}\n"
            f"--- HISTORY ---\n{history}\n"
        )

        full_prompt = f"{system_prompt}\nUser: {user_input}\nAssistant:"

        print("Assistant: ", end="", flush=True)
        
        response_buffer = ""
        full_response = llm.invoke(full_prompt) 
        
        # Check for Tool Usage
        tool_match = re.search(r"\[TOOL: (\w+)(?: (.*?))?\]", full_response)
        
        if tool_match:
            tool_name = tool_match.group(1)
            tool_arg = tool_match.group(2) or ""
            print(f"\n   🛠️  AI Request: {tool_name} {tool_arg}")

            if tool_name in AVAILABLE_TOOLS:
                tool_output = AVAILABLE_TOOLS[tool_name](tool_arg)
                print(f"   ✅ Tool Output Received ({len(tool_output)} bytes)")
                
                # Feed result back to AI
                follow_up_prompt = (
                    f"{full_prompt}\n{full_response}\n"
                    f"--- TOOL OUTPUT ---\n{tool_output}\n"
                    "--- INSTRUCTION ---\n"
                    "Interpret the tool output above for the user. Is the device online? What is the latency?"
                )
                final_answer = llm.invoke(follow_up_prompt)
                print(final_answer)
                response_buffer = final_answer
            else:
                print(f"❌ Error: Tool '{tool_name}' not found.")
                print(full_response)
        else:
            print(full_response)
            response_buffer = full_response

        history += f"\nUser: {user_input}\nAssistant: {response_buffer}\n"

if __name__ == "__main__":
    main()