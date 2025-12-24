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
PRIORITY_RULES = {
    "ip": "network_map.md",
    "address": "network_map.md",
    "subnet": "network_map.md",
    "vlan": "network_map.md",
    "port": "network_map.md",
    "online": "network_map.md",
    "status": "network_map.md",
    "pihole": "network_map.md",
    "pi-hole": "network_map.md",
    "server": "network_map.md",
    "foster": "network_map.md",
    "router": "network_map.md",
    "proxmox": "network_map.md",
    "hardware": "infrastructure_manifest.md",
    "specs": "infrastructure_manifest.md",
}

# --- TOOLS REGISTRY ---
def run_ping(target):
    if not re.match(r"^[a-zA-Z0-9\.\-]+$", target):
        return "Error: Invalid target format."
    
    param = "-n" if platform.system().lower() == "windows" else "-c"
    if target.lower() == "argument": 
        return "Error: You literally typed 'argument'. Please use a real IP address."

    print(f"   [System] Pinging {target}...")
    command = ["ping", param, "2", target] 
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            return f"SUCCESS: Target {target} is UP.\n{result.stdout[:200]}"
        else:
            return f"FAILURE: Target {target} is DOWN or unreachable."
    except Exception as e:
        return f"Ping failed: {e}"

def run_system_check(arg=None):
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

# --- RAG ENGINE ---
def get_relevant_context(query):
    all_md_files = []
    # 1. Recursive File Search
    for folder in DOC_DIRS:
        if os.path.exists(folder):
            for root, dirs, files in os.walk(folder):
                for file in files:  # <--- This was the missing loop!
                    if file.endswith(".md"):
                        all_md_files.append(os.path.join(root, file))

    # 2. Sniper Mode (Priority Rules)
    forced_files = []
    query_lower = query.lower()
    for keyword, target_file in PRIORITY_RULES.items():
        if keyword in query_lower:
            for path in all_md_files:
                if target_file in path:
                    print(f"   ⚡ SNIPER MODE: '{keyword}' detected -> reading '{target_file}'")
                    forced_files.append(path)
    
    if forced_files:
        final_selection = list(set(forced_files))
    else:
        # 3. Standard Keyword Ranking
        scores = []
        clean_query = query.lower().replace("-", "").replace(" ", "")
        query_words = set(re.findall(r'\w+', query.lower())) - {'the', 'is', 'at', 'in'}
        for path in all_md_files:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read().lower()
                    clean_content = content.replace("-", "").replace(" ", "")
                    score = (clean_content.count(clean_query) * 10) + sum(content.count(w) for w in query_words)
                    if score > 0: scores.append((path, score))
            except: pass
        scores.sort(key=lambda x: x[1], reverse=True)
        final_selection = [p for p, s in scores[:TOP_K_DOCS]]

    # 4. Read Content
    context = ""
    print(f"   -> Reading {len(final_selection)} files:")
    for path in final_selection:
        print(f"      - {os.path.basename(path)}")
        try:
            with open(path, "r", encoding="utf-8") as f:
                context += f"\n\n--- FILE: {os.path.basename(path)} ---\n"
                context += f.read()
        except Exception as e:
            print(f"Error: {e}")
    return context

# --- MAIN APP ---
def main():
    print(f"🚀 Lab Assistant RAG + Multi-Tools (Model: {MODEL_NAME})")
    llm = OllamaLLM(model=MODEL_NAME)
    history = ""

    while True:
        user_input = input("\nYou: ")
        if user_input.lower() in ["exit", "quit"]: break

        context_data = get_relevant_context(user_input)

        system_prompt = (
            "You are a Lab Assistant. You can run diagnostics tools.\n"
            "TOOLS AVAILABLE:\n"
            "- ping <ip_address>: Check if a device is online.\n"
            "- check_server: Check local server uptime.\n"
            "\n"
            "INSTRUCTIONS:\n"
            "1. To use a tool, output: [TOOL: ping 192.168.1.1]\n"
            "2. DO NOT use placeholder text like 'argument'. Use REAL IP addresses from the Context.\n"
            "3. If multiple IPs match the question (e.g. two Pi-holes), RUN THE TOOL FOR BOTH.\n"
            "4. Wait for the Tool Output before saying 'It is online'. Do not guess.\n"
            "\n"
            f"--- CONTEXT ---\n{context_data}\n"
            f"--- HISTORY ---\n{history}\n"
        )

        full_prompt = f"{system_prompt}\nUser: {user_input}\nAssistant:"
        print("Assistant: ", end="", flush=True)
        
        # 1. First Pass: Get AI Plan
        full_response = llm.invoke(full_prompt)
        print(full_response) 

        # 2. Loop through ALL tool requests
        tool_matches = re.findall(r"\[TOOL: (\w+)(?: (.*?))?\]", full_response)
        
        tool_outputs = ""
        if tool_matches:
            print(f"\n   🛠️  Detected {len(tool_matches)} tool requests...")
            for tool_name, tool_arg in tool_matches:
                if tool_name in AVAILABLE_TOOLS:
                    output = AVAILABLE_TOOLS[tool_name](tool_arg)
                    tool_outputs += f"\n[Result for {tool_name} {tool_arg}]:\n{output}\n"
                else:
                    tool_outputs += f"\nError: Tool {tool_name} not found.\n"
            
            # 3. Final Pass: Feed results back to AI
            print(f"   ✅ Feeding results back to AI...")
            follow_up_prompt = (
                f"{full_prompt}\n{full_response}\n"
                f"--- TOOL RESULTS ---\n{tool_outputs}\n"
                "--- INSTRUCTION ---\n"
                "Summarize the results above. Which devices are UP and which are DOWN?"
            )
            final_answer = llm.invoke(follow_up_prompt)
            print(f"\nFinal Answer: {final_answer}")
            history += f"\nUser: {user_input}\nAssistant: {final_answer}\n"
        else:
            history += f"\nUser: {user_input}\nAssistant: {full_response}\n"

if __name__ == "__main__":
    main()