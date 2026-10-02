import json
import requests
import os

def add(a:int,b:int):
    """
    Add two integers
    """
    return a+b
       
def search_gutenberg_books(search_terms:list):
    """
        Search items from gutenberg library
    """

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
    """
        Read a file by providing a path
    """
    try:
        with open(path,"r") as file:
            return file.read()
    except Exception as e:
        return f"{e}"


def write_file(path:str,content:str):
    """
        Write contents to a file.
    """
    try:
        with open(path,"w") as file:
            file.write(content)
            return f"Created file {path}"
    except Exception as e:
        return f"{e}"


def create_dir(name:str):
    """Create a directory"""
    os.mkdir(name)
    return "Success"

def list_dir(path:str):
    """List contents of the current directory"""
    return os.listdir(path)

def chdir(path:str):
    """Change Working directory"""
    os.chdir(path)
    return "Success"
   
def rmdir(path:str):
    """Remove a directory by providing a path"""
    try:
        os.rmdir(path)
        return "Successfully deleted folder"
    except Exception as e:
        return f"Error:{e}"

def delete_file(path:str):
    """Delete a file"""
    try:
        os.remove(path)
        return "Successfully delete file"
    except Exception as e:
        return f"Error: {e}"

def get_request(url:str):
    """Perform a get request on a web site"""
    try:
        data = requests.get(url)
        return data.text
    except Exception as e:
        return f"{e}"
