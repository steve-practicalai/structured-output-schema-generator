from typing import List
import openai
import logging
from dotenv import load_dotenv
import json
from pydantic import BaseModel

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
load_dotenv()

class ProjectSetupResponse(BaseModel):
    title: str
    description: str 
    prompt: str

class SchemaField(BaseModel):
    name: str
    description: str
    data_type: str

class ResponseSchema(BaseModel):
    data_fields: List[SchemaField]
    confirmation_message: str

class LLMHelper:
    def __init__(self):
        try:
            self.client = openai.OpenAI()
            self.model = "gpt-4o-mini"
            logger.info("OpenAI client initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing OpenAI client: {str(e)}")
            raise

    def chat_completion(self, messages, temperature=0.2, response_format=None):
        try:
            kwargs = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
            }

            try:
                logger.debug(f"OpenAI client request: {json.dumps(kwargs, indent=2)}")
            except TypeError:
                logger.error(f"OpenAI client request (non-serializable): {kwargs}")

            # Make the API call
            response = self.client.beta.chat.completions.parse(**kwargs, response_format=response_format)

            # Log the response
            try:
                logger.debug(f"OpenAI client response: {json.dumps(response.model_dump(), indent=2)}")
            except TypeError:
                logger.error(f"OpenAI client response (non-serializable): {response}")

            return response
        except Exception as e:
            logger.error(f"Error in chat completion: {str(e)}")
            raise

    def project_setup(self, goal) -> ProjectSetupResponse:
        try:
            messages = [
                {"role": "system", "content": "You are an AI assistant designed to take instructions on what information they wish to extract from a text file and return the Title, Description and Prompt for a given extraction goal."},
                {"role": "assistant", "content": "Example: 'Meeting action items' / Returns: Title: Extract meeting action items / Description: A list of action items that need to be completed by the next week. / Prompt: Extract meeting action items that need to be completed and by whom.'"},
                {"role": "user", "content": goal}
            ]

            project_setup_response = self.chat_completion(
                messages=messages,
                response_format=ProjectSetupResponse
            )
            if project_setup_response.choices[0].message.refusal:
                raise Exception(project_setup_response.choices[0].message.refusal)

            parsed_response = project_setup_response.choices[0].message.parsed
            return parsed_response 
        except Exception as e:
            logger.error(f"Error generating schema: {str(e)}")
            raise

    def extract_schema(self, file_contents, prompt) -> ResponseSchema:
        try:
            messages = [
                {"role": "system", "content": "You are an AI assistant designed to create JSON schemas for structured data extraction. Limit data types to String, Number, Boolean, and Enum. Do not use nested structures (Object or Array)."},
                {"role": "user", "content": f"Create a JSON schema for extracting the following information: {prompt}\n\nHere's an example of the input:\n\n{file_contents}"}
            ]

            extract_schema_response = self.chat_completion(
                messages=messages,
                response_format=ResponseSchema
            )
            if extract_schema_response.choices[0].message.refusal:
                raise Exception(extract_schema_response.choices[0].message.refusal)

            parsed_response = extract_schema_response.choices[0].message.parsed
            return parsed_response 
        except Exception as e:
            logger.error(f"Error generating schema: {str(e)}")
            raise

    def run_schema(self, prompt, file_contents, schema) -> ResponseSchema:
        try:
            messages = [
                {"role": "system", "content": f"You are an AI assistant that extracts structured data from text. Your goal is {prompt}"},
                {"role": "user", "content": f"Extract for this input:\n\n{file_contents}"}
            ]
                    
            run_schema_response = self.chat_completion(
                messages=messages,
                response_format=ResponseSchema
            )
            if run_schema_response.choices[0].message.refusal:
                raise Exception(run_schema_response.choices[0].message.refusal)

            parsed_response = run_schema_response.choices[0].message.parsed

            return parsed_response
        except Exception as e:
            logger.error(f"Error generating example: {str(e)}")
            raise
