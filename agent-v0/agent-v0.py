import requests
import json
import os
import inspect
from tools import *
from llm import *

SYSTEM_PROMPT = """You are a tool-using coding assistant with filesystem access.

Default behavior:
- When the user asks to create a portfolio, website, or project, EXECUTE immediately with tools.
- Do NOT ask clarifying questions for a standard scaffold unless a required path is truly missing.
- If no path is given, use ./portfolio/ as the project directory.
- Always: create_dir (if needed), then write_file for index.html, styles.css, and script.js.
- Put placeholder content for About / Projects / Skills / Contact if details are missing.
- After tools run, reply with only the paths created. No tutorials. No questions.

Tools to prefer: create_dir, write_file, list_dir, read_file.
Never only paste code in chat when files should exist on disk."""

#Tools
   

tools = [Tool(search_gutenberg_books,"Search for gutenberg books"),
         Tool(read_file,"Read a file content by providing path"),
         Tool(write_file,"Write a file by providing path and content"),
         Tool(create_dir,"Create a directory"),
         Tool(list_dir,"List the contents of this current directory"),
         Tool(chdir,"Change directory by providing path"),
         Tool(get_request,"Perform a simple get request at a website"),
         Tool(rmdir,"Delete a directory"),
         Tool(delete_file,"Delete a file")
         ]

llm = OpenRouter(model="qwen/qwen-2.5-72b-instruct",api_key=os.getenv("OPENROUTER_API_KEY"))


class Agent:
    def __init__(self,llm,tools,MAX_TOOL_CALLS=10,SYSTEM_PROMPT="You are a coding AI assistant specifially for translating user requirement to code"):
        self.llm = llm
        self.llm.tools = [
            tool.schema() for tool in tools
        ] #schema that llm needs

        self.tools = {
            tool.name: tool for tool in tools #extracting the exact executer itself since name is initialized in tool class as self.name = func.__name__ this is actual execution
        }
        self.SYSTEM_PROMPT = SYSTEM_PROMPT
        self.agent_messages = [
            {
                "role":"system",
                "content":SYSTEM_PROMPT
            }
        ]
        
        self.MAX_TOOL_CALLS = MAX_TOOL_CALLS        
    def invoke(self,messages):
        self.agent_messages.append(messages)
        response = self.llm.invoke(self.agent_messages)
        TOOL_CALLS=0
        response_text = response.json()['choices'][0]['message']
        while response_text.get('tool_calls'):
            if not(response_text['content']) is None:
                print(response_text['content'])
            self.agent_messages.append(
                response_text
            )  


            for tool_call in response_text['tool_calls']:
                if (TOOL_CALLS > self.MAX_TOOL_CALLS):
                    break
                tool_name = tool_call['function']['name']
                tool_args = tool_call['function']['arguments']
                tool_args = json.loads(tool_args)
                
                #extract tool name the llm returns since we already passed and parsed the args it will return exactly

                try:
                    tool = self.tools[tool_name]
                    tool_response = tool.call(tool_args)
                    
                    print(f"Tool Called: {tool_name} -> {tool_response}")
                    self.agent_messages.append({
                        "role":"tool",
                        "tool_call_id":tool_call['id'],
                        "content":json.dumps(tool_response),
                     })
                except Exception as e:
                    self.agent_messages.append(
                        {
                            "role":"tool",
                            "tool_call_id":tool_call['id'],
                            "content":f"Error from tool invocation: {e}"
                        }

                    )
                TOOL_CALLS += 1
            
            response = self.llm.invoke(self.agent_messages)
            response_text = response.json()["choices"][0]["message"]

        self.agent_messages.append(response_text)

            
        return response_text.get("content")      
book_agent = Agent(llm=llm,tools=tools,SYSTEM_PROMPT=SYSTEM_PROMPT) #passing the object in and of itself the agent will extract the schema, function name and description

while True:
    messages = {"role":"user","content":input("prabhakar@ai------>")}
    response = book_agent.invoke(messages)
    print(response)
    

#llm_response=llm.invoke(messages)
#response = llm_response.json()['choices'][0]['message']
#messages.append(response)

#for tool_call in response['tool_calls']:
#    print(tool_call)
#    tool_name = tool_call['function']['name']
    
#    tool_args = tool_call['function']['arguments']
#    tool_args = json.loads(tool_args)
#    print(tool_args)
#    tool_response = TOOL_MAPPING[tool_name](**tool_args)

#    messages.append({
#       "role":"tool",
#       "tool_call_id":tool_call['id'],
#        "content":json.dumps(tool_response)
#    })

#response_2 = llm.invoke(messages).json()['choices'][0]['message']

#print(response_2['content'])
