from abc import ABC,abstractmethod
from core_types import *

class LLMInterface(ABC):

    @abstractmethod
    def generate(self,model,messages,tools) -> LLMResponse:
        """
            Every lllm interface ought to inherit this functionality 
            a standard interface for deepseek,openrouter,whatever provider we decide to add on later
        """
        pass
