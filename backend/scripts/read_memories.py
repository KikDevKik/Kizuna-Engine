import json
from pathlib import Path
from datetime import datetime

# Path
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_FILE = BASE_DIR / "data" / "graph.json"

def load_data():
    if not DATA_FILE.exists():
        print(f"No graph.json found at {DATA_FILE}")
        return None
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def parse_timestamp(ts_str):
    if not ts_str: return datetime.min
    try:
        # Remove 'Z' if present for fromisoformat compatibility in older python versions if needed
        # But usually fromisoformat handles standard ISO
        return datetime.fromisoformat(str(ts_str).replace('Z', '+00:00'))
    except ValueError:
        return datetime.min

def main():
    data = load_data()
    if not data: return

    # Indexing for speed
    users = {u["id"]: u for u in data.get("users", [])}
    # Agents might be in data['agents'] if seeded, but usually we rely on file system.
    # However, for log viewing, if graph.json has agent references, we might need them.
    # LocalSoulRepository clears self.agents but writes them back to disk from memory (which was loaded from files).
    # So graph.json SHOULD have agents.
    agents = {a["id"]: a for a in data.get("agents", [])}
    episodes = {e["id"]: e for e in data.get("episodes", [])}
    dreams = {d["id"]: d for d in data.get("dreams", [])}

    # Shadow Edges (User -> Dream)
    # JSON structure: "shadows": {"user_id": [edge_obj, ...]}
    user_dreams = {}
    raw_shadows = data.get("shadows", {})
    for uid, edges in raw_shadows.items():
        user_dreams[uid] = []
        for edge in edges:
            dream_id = edge["target_id"]
            if dream_id in dreams:
                user_dreams[uid].append(dreams[dream_id])

    resonances = data.get("resonances", [])

    print("\n" + "="*60)
    print("📜 KIZUNA ENGINE: MEMORY LOG VIEWER")
    print("="*60 + "\n")

    # Group resonances by Agent
    agent_resonances = {} # agent_id -> list of resonance edges
    for r in resonances:
        aid = r["target_id"]
        if aid not in agent_resonances:
            agent_resonances[aid] = []
        agent_resonances[aid].append(r)

    # Iterate Agents
    # If no agents in graph.json (e.g. only in files), we iterate resonances to find agent IDs
    all_agent_ids = set(agents.keys()) | set(agent_resonances.keys())

    for agent_id in all_agent_ids:
        agent = agents.get(agent_id, {"name": "Unknown Agent", "id": agent_id})
        print(f"🤖 AGENT: {agent.get('name', 'Unknown')} ({agent_id})")

        res_list = agent_resonances.get(agent_id, [])
        if not res_list:
            print("   (No interactions recorded)")
            continue

        for res in res_list:
            user_id = res["source_id"]
            user = users.get(user_id, {"name": "Unknown User"})
            affinity = res.get("affinity_level", 0.0)

            print(f"\n   👤 User: {user.get('name', 'Unknown')} (ID: {user_id})")
            print(f"      ❤️ Affinity: {affinity:.1f}")
            print(f"      ⏳ Timeline:")

            timeline = []

            # 1. Episodes (Shared Memories)
            shared_ids = res.get("shared_memories", [])
            for eid in shared_ids:
                if eid in episodes:
                    ep = episodes[eid]
                    timeline.append({
                        "type": "EPISODE",
                        "obj": ep,
                        "time": parse_timestamp(ep.get("timestamp"))
                    })

            # 2. Dreams (User Specific)
            # Dreams are global to the user, not specific to the agent technically,
            # but they are part of the user's narrative.
            # We can show them interleaved.
            u_dreams = user_dreams.get(user_id, [])
            for dream in u_dreams:
                timeline.append({
                    "type": "DREAM",
                    "obj": dream,
                    "time": parse_timestamp(dream.get("timestamp"))
                })

            # Sort by time
            timeline.sort(key=lambda x: x["time"])

            if not timeline:
                print("      (No history)")

            for event in timeline:
                t_str = event["time"].strftime("%Y-%m-%d %H:%M:%S")
                if event["type"] == "EPISODE":
                    ep = event["obj"]
                    summary = ep.get("summary", "No summary")
                    transcript = ep.get("raw_transcript")
                    valence = ep.get("emotional_valence", 0.0)

                    print(f"\n      [{t_str}] 🗣️ EPISODE (Valence: {valence:.1f})")
                    print(f"      Summary: {summary}")
                    if transcript:
                        # Indent transcript
                        print(f"      Transcript:")
                        for line in transcript.split("\n"):
                            print(f"        {line}")
                    else:
                        print(f"      Transcript: [NULL]")

                elif event["type"] == "DREAM":
                    dream = event["obj"]
                    theme = dream.get("theme", "Unknown")
                    intensity = dream.get("intensity", 0.0)
                    print(f"\n      [{t_str}] 🌙 DREAM (Intensity: {intensity:.1f})")
                    print(f"      Theme: {theme}")

        print("\n" + "-"*60 + "\n")

if __name__ == "__main__":
    main()
