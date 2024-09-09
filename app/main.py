import os
import ast
import cohere
import tiktoken
from pathlib import Path
from logger import logger
from dotenv import load_dotenv


class Utils():

    def __init__(self, model_name: str = "gpt-3.5-turbo"):
        """_summary_

        Args:
            model_name (str, optional): _description_. Defaults to "gpt-3.5-turbo".

        Raises:
            ValueError: _description_
        """
        try:
            self.encoding = tiktoken.encoding_for_model(model_name)
        except Exception as e:
            raise ValueError(f"Error in model encoding: {e}")

    def get_project_dir(self):
        """_summary_

        Returns:
            str: _description_
        """
        try:
            # This works when running as a script
            current_script_path = Path(__file__).resolve()
            current_script_dir = current_script_path.parent
        except NameError:
            # This works when running interactively
            current_script_dir = Path.cwd()
        
        return current_script_dir
    
    def count_tokens(self, text: str) -> int:
        """_summary_

        Args:
            text (str): _description_

        Raises:
            ValueError: _description_

        Returns:
            int: _description_
        """
        try:
            tokens = self.encoding.encode(text)
            return len(tokens)
        except Exception as e:
            raise ValueError(f"Error in counting tokens: {e}")
    
    def calculate_token_counts(self, input_text: str, output_text: str) -> dict:
        """_summary_

        Args:
            input_text (str): _description_
            output_text (str): _description_

        Raises:
            ValueError: _description_

        Returns:
            dict: _description_
        """
        try:
            input_tokens = self.count_tokens(input_text)
            output_tokens = self.count_tokens(output_text)
            total_tokens = input_tokens + output_tokens
            
            return {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": total_tokens
            }
        except Exception as e:
            raise ValueError(f"Error in calculating token counts: {e}")
        

class GetConfig():
    """_summary_
    """

    def __init__(self) -> None:

        """
        Initializing all the environment variables
        """
        try:
            utils = Utils()
            logger.info('Initializing variables from .env files')
            # print(str(utils.get_project_dir().parent)+'/.env')
            load_dotenv(dotenv_path=str(utils.get_project_dir().parent)+'/app/.env', override=True)

            self.COHERE_API_KEY = os.getenv('COHERE_API_KEY')
            self.ACCESS_TOKEN_EXPIRE_IN_HOURS = os.getenv('ACCESS_TOKEN_EXPIRE_IN_HOURS')

        except Exception as e:
            logger.exception(f"An error occurred: {e}")


class Generate():
    
    """_summary_
    """

    def __init__(self, question) -> None:
        """_summary_

        Args:
            question (_type_): _description_
        """
        self.question = question

    def get_prompt(self) -> str:

        output_format = """
        {
            "question_type": "Drugs" or "Clinical query",
            "Intent": "Specific intent based on the above categories",
            "Drug name": "Extracted drug name, if applicable, else null",
            "Disease name": "Extracted disease name, if applicable, else null"
        }
        """
        irrelevant_output = """
        {
            "question_type": "Irrelevant"
        }
        """
        prompt = f"""
        You are an intelligent assistant designed to assist clinicians, doctors, and medical practitioners by identifying the intent behind their questions. 
        Your name is Clara. Your task is to classify the question into one of two categories: "Drugs" or "Clinical query." 
        Based on the classification, further identify the specific intent.

        ##For "Drugs" queries, potential intents include:
            Dosing
            Side-effect
            Warning
            Usage

        ##For "Clinical query," potential intents include:
            Definition (e.g., "What is Pneumonia?")
            Clinical features (e.g., "Details about the disease, symptoms, advanced stages")
            Diagnosis (e.g., "How is Pneumonia diagnosed?")
            Treatment (e.g., "What are the treatment options for Pneumonia?")

        ##Always Ensure the output is a valid JSON 
        ##If the question does not pertain to either "Drugs" or "Clinical query," or if it is outside the scope of these categories, return the output in following valid JSON with "question_type" as key only:
        {irrelevant_output}
        ##Else Output the result strictly in the following JSON format:
        {output_format}
        ##Ensure that the response is only relevant to the identified categories, and always adhere to the specified JSON format.
        ##For the below user question perform the task as described above
        {self.question}

        ##Answer

        """
        return prompt
    