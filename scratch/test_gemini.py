import os
from google import genai

def test_gemini():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        from dotenv import load_dotenv
        load_dotenv()
        api_key = os.environ.get("GEMINI_API_KEY")
        
    print("API Key exists:", bool(api_key))
    client = genai.Client(api_key=api_key)
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents="Say Hello"
        )
        print("Response:", response.text)
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    test_gemini()
