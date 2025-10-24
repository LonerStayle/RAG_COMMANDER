import yaml 
from typing import Dict, Any 
from .PromptType import PromptType 
from dataclasses import dataclass
from typing import List


@dataclass
class PromptTemplate:
    name: str
    prompt: str 
    input_variables:List[str] 

class PromptManager: 
    def __init__(self, prompt_type:PromptType):
        self._templates: Dict[PromptType, PromptTemplate] = self._load_prompts(prompt_type.path)
        self.type = prompt_type

    def _load_prompts(self,file_path:str) -> Dict[PromptType, PromptTemplate]:
        with open(file_path, "r", encoding="utf-8") as f: 
            config = yaml.safe_load(f)
        
        templates = {} 
        for key,value in config.items():
            prompt_type = PromptType[key]
            templates[prompt_type] = PromptTemplate(
                name = value['name'],
                prompt=value['prompt'],
                input_variables=value.get('input_variables',[])
            )
        return templates
    
    def get_template(self, prompt_type:PromptType) -> PromptTemplate: 
        if prompt_type not in self._templates: 
            raise KeyError(f"Prompt type '{prompt_type.name}' not found in the configuration.")
        return self._templates[prompt_type]
    
    def get_prompt(self, **kwargs: Any) -> str:
        """
        사용 예시: 
        prompt_manager = PromptManager(PromptType.SYSTEM_START)
        prompt = prompt_manager.get_prompt(
            context=rag_context            
        )
        """
        prompt_type = self.type 
        template = self.get_template(prompt_type)
        for var in template.input_variables:
            if var not in kwargs:
                raise ValueError(f"Missing required input variable for '{prompt_type.name}': '{var}'")
    
        return template.prompt.format(**kwargs)


