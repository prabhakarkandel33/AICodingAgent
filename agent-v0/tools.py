"""
#LLM format
tools = [ 
        {          
    "type": "function",
      "function": {
        "name": "search_gutenberg_books",
        "description": "Search for books in the Project Gutenberg library",
        "parameters": {
          "type": "object",
          "properties": {
            "search_terms": {
              "type": "array",
              "items": {"type": "string"},
              "description": "List of search terms to find books"
            }
          },
          "required": ["search_terms"]
        }
      }
        }
]

#my format
separately through function definition,

name -> xxy
parameters -> [{"par_name":{"type":"x","description":"..."}}]

"""
import inspect
import json
import requests
import os

class Tool:
    def __init__(self,func,description):
        self.func=func
        self.name=func.__name__
        self.description = description

    def schema(self):
        """
            Convert tool object initialization to llm tool schema"""
        properties = {}
        required = []

        signature = inspect.signature(self.func)

        for name,parameter in signature.parameters.items():
            annotation = parameter.annotation

            if annotation is str:
                properties[name] = {"type":"string"}
            elif annotation is int:
                properties[name] = {"type":"number"}
            elif annotation is float: 
                properties[name] = {"type":"float"}
            elif annotation is list:
                properties[name] = {"type":"array"}
            else:
                properties[name] = {"type":"string"}

            if parameter.default is inspect.Parameter.empty:
                required.append(name)

        return {
            "type":"function",
            "function":{
                "name":self.name,
                "description":self.description,
                "parameters":{
                    "type":"object",
                    "properties":properties,
                    "required":required
                }
            }
        }
    def call(self,arguments):
        return self.func(**arguments)

    
        
def search_gutenberg_books(search_terms:list):
    search_query = " ".join(search_terms)
    url = "https://gutendex.com/books"
    response = requests.get(url,params={"search":search_query})

    simplified_results = []

    for book in response.json().get("results",[]):
        simplified_results.append({
            "id":book.get("id"),
            "title":book.get("title"),
            "authors":book.get("authors")
        })
    return simplified_results

def read_file(path:str):
    try:
        with open(path,"r") as file:
            return file.read()
    except Exception as e:
        return f"{e}"


def write_file(path:str,content:str):
    try:
        with open(path,"w") as file:
            file.write(content)
            return f"Created file {path}"
    except Exception as e:
        return f"{e}"


def create_dir(name:str):
    os.mkdir(name)
    return "Success"

def list_dir(path:str):
    return os.listdir(path)

def chdir(path:str):
    os.chdir(path)
    return "Success"
   
def rmdir(path:str):
    try:
        os.rmdir(path)
        return "Successfully deleted folder"
    except Exception as e:
        return f"Error:{e}"

def delete_file(path:str):
    try:
        os.remove(path)
        return "Successfully delete file"
    except Exception as e:
        return f"Error: {e}"

def get_request(url:str):
    try:
        data = requests.get(url)
        return data.text
    except Exception as e:
        return f"{e}"




