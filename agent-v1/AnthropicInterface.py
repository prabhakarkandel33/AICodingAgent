from anthropic.types.message import Message
from anthropic.types.text_block import TextBlock
from anthropic.types.tool_use_block import ToolUseBlock
from BaseInterface import LLMInterface
import sys
from typing import List
from core_types import *
import json
import inspect
import os
from anthropic import Anthropic

from dotenv import load_dotenv

load_dotenv()


"""
Anthropic's expected tool call format:

 {
                     "name":"add_nums",
                     "description":"add two numbers",
                     "input_schema":{
                        "type":"object",
                        "properties":{
                            "a":{
                                "type":"number",
                                "description":"first number"
                            },
                            "b":{
                                "type":"number",
                                "description":"second number"
                            }
                        },
                        "required":["a","b"]
                    }
                    },
                    {
"name":"sub_nums",
                     "description":"subtract two numbers",
                     "input_schema":{
                        "type":"object",
                        "properties":{
                            "a":{
                                "type":"number",
                                "description":"first number"
                            },
                            "b":{
                                "type":"number",
                                "description":"second number"
                            }
                        },
                        "required":["a","b"]
                    }
                    }
                ]





"""

class AnthropicInterface(LLMInterface):

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
                "name":tool.name,
                "description":tool.description,
                "input_schema":{
                    "type":"object",
                    "properties":properties,
                    "required":required
                }
        }

    def harness_tool_parse(self,tool_id,content,name=""):
        return {
                "role":"user",
                "content":[
                    {
                        "type":"tool_result",
                        "tool_use_id":tool_id,
                        "content":content
                    }
                ]
        }

    def bind_tools(self,tools:List[Tool]):
        tool_schemas = []
        for tool in tools:
            tool_schemas.append(self.generate_schema(tool))

        return tool_schemas

    def generate(self,model:str,SYSTEM_PROMPT:str,messages:List[dict],tools:List[Tool]=[]) -> LLMResponse:
        
        #for index,message in enumerate(messages):
        #    print(message)
        #    if isinstance(message,TextBlock):
        #        print("text block detected")
        #        messages[index] = {
        #            "role":"assistant",
        #            "content":message.text,
        #        }
    
        client = Anthropic(api_key=self.api_key)
        tools = self.bind_tools(tools)
        response = client.messages.create(
                max_tokens=1024,
                system=SYSTEM_PROMPT,
                messages=messages,
                model=model,
                tools=tools
        )
       
        
        response_id = response.id
        response_content = response.content
        message_content = ""
        tool_called = False
        tool_calls = []

        
        for chunk in response_content:
            if isinstance(chunk,TextBlock):
                raw_agent_message = {
                    "role":"assistant",
                    "content":chunk.text
                }

                message_content += chunk.text
            if isinstance(chunk,ToolUseBlock):
                tool_called=True
                tool_calls.append(
                    {
                        "call_type":chunk.type,
                        "call_id":chunk.id,
                        "name":chunk.name,
                        "arguments":chunk.input
                    }
                )
                raw_agent_message = {
                    "role":"assistant",
                    "content": [
                        {
                            "type":"tool_use",
                            "id":chunk.id,
                            "name":chunk.name,
                            "input":chunk.input
                        }
                    ]
                }
                
        tokens_used = response.usage.input_tokens + response.usage.output_tokens
        
        

        return {
            "response_id":response_id,
                "message_content":message_content,
                "tokens_used": tokens_used,
                "total_cost": "",
                "tool_called":tool_called,
                "tool_calls": tool_calls,
                "raw_message":raw_agent_message,

                
        }
#claude = AnthropicInterface(os.getenv("ANTHROPIC_API_KEY"))
#data = claude.generate(
#        model = "claude-haiku-4-5-20251001",
#        messages = [{
#            "role":"user",
#            "content" : "hello claude add 2 and 3, subtract 5 and 3 and tell me about yourself as well",
#        }],
#        tools=[]
#)

