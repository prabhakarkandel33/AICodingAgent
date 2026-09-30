import requests
import json
from dotenv import load_dotenv
import os

load_dotenv()

class OpenRouter:
    def __init__(self,model,api_key,tools=[]):
        if not model:
            raise ValueError("Please define a model name")
        if not api_key:
            raise ValueError("Please provide an api key")
        self.model=model
        self.api_key=api_key
        self.tools=tools 

      



    def invoke(self,messages):
        response = requests.post(
           url = "https://openrouter.ai/api/v1/chat/completions",                headers = {
                    "Authorization":"Bearer "+self.api_key,
        },
        
            data = json.dumps({
            "model": self.model,
            "messages":messages,
            "tools":self.tools
            }
        )
    )
    
        return response



