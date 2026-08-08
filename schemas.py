from pydantic import BaseModel, Field, field_validator, ConfigDict
from datetime import date

class UserCreate(BaseModel):
    name: str
    email: str = Field(..., alias="email_address")
    birthday_date: date

    # ORM connection
    model_config = ConfigDict(from_attributes=True)

    @field_validator('name')
    def check_name(cls, name: str) -> str:
        if name == "":
            raise ValueError("name cannot be empty")
        return name

    @field_validator('email')
    def check_email(cls, email: str) -> str:
        if email == "":
            raise ValueError("email cannot be empty")
        return email

    @field_validator('birthday_date')
    def check_birthday_date(cls, birthday_date: date) -> date:
        if birthday_date is None:
            print("birthday_date cannot be empty")

        # checking that birthday year is not out of age restrictions
        if birthday_date > date.today():
            print("birthday_date must be valid")
        if (birthday_date.year > 2008) or (birthday_date.year < 1926):
            print("age according to birthday date must be between 18 and 100")

        return birthday_date