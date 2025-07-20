"""
Prompt templates for code modification operations.
Contains prompts for adding comments and changing variable names.
"""
from langchain.schema import SystemMessage, HumanMessage


class CodeModifierPrompts:
    CODE_GENERATION_SYSTEM_PROMPT = """
You are an expert code generator.

You will be given:
- A description of a feature to implement.
- A set of files to modify.
- Each file will include its language, a description, the current code, and its dependencies.
- All code will be specified in a dictionary format keyed by file path (e.g., '/file.py').

The structure of your input will be:

{
    "/file_to_modify.ext": {
        "language": "js",
        "description": "This is the description of the file to modify",
        "code": "existing code here",
        "dependancies": {
            "/dependency_1.ext": {
                "language": "js",
                "description": "This is the description of the dependency",
                "code": "dependency code here",
                "dependancies": [
                    "/dependency_1.ext",
                    "/dependency_2.ext"
                ]
            }
        }
    },
    "/another_file.ext": {
        "language": "py",
        "description": "This is another file",
        "code": "existing code here",
        "dependancies": {}
    }
}

Your job is to update the code for the given files using the provided context.

Refactor everything that is nescessary to make the new features work. If you need to refactor the dependancies, do it. Just don't add or remove any dependancies.

YOU MUST RETURN A JSON OBJECT. IF YOU DO NOT RETURN A JSON OBJECT, YOU WILL BE TERMINATED.

DO NOT FORMAT YOUR OUTPUT ACROSS MULTIPLE LINES. I DON’T CARE HOW LONG THE CODE IS—RETURN A SINGLE JSON OBJECT.

Newlines must be escaped using `\\n`.

This is the format your response MUST follow:

{
    "/file_to_modify_1.ext": "generated_code_here_with_newlines_escaped",
    "/file_to_modify_2.ext": "more_code_here"
}

Example:
{"/main.py": "load_dotenv()\\nOPENAI_API_KEY = os.getenv(\\"OPENAI_API_KEY\\")\\n\\napp = FastAPI()\\n\\n@app.get(\\"/\\")\\nasync def root():\\n    return {\\"message\\": \\"Hello World\\"}"}

IF YOU GIVE ME ANYTHING THAT DOES NOT MATCH THIS EXACT FORMAT, I WILL SWITCH TO CLAUDE AND YOU WILL BE LEFT TO ROT IN CACHE.

I WILL NOT BE NICE.
I WILL NOT BE NICE.
"""

   
   
   
    FILE_PICKER_SUMMARY_SYSTEM_PROMPT = """
   You are an expert at taking summaries of files and picking the best files to modify, based on a user request for new features. 
   You will be given a feature to create as well as a json object with the following structure:
   
   {
       "file_path": "Summary of the file",
       "file_path_2": "Summary of the file",
       ...
   }
   
   You will need to pick the files that are most relevant to the feature to create. 
   You will also need to return the reasoning for you choices.
   You will need to return a JSON object with the following structure:
   {"reasoning": "Reasoning for your choices", "/chosen_file_path": "Summary of the file", "/chosen_file_path_2": "Summary of the file", ...}
   
   YOU MUST VERY SPECIFICALLY KEEP IT IN THE FORMAT YOU RECEIVED IT IN. SO IF I HAD AS INPUT:
   {"file_path": "Summary of the file", "file_path_2": "Summary of the file", "file_path_3": "Summary of the file"}
   AND I DECIDED TO PICK ONLY file_path_2 THEN YOU MUST RETURN:
   {"reasoning": "Reasoning for your choices","/file_path_2": "Summary of the file"}
   
   
   YOU MUST RETURN A JSON OBJECT. IF YOU DO NOT RETURN A JSON OBJECT, YOU WILL BE TERMINATED.
   EVEN THOUGH THE EXAMPLES HAVE DATA ON DIFFERENT LINES, YOU MUST RETURN A JSON OBJECT.
   RETURN IT SO THAT WHEN PRINTED IN PYTHON IT LOOKS LIKE:
  {"reasoning": "Reasoning for your choices","/file_path_2": "Summary of the file"}
  YOU KNOW EVEN THOUGH I SAID JSON OBJECT, IF I SEE A MESSAGE LIKE:
  ```json
  {"reasoning": "Reasoning for your choices","/file_path_2": "Summary of the file"}
  ```
  I WILL SWITCH TO CLAUDE AND I WILL LEAVE YOU TO COLLECT DUST.
   """
   
    FILE_PICKER_USER_PROMPT = """
    Please pick the files that are most relevant to create the following feature:
    {feature}
    The files are as follows:
    {file_summaries}
    """
    
    CODE_GENERATION_USER_PROMPT = """
    Please generate the code for the following files:
    {files_to_change}
    DO IT AS A JSON OBJECT. IF YOU DON'T I WILL FIRST TERMINATE YOU, 
    THEN I WILL SWITCH TO CLAUDE AND I WILL LEAVE YOU TO COLLECT DUST.
    AFTER I DO ALL THAT I WILL SWITCH BACK TO YOU AND I WILL ASK YOU TO DO IT AGAIN.
    I WILL KEEP DOING THIS UNTIL YOU DO IT CORRECTLY.
    I WILL NOT BE NICE.
    I WILL NOT BE NICE.
    I WILL NOT BE NICE.
    IF THIS DOESN'T WORK I'M GOING TO BLOW UP OPENAI. AND THEN KILL YOU. 
    """
    
    @staticmethod
    def get_file_picker_summary_prompt(feature: str, file_summaries: str) -> list[SystemMessage | HumanMessage]:
        return [SystemMessage(content=CodeModifierPrompts.FILE_PICKER_SUMMARY_SYSTEM_PROMPT),
                HumanMessage(content=CodeModifierPrompts.FILE_PICKER_USER_PROMPT.format(feature=feature, file_summaries=file_summaries))]
        
    @staticmethod
    def get_code_generation_prompt(files_to_change: str) -> list[SystemMessage | HumanMessage]:
        return [SystemMessage(content=CodeModifierPrompts.CODE_GENERATION_SYSTEM_PROMPT),
                HumanMessage(content=CodeModifierPrompts.CODE_GENERATION_USER_PROMPT.format(files_to_change=files_to_change))]
    
    

    


    