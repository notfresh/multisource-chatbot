import requests
import json

url = "https://api.302.ai/v1/chat/completions"

payload = json.dumps({
   "model": "deepseek-chat",
   "messages": [
      {
         "role": "user",
         "content": "你是谁"
      }
   ]
})
headers = {
   'Accept': 'application/json',
   'Authorization': 'Bearer ',
   'Content-Type': 'application/json'
}

response = requests.request("POST", url, headers=headers, data=payload)

print(response.text)