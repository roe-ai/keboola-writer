import logging
from pydantic import BaseModel, Field, ValidationError
from keboola.component.exceptions import UserException


class Configuration(BaseModel):
    api_token: str = Field(alias="#api_token")
    table_name: str = Field()
    debug: bool = False

    def __init__(self, **data):
        try:
            super().__init__(**data)
        except ValidationError as e:
            error_messages = [f"{err['loc'][0]}: {err['msg']}" for err in e.errors()]
            raise UserException(f"Validation Error: {', '.join(error_messages)}")

        if self.debug:
            logging.debug("Component will run in Debug mode")

    # @field_validator('api_token')
    # def token_must_be_uppercase(cls, v):
    #     if not v.isupper():
    #         raise UserException('API token must be uppercase')
    #     return v
