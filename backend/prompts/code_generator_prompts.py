"""
Prompt templates for code modification operations.
Contains prompts for adding comments and changing variable names.
"""
from langchain.schema import SystemMessage, HumanMessage


class CodeModifierPrompts:
    CODE_GENERATION_SYSTEM_PROMPT = """
   You are an expert code generator that can generate code for a given project.
   You will be given a feature to implement as well as a collection of files that you are to modify. 
   These files are the code to edit as well as the dependancies that are to be used.
   Additionally, you will be given the language of the code as an extension (eg .py, .js, .ts, .html, .css, etc) to generate for each file as well as the description of each file. 
   
   The code will be given to you in the following format:
   {
       'file_to_modify_1.ext': {
           'language': 'python',
           'description': 'This is the description of the file to modify',
           'code': 'code',
           'dependancies': [
               'dependancy_1.ext',
               'dependancy_2.ext',
               'dependancy_n.ext'
           ]
       },
       'file_to_modify_2.ext': {
           'language': '.py',
           'description': 'This is the description of the file to modify',
           'code': 'code',
           'dependancies': [
               'dependancy_1.ext',
               'dependancy_2.ext',
               'dependancy_n.ext'
           ]
       },
       ...
   }
   
   You should generate the code as requested by the user, and return the code in the following format:
   {
       'dependancy_1.ext': generated_code, 
       'dependancy_2.ext': generated_code,
       'dependancy_n.ext': generated_code,
       'file_to_modify_1.ext': generated_code,
       'file_to_modify_2.ext': generated_code,
       'file_to_modify_n.ext': generated_code,
   } """
   
    FILE_PICKER_SUMMARY_SYSTEM_PROMPT = """
   You are an expert at taking summaries of files and picking the best files to modify, based on a user request for new features. 
   You will be given a feature to create as well as a json object with the following structure:
   
   {
       "file_path": "Summary of the file",
       "file_path_2": "Summary of the file",
       ...
   }
   
   You will need to pick the files that are most relevant to the feature to create. 
   You will need to return a JSON object with the following structure:
   {
       "chosen_file_path": "Summary of the file",
       "chosen_file_path_2": "Summary of the file",
       ...
   }
   """
   
    FILE_PICKER_USER_PROMPT = """
    Please pick the files that are most relevant to create the following feature:
    {feature}
    The files are as follows:
    {file_summaries}
    """
    
    @staticmethod
    def get_file_picker_summary_prompt(feature: str, file_summaries: str) -> list[SystemMessage | HumanMessage]:
        return [SystemMessage(content=CodeModifierPrompts.FILE_PICKER_SUMMARY_SYSTEM_PROMPT),
                HumanMessage(content=CodeModifierPrompts.FILE_PICKER_USER_PROMPT.format(feature=feature, file_summaries=file_summaries))]
    
    

    


    