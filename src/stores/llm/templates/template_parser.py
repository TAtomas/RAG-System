import os

class TemplateParser:
    def __init__(self ,language:str ,default_language:str ="en"):
        self.default_language=default_language
        self.currant_path=os.path.dirname(os.path.abspath(__file__))
        self.language=None

        self.set_language(language)

    def set_language(self,language:str):
        if not language:
            self.language=self.default_language

        language_path=os.path.join(self.currant_path,"locales",language)
        if os.path.exists(language_path):
            self.language=language
        else:
            self.language=self.default_language


    def get(self , group:str ,keys:str ,vars:dict={}):
        if not group or not keys:
            return None
        group_path=os.path.join(self.currant_path,"locales",self.language,f"{group}.py")
        targeted_language=self.language
        if not os.path.exists(group_path):
            group_path=os.path.join(self.currant_path,"locales",self.default_language,f"{group}.py")
            targeted_language=self.default_language
        if not os.path.exists(group_path):
            return None


        modules= __import__(f"stores.llm.templates.locales.{targeted_language}.{group}",fromlist=[group])

        if not modules :
            return None

        key_attribute=getattr(modules,keys)
        return key_attribute.substitute(vars)