import sqlite3
import json
import os
from pathlib import Path

# Path resolution
BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "kizuna_graph.db"

def check_memories():
    print("\n" + "="*60)
    print("📜 KIZUNA SQLITE: MEMORY AUDIT")
    print("="*60 + "\n")

    if not DB_PATH.exists():
        print(f"❌ Database not found at: {DB_PATH}")
        print(f"Current Directory: {os.getcwd()}")
        return

    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()

        # Fetch MemoryEpisodeNodes
        query = "SELECT id, data, created_at FROM nodes WHERE label = 'MemoryEpisodeNode' ORDER BY created_at DESC LIMIT 10"
        cursor.execute(query)
        rows = cursor.fetchall()

        if not rows:
            print("📭 No memories found in the database.")
            # Check if there are ANY nodes at all to verify DB health
            cursor.execute("SELECT count(*) FROM nodes")
            count = cursor.fetchone()[0]
            print(f"📊 Total Nodes in DB: {count}")
        else:
            for row in rows:
                node_id, data_json, created_at = row
                try:
                    data = json.loads(data_json)
                    summary = data.get("summary", "No summary")
                    transcript = data.get("raw_transcript", "[NO TRANSCRIPT]")
                    
                    print(f"🕒 Timestamp: {created_at}")
                    print(f"📝 Summary: {summary}")
                    print(f"🗣️ Full Transcript:")
                    if transcript:
                        for line in str(transcript).split("\n"):
                            print(f"    {line}")
                    else:
                        print("    [EMPTY]")
                    print("-" * 40)
                except Exception as parse_err:
                    print(f"⚠️ Error parsing node {node_id}: {parse_err}")

    except Exception as e:
        print(f"❌ Critical Database Error: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    check_memories()
