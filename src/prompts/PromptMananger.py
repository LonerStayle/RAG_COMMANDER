import yaml 
from typing import Dict, Any 
from .PromptType import PromptType 
from dataclasses import dataclass
from typing import List


@dataclass
class SystemPromptTemplate:
    name: str
    system_prompt: str 
    input_variables:List[str] 

class PromptManager: 
    def __init__(self, prompt_type:PromptType):
        self._templates: Dict[PromptType, SystemPromptTemplate] = self._load_prompts(prompt_type.path)
        self.type = prompt_type

    def _load_prompts(self,file_path:str) -> Dict[PromptType, SystemPromptTemplate]:
        with open(file_path, "r", encoding="utf-8") as f: 
            config = yaml.safe_load(f)
        
        templates = {} 
        for key,value in config.items():
            prompt_type = PromptType[key]
            templates[prompt_type] = SystemPromptTemplate(
                name = value['name'],
                system_prompt=value['system_prompt'],
                input_variables=value.get('input_variables',[])
            )
        return templates
    
    def get_template(self, prompt_type:PromptType) -> SystemPromptTemplate: 
        if prompt_type not in self._templates: 
            raise KeyError(f"Prompt type '{prompt_type.name}' not found in the configuration.")
        return self._templates[prompt_type]
    
    def get_prompt(self, prompt_type: PromptType, **kwargs: Any) -> str:
        template = self.get_template(prompt_type)
        for var in template.input_variables:
            if var not in kwargs:
                raise ValueError(f"Missing required input variable for '{prompt_type.name}': '{var}'")
    
        return template.system_prompt.format(**kwargs)


