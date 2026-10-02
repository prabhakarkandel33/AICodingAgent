from tool_registry import *
from core_types import *
from OpenRouterInterface import *
from typing import List
import json

import os
from dotenv import load_dotenv

load_dotenv()


"""
 

class Tool:


    def __init__(self,func):
        self.name = func.__name__
        self.description = func.__doc__
        self.func=func

    def call(self,arguments):
        return self.func(**arguments)


class LLMToolCall(TypedDict):
    call_type:str
    call_id:str
    name:str
    arguments:dict[str,Any]



class LLMResponse(TypedDict):
    response_id:str
    message_content:str | None
    tokens_used: int
    total_cost: float
    tool_called: bool
    tool_calls: List[LLMToolCall] | None

{'response_id': 'gen-1790847767-GZlrXfg69vSaHCKQdV4y', 'message_content': None, 'tokens_used': 351, 'total_cost': 0.00012736, 'tool_called': True, 'tool_calls': [{'call_type': 'function', 'call_id': 'call_ksOmDD3ilOpmGWVi47QGdxbX', 'name': 'add', 'arguments': '{"a": 2, "b": 3}'}]}


"""
class Agent:
    def __init__(
        self,
        model:str,
        api_key:str,
        tools:List[Tool],
        provider:str,
        MAX_TOOL_CALLS:int=10,
        SYSTEM_PROMPT:str="You are a helpful AI assistant use your tool registry whenever applicable and on tool calls just one shot the thing"
    ):
        self.model = model
        self.tools = tools
        
        self.provider = provider


        #in future can expand this
        if (self.provider == "openrouter"):
            self.llm = OpenRouterInterface(api_key)
        else:
            self.llm = None
        self.agent_messages = [
{
                "role":"system",
                "content":SYSTEM_PROMPT,
            }
        ]
        self.MAX_TOOL_CALLS=MAX_TOOL_CALLS

    def invoke(self,messages:Dict):
        self.agent_messages.append(messages)
        response = self.llm.generate(self.model,
                                    self.agent_messages,
                                    self.tools
        )
        tool_call_count = 0
            
        
        while response.get('tool_called') and response.get('tool_calls'):
            self.agent_messages.append(
                    response['raw_message']
            )
            for tool_call in response['tool_calls']:

                if(tool_call_count >= self.MAX_TOOL_CALLS):
                    break
                tool_call_count += 1

            
    
                parsed_tool = parse_tool_calls(tool_call)
                if isinstance(parsed_tool,ParseError):
                    self.agent_messages.append(
                        {"role":"tool","tool_call_id":tool_call["call_id"],
                            "content":f"Tool Call error: {parsed_tool.raw} Reason: {parsed_tool.reason}"
                         }
                    )
                    continue
                name = parsed_tool.name
                tool_call_id = parsed_tool.id
                args = parsed_tool.args
                
                
                
                tool = next((t for t in self.tools if t.name==name),None)#search for the tool name from response in our registry probably better to define our registry as dict :(
                if tool is None:
                    content = json.dumps(
                        {
                            "error": f"unknown tool {name}"
                        }
                    )
                else:
                    validation_errors = validate_args(tool,args)
                    if validation_errors == []:
                        try:
                            tool_response = tool.call(**args)
                        except Exception as e:
                            tool_response = str(e)
                        print(f"Tool called successfully: {name} Response: {tool_response}") 
                        content = json.dumps(tool_response)
                    else:
                        content = "\n".join(validation_errors)

                self.agent_messages.append(
                    {
                        "role":"tool",
                        "tool_call_id":tool_call["call_id"],
                        "content":content,
                    }
                )
            if tool_call_count >= self.MAX_TOOL_CALLS:
                break

            response = self.llm.generate(self.model,self.agent_messages,self.tools)
        self.agent_messages.append(
            response["raw_message"]
        )
        return response.get("message_content")

            


       
 
agent = Agent(model="qwen/qwen-2.5-72b-instruct",
              api_key=os.getenv("OPENROUTER_API_KEY"),
              provider="openrouter",
              tools=[Tool(add),Tool(read_file),Tool(create_dir)
                
              ],)
while True:
    data = agent.invoke({
                    "role":"user",
                    "content":input("prabhakar@ai---->")
        })

    print(data)
              

