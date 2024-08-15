from typing import Any, List, Type
import openai
import logging
from dotenv import load_dotenv
import json
from pydantic import BaseModel, Field, create_model

# Set up logging
logging.basicConfig(level=logging.ERROR)
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

    def to_dict(self):
        return {
            "name": self.name,
            "data_type": self.data_type,
            "description": self.description
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            name=data["name"], 
            description=data["description"], 
            data_type=data["data_type"]
        )
    
class SchemaFieldResults(BaseModel):
    name: str
    description: str
    data_type: str
    value: str | None = Field(default=None, exclude=True)

    def to_dict(self):
        return {
            "name": self.name,
            "data_type": self.data_type,
            "description": self.description
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            name=data["name"], 
            description=data["description"], 
            data_type=data["data_type"]
        )
    
class ResponseSchema(BaseModel):
    data_fields: List[SchemaField]
    confirmation_message: str

    def to_dict(self):
        return {
            "data_fields": [field.to_dict() for field in self.data_fields],
            "confirmation_message": self.confirmation_message
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            data_fields=[SchemaField.from_dict(field_data) for field_data in data["data_fields"]],
            confirmation_message=data["confirmation_message"]
        )
    
class ResponseSchemaResults(BaseModel):
    data_fields: List[SchemaFieldResults]
    confirmation_message: str

    def to_dict(self):
        return {
            "data_fields": [field.to_dict() for field in self.data_fields],
            "confirmation_message": self.confirmation_message
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            data_fields=[SchemaField.from_dict(field_data) for field_data in data["data_fields"]],
            confirmation_message=data["confirmation_message"]
        )

class LLMHelper:
    def __init__(self):
        try:
            self.client = openai.OpenAI()
            self.model = "gpt-4o-mini"
        except Exception as e:
            logger.error(f"Error initializing OpenAI client: {str(e)}")
            raise

    def chat_completion(self, messages, temperature=0.2, response_format=None, response_format_json=None):
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
            if response_format is not None:
                logger.info("Running OpenAI Query with response format")
                response = self.client.beta.chat.completions.parse(
                    **kwargs,
                    response_format=response_format
                )
            elif response_format_json is not None:
                logger.info("Running OpenAI Query with response format json")
                response = self.client.chat.completions.create(**kwargs, response_format=response_format_json)
            else:
                logger.debug("Running OpenAI Query")
                response = self.client.chat.completions.create(**kwargs)

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

    def create_dynamic_model(self, schema: ResponseSchema) -> dict:
        properties = {}
        required_fields = []

        for data_field in schema.data_fields:
            properties[data_field.name] = {"type": data_field.data_type.lower()}
            required_fields.append(data_field.name)

        response_format_json = {
            "type": "json_schema",
            "json_schema": {
                "name": "schema_response",
                "schema": {
                    "type": "object",
                    "properties": {
                        "data_fields": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": properties,
                                "required": required_fields,
                                "additionalProperties": False
                            }
                        }
                    },
                    "required": ["data_fields"],
                    "additionalProperties": False
                },
                "strict": True
            }
        }

        return response_format_json

    def run_schema(self, prompt: str, file_contents: str, schema: str) -> List[ResponseSchemaResults]:
        try:
            messages = [
                {"role": "system", "content": f"You are an AI assistant that extracts structured data from text. Your goal is {prompt}. Please return a list of extracted data items."},
                {"role": "user", "content": f"Extract for this input:\n\n{file_contents}"}
            ]

            extraction_response = self.chat_completion(
                messages=messages,
                response_format_json=self.create_dynamic_model(schema)
            )

            if extraction_response.choices[0].message.refusal:
                raise Exception(extraction_response.choices[0].message.refusal)

            parsed_items = json.loads(extraction_response.choices[0].message.content)

            # Convert the parsed items to ResponseSchemaResults objects
            return [
                ResponseSchemaResults(
                    data_fields=[
                        SchemaFieldResults(
                            name=field.name,
                            description=field.description,
                            data_type=field.data_type,
                            value=str(item.get(field.name, ''))
                        )
                        for field in schema.data_fields
                    ],
                    confirmation_message=schema.confirmation_message
                )
                for item in parsed_items['data_fields']
            ]

        except Exception as e:
            logger.error(f"Error generating example: {str(e)}")
            raise
