from BaseInterface import LLMInterface
import sys
from typing import List
from core_types import *
from dotenv import load_dotenv
import requests
import json
import inspect
from openrouter import OpenRouter


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

    def harness_tool_parse(self,tool_id,content,name):
        return {
                "role":"tool",
                "name":name,
                "tool_call_id":tool_id,
                "content":content
            }

    def bind_tools(self,tools:List[Tool]):
        tool_schemas = []
        for tool in tools:
            tool_schemas.append(self.generate_schema(tool))

        return tool_schemas

    def generate(self,model:str,SYSTEM_PROMPT:str,messages:List[dict],tools:List[Tool]=[]) -> LLMResponse:
        system_message = {
            "role":"system",
            "content":SYSTEM_PROMPT,
        }

        messages = [system_message] + messages
        if not self.api_key:
            raise ValueError("Please provide an api key")
            return
        
        if tools:
            tools = self.bind_tools(tools)


        open_router = OpenRouter(api_key = self.api_key)

        response = open_router.chat.send(
                model = model,
                messages = messages,
                tools=tools
        )
        
        response_id = response.id
        message_content = response.choices[0].message.content
        total_tokens = response.usage.total_tokens
        total_cost = response.usage.cost
        raw_message = response.choices[0].message

        #print(raw_message) 
        #print(response['choices'][0]['message']['tool_calls'])
        #print(response['choices'][0]['message']['tool_calls'] == None) 
        
    
        response_tool_calls = raw_message.tool_calls
        
        tool_called = False if response_tool_calls == None else True
        
        
        
            
        
        
    
            
            
        tool_calls = []
        if tool_called:
            for tool_call in response_tool_calls:
                    
                tool_calls.append({
                        'call_type':tool_call.type,
                        'call_id':tool_call.id,
                        'name':tool_call.function.name,
                        'arguments':tool_call.function.arguments
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

            
                            



    





