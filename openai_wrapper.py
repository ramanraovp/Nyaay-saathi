import os
import requests
import json

# Simple wrapper for OpenAI API to avoid client initialization issues
class SimpleOpenAI:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.openai.com/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def chat_completions_create(self, model="gpt-4", messages=None, temperature=0.7, max_tokens=1000):
        if messages is None:
            messages = []
        
        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        response = requests.post(url, headers=self.headers, data=json.dumps(payload))
        response.raise_for_status()
        return SimpleResponse(response.json())

# Simple response object to match OpenAI's structure
class SimpleResponse:
    def __init__(self, data):
        self.data = data
        self.choices = [SimpleChoice(data["choices"][0])] if "choices" in data and data["choices"] else []

class SimpleChoice:
    def __init__(self, data):
        self.message = SimpleMessage(data["message"]) if "message" in data else None

class SimpleMessage:
    def __init__(self, data):
        self.content = data.get("content", "")

def get_openai_client(api_key=None):
    if api_key is None:
        api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        raise ValueError("No OpenAI API key found")
    
    # Try to use the official client first
    try:
        import openai
        try:
            # First try the newer style
            return openai.OpenAI(api_key=api_key)
        except (TypeError, AttributeError):
            # Fall back to older style
            openai.api_key = api_key
            return openai
    except:
        # If all else fails, use our simple client
        return SimpleOpenAI(api_key)
