
import asyncio
from google import genai
from google.genai import types

async def main():
    client = genai.Client(api_key="FAKE_KEY")
    
    manual_schema = {
        "type": "OBJECT",
        "properties": {
            "name": {"type": "STRING"}
        }
    }

    try:
        response = await client.aio.models.generate_content(
            model="gemini-2.0-flash",
            contents="Hello",
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=manual_schema
            )
        )
        print(f"Parsed: {response.parsed}")
    except Exception as e:
        # We expect 400 for API key, but we want to see if it passes local validation
        if "API key not valid" in str(e):
             print("Passed local validation with manual dict schema.")
        else:
             print(f"Failed local validation: {e}")

if __name__ == "__main__":
    asyncio.run(main())
