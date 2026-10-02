from BaseInterface import LLMInterface
import sys
from typing import List
from core_types import *
from dotenv import load_dotenv
import os
import requests
import json
import inspect
load_dotenv()

"""

    name:str
    description:str
    arguments:List[str,dict[str,Any]]
    func:Callable[[Any],Any]

def call(self,func,**args):
        return self.func(**args)


"""



class OpenRouterInterface(LLMInterface):

    def __init__(self,api_key=None):
        self.api_key = api_key

    def generate_schema(self,tool:Tool):
        properties = {}
        required = []

        signature = inspect.signature(tool.func)

        for name,parameter in signature.parameters.items():
            annotation = parameter.annotation

            if annotation is str:
                properties[name] = {"type":"string"}
            elif annotation is int:
                properties[name] = {"type":"number"}
            elif annotation is float:
                properties[name] = {"type":"float"}
            elif annotation is list:
                properties[name]={"type":"array"}
            else:
                properties[name] = {"type":"string"}
            
            if parameter.default is inspect.Parameter.empty:
                required.append(name)
        return {
            "type":"function",
            "function":{
                "name":tool.name,
                "description":tool.description,
                "parameters":{
                    "type":"object",
                    "properties":properties,
                    "required":required
                }
            }
        }

    def bind_tools(self,tools:List[Tool]):
        tool_schemas = []
        for tool in tools:
            tool_schemas.append(self.generate_schema(tool))

        return tool_schemas

    def generate(self,model:str,messages:List[dict],tools:List[Tool]=[]) -> LLMResponse:
        if not self.api_key:
            raise ValueError("Please provide an api key")
            return
        
        if tools:
            tools = self.bind_tools(tools)

        response = requests.post(
                url = "https://openrouter.ai/api/v1/chat/completions",
                headers = {
                    "Authorization":"Bearer "+self.api_key,
                },
                data = json.dumps(
                    {
                        "model":model,
                        "messages":messages,
                        "tools":tools
                    }
                )
            )
        response = json.loads(response.text)
        response_id = response['id']
        message_content = response['choices'][0]['message']['content']
        total_tokens = response['usage']['total_tokens']
        total_cost = response['usage']['cost']
        raw_message = response['choices'][0]['message']

        
        #print(response['choices'][0]['message']['tool_calls'])
        #print(response['choices'][0]['message']['tool_calls'] == None) 
        
        response_tool_calls = raw_message.get("tool_calls") or []
        tool_called = len(response_tool_calls) > 0
        
            
        
        
    
            
            
        tool_calls = []
        if tool_called:
            for tool_call in response_tool_calls:
                    
                tool_calls.append({
                        'call_type':tool_call['type'],
                        'call_id':tool_call['id'],
                        'name':tool_call['function']['name'],
                        'arguments':tool_call['function']['arguments']
                    })
        

        return {
            "response_id":response_id,
                "message_content":message_content,
                "tokens_used": total_tokens,
                "total_cost": total_cost,
                "tool_called":tool_called,
                "tool_calls": tool_calls,
                "raw_message":raw_message,

                
            }

            
                            

def add(a:int,b:int):
    """
    Add two numbers together
    """
    return a + b
            
        
#llm = OpenRouterInterface(api_key=os.getenv("OPENROUTER_API_KEY"))
#data = llm.generate(model="qwen/qwen-2.5-72b-instruct",
#             messages = [
#             {"role":"user","content":"Add two numbers 2 and 3 explicitly return a tool call plz"}
 #            ] , tools=[
#                        Tool(add)
#]
#)

    





