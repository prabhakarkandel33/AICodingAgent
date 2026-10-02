from dataclasses import dataclass
from typing import TypedDict,Any
from collections.abc import Callable




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



