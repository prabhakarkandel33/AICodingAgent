from tool_registry import *
from core_types import *
from OpenRouterInterface import *
from AnthropicInterface import *
from typing import List
import json

import os
from dotenv import load_dotenv
from assets import COMPACTION_PROMPT


load_dotenv()


class Agent:
    def __init__(
        self,
        model:str,
        api_key:str,
        tools:List[Tool],
        provider:str,
        MAX_TOOL_CALLS:int=10,
        SYSTEM_PROMPT:str="You are a helpful AI assistant use your tool registry whenever applicable and on tool calls just one shot the thing",
        agent_truncation_limit:int=50000,
        compaction_window:int=10
    ):
        self.model = model
        self.tools = tools
        
        self.provider = provider


        #in future can expand this
        if (self.provider == "openrouter"):
            self.llm = OpenRouterInterface(api_key)
        elif (self.provider == "anthropic"):
            self.llm = AnthropicInterface(api_key)
        else:
            self.llm = None
        self.agent_messages = []
        self.system_prompt = SYSTEM_PROMPT
        self.MAX_TOOL_CALLS=MAX_TOOL_CALLS
        self.agent_truncation_limit = agent_truncation_limit
        self.compaction_window=compaction_window

    def compact(self):
        """
         if (len(str(cleaned_message)) > chr_budget) or (compaction==True):
            
            cleaned_message.append(
                {
                    "role":"user",
                    "content":COMPACTION_PROMPT,
                }
            )

            
            response = self.generate(
                model,
                SYSTEM_PROMPT,
                cleaned_message)
            compacted_msg = response.get("message_content")

            cleaned_message = []
            cleaned_message.append(response["raw_message"])

        """
        if (len(self.agent_messages) <= self.compaction_window):
            return

        old = self.agent_messages[:-self.compaction_window]
        recent = self.agent_messages[-self.compaction_window:]

        self.agent_messages = old

        self.agent_messages.append(
                {
                    "role":"user",
                    "content":COMPACTION_PROMPT,
                }
        )
        response = self.llm.generate(self.model,
                                     self.system_prompt,
                                     self.agent_messages,
                                     tools = []
                                     ) 

        self.agent_messages = [response["raw_message"]] + recent
        print(response["message_content"])

                                     
        

    def invoke(self,messages:Dict):
        compaction = (messages["content"] == "/compact")

        
    
        self.agent_messages.append(messages)


        context_response = self.llm.build_context(
            messages = self.agent_messages
        )
        
        self.agent_messages = context_response["cleaned_message"]

        if (context_response["compaction_required"]) or compaction:
            if (len(self.agent_messages) >= self.compaction_window):
                print("*"*40+"Compaction"+"*"*40)

                self.compact()
            else:
                print("Within window limit, no need for compaction")
                print("*"*40)
                return
    
        response = self.llm.stream_response(self.model,
                                     self.system_prompt,
                                    self.agent_messages,
                                    self.tools
        )
        tool_call_count = 0
            
        
        while response.get('tool_called') and response.get('tool_calls'):
            #print("tool called by anthropic")
            self.agent_messages.append(
response['raw_message']
            )
            for tool_call in response['tool_calls']:

                if(tool_call_count >= self.MAX_TOOL_CALLS):
                    break
                tool_call_count += 1

            
    
                parsed_tool = parse_tool_calls(tool_call)
                if isinstance(parsed_tool,ParseError):
                    tool_resp = self.llm.harness_tool_parse(
                            tool_call["call_id"],name=tool_call['name'],
                            content=f"Tool Call error: {parsed_tool.raw} Reason: {parsed_tool.reason}")
 
                    self.agent_messages.append(
                        tool_resp
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
                                                
                        tool_response = json.dumps(tool_response)

                        #truncation for tool calls
                        MAX = self.agent_truncation_limit
                        if (len(tool_response) > MAX):
                            tool_response = tool_response[:MAX//2] + f"\n<Truncated {len(tool_response) - MAX} characters>" + tool_response[-MAX//2:]
                        content = tool_response

                    else:
                        content = "\n".join(validation_errors)
                
                tool_resp = self.llm.harness_tool_parse(
                        tool_id=tool_call["call_id"],
                        name=tool_call["name"],
                        content=content
                )
                self.agent_messages.append(
                    tool_resp
                )
            if tool_call_count >= self.MAX_TOOL_CALLS:
                break

            response = self.llm.generate(self.model,self.system_prompt,self.agent_messages,self.tools)
        self.agent_messages.append(
            response["raw_message"]
        )
        return response.get("message_content")

            


"""
        claude-haiku-4-5-20251001
        qwen/qwen-2.5-72b-instruct
"""
 
agent = Agent(model="qwen/qwen-2.5-72b-instruct",
              api_key=os.getenv("OPENROUTER_API_KEY"),
              provider="openrouter",
              tools=[Tool(add),
                     Tool(read_file),
                     Tool(create_dir),
                     Tool(write_file),
                     Tool(get_request),
                     Tool(list_dir),
                     Tool(chdir),
                     Tool(rmdir),
                     
                
              ],)
while True:
    data = agent.invoke({
                    "role":"user",
                    "content":input("prabhakar@ai---->")
        })
    print("\n")
    print(data) if data else ""


