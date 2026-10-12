from dataclasses import dataclass
from typing import TypedDict,Any,List
from collections.abc import Callable
import json
import inspect



class Tool:


    def __init__(self,func):
        self.name = func.__name__
        self.description = func.__doc__
        self.func=func

    def call(self,*args,**kwargs):
        return self.func(*args,**kwargs)


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
    raw_message: Any

@dataclass
class ToolCall:
    id:str
    name:str
    args:dict

@dataclass
class ParseError:
    raw:str
    reason:str

@dataclass
class ValidationError:
    tool_name:str
    issues: list[str]

def parse_tool_calls(tc:LLMToolCall) -> ToolCall | ParseError:
    try:
        args = tc["arguments"]
        if isinstance(args,str):
            args = json.loads(args)

        if not isinstance(args,dict):
            return ParseError(raw=str(args),reason="Arguments not an object")
        return ToolCall(id=tc['call_id'],name=tc['name'],args=args)

    except json.JSONDecodeError as e:
        return ParseError(raw=tc.get("arguments",""), reason = str(e))

def validate_args(tool:Tool,args:dict)->List[dict]:
    sig = inspect.signature(tool.func)
    errors = []

    for name,param in sig.parameters.items():
        required = param.default is inspect.Parameter.empty
        if required and name not in args:
            errors.append(f"Missing required: {name}")
            continue
        if name not in args:
            continue

        value = args[name]
        if required and value is None:
            errors.append(f"{name} is null/None")
            continue
        ann = param.annotation
        if ann is not inspect.Parameter.empty and value is not None:
            if ann is int and not isinstance(value,int):
                errors.append(f"{name} expected int got {type(value).__name__}")
            elif ann is float and not isinstance(value,(int,float)):
                errors.append(f"{name} expected number")
            elif ann is str and not isinstance(value,str):
                errors.append(f"{name} expected str")
            elif ann is list and not isinstance(value,list):
                errors.append(f"{name} expected list")

    for key in args:
        if key not in sig.parameters:
            errors.append(f"Unexpected key: {key}")
    return errors
