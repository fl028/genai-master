import requests
import json

url = "http://devcontainer_ollama:11434/api/generate"

headers = {
    "Content-Type": "application/json"
}

body = {
    "model": "llama3",
    "prompt": "Hi!",
    "stream": False
}

response = requests.post(url, headers=headers, data=json.dumps(body))

if response.status_code == 200:
    print("Response JSON:", response.json())
else:
    print("Failed to call API. Status code:", response.status_code)
    print("Response:", response.text)

# TODO read from db
# Call API
# Save in db
