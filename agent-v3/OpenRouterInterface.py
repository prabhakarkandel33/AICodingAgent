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

    def stream_response(self,model:str,SYSTEM_PROMPT:str,messages:List[dict],
                        tools:List[Tool]=[],on_text = lambda t: print(t,end="",flush=True)) -> LLMResponse:
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
                tools=tools,
                stream=True,
             )
        tool_acc = {}
        content_parts = []
        usage= {}
        for chunk in response:
            if getattr(chunk,"id",None):
                response_id = chunk.id

            if getattr(chunk,"usage",None):
                usage = {
                    "total_tokens":chunk.usage.total_tokens
                }

            if not chunk.choices:
                continue

            delta = chunk.choices[0].delta

            

            if delta.content:
                content_parts.append(delta.content)
                if on_text:
                    on_text(delta.content)

            
        
            for tc in delta.tool_calls or []:

                i = tc.index
                slot = tool_acc.setdefault(i,{
                    "id":"",
                    "name":"",
                    "arguments":"",
                })

                if tc.id:
                    print("id detected")
                    slot["id"] = tc.id
            
                if tc.function:
                    print("function calls detected")
                    if tc.function.name:
                        slot["name"] += tc.function.name
                    if tc.function.arguments:
                        slot["arguments"] += tc.function.arguments
        
         
        message_content = "".join(content_parts) or None
        tool_calls = [
                {
                    "call_type":"function",
                    "call_id":slot["id"],
                    "name":slot["name"],
                    "arguments":slot["arguments"]
                }
                for _, slot in sorted(tool_acc.items())
        ]

    

        raw_message = {
                "role":"assistant",
                "content":message_content,
                "tool_calls": [
                    {
                        "id":t["call_id"],
                        "type":"function",
                        "function": {
                            "name": t["name"],
                            "arguments":t["arguments"],
                        },
                    }
                    for t in tool_calls

                ] or None
        }

        print(tool_calls)
        return {
                "response_id":response_id,
                "message_content":message_content,
                "tokens_used":usage.get("total_tokens"),
                "total_cost":usage.get("cost"),
                "tool_called":bool(tool_calls),
                "tool_calls":tool_calls,
                "raw_message":raw_message
        }

    def test_stream_call(self):
        data = self.stream_response(
                model="qwen/qwen-2.5-72b-instruct",
                SYSTEM_PROMPT="You are a helpful AI assitant",
                messages = [
                    {
                        "role":"user",
                        "content":"write an essay on sam altman for me"
                    }
                ],
        )
        print(data)
        print("hey works")
        print(data['message_content'],end="")
                
                



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
                tools=tools,
                stream=False
        )

        #for chunk in response:
        #    if chunk.choices[0].delta.content is not None:
        #        print(chunk)
        #        print(chunk.choices[0].delta.content,end="")
        #        message_content = chunk.choices[0].delta.content
        
        #return message_content
        response_id = response.id
        message_content = response.choices[0].message.content
        total_tokens = response.usage.total_tokens
        total_cost = response.usage.cost
        raw_message = response.choices[0].message

        
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
    def build_context(self,messages,chr_budget=120000,last_k=100,window_limit=200):

        context_messages = messages[-last_k:] if len(messages) > window_limit else list(messages) 
        
           
       
        
        return {
                "compaction_required": len(str(context_messages)) > chr_budget,
                "cleaned_message":context_messages
        }





