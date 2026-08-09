from pydantic import BaseModel, Field, field_validator, ConfigDict
from datetime import date, datetime
import re

# This model is used to add user to database
class UserCreate(BaseModel):
    username: str = Field(..., min_length=1 , description="Name of user")
    email: str = Field(..., description="Email address of user")
    birthday_date: date

    # ORM connection
    model_config = ConfigDict(from_attributes=True)

    @field_validator('username')
    def check_name(cls, name: str) -> str:
        if not name.strip():
            raise ValueError("Name cannot be empty")
        return name.strip()

    @field_validator('email')
    def check_email(cls, email: str) -> str:
        if not email.strip():
            raise ValueError("Email cannot be empty")
        if not is_valid_email(email):
            raise ValueError("Invalid email")
        return email.strip()

    @field_validator('birthday_date')
    def check_birthday_date(cls, birthday_date: date) -> date:
        if birthday_date is None:
            raise ValueError("Birthday_date cannot be empty")

        age = calculate_age(birthday_date)

        # checking that birthday year is not out of age restrictions
        if age < 18:
            raise ValueError("You must be at least 18 years old")

        if age > 100:
            raise ValueError("Age cannot exceed 100 years.")

        return birthday_date

# This model is used in flask web server to register new user
class UserRegistration(BaseModel):
    username: str = Field(..., min_length=1 , description="Name of user")
    email: str = Field(..., description="Email address of user")
    birthday_date: date
    password: str = Field(..., min_length=6, description="Password of user")
    confirm_password: str = Field(..., description="Confirmation password of user")

    @field_validator('password')
    def validate_password(cls, value):
        if len(value) < 6:
            raise ValueError('Password must be at least 6 characters')
        return value

    @field_validator('confirm_password')
    def validate_confirmation_password(cls, value, info):
        if value != info.data.get('password'):
            raise ValueError('Confirmation password does not match')
        return value

    @field_validator('username')
    def check_name(cls, name: str) -> str:
        if not name.strip():
            raise ValueError("Name cannot be empty")
        return name.strip()

    @field_validator('email')
    def check_email(cls, email: str) -> str:
        if not email.strip():
            raise ValueError("Email cannot be empty")
        if not is_valid_email(email):
            raise ValueError("Invalid email")
        return email.strip()

    @field_validator('birthday_date', mode='before')
    def check_birthday_date(cls, birthday_date) -> date:

        birthday = date.today()

        if not birthday_date:
            raise ValueError("Birthday_date cannot be empty")

        if isinstance(birthday_date, date):
            return birthday_date

        if isinstance(birthday_date, str):
            try:
                birthday: date = datetime.strptime(birthday_date, '%Y-%m-%d').date()
            except ValueError:
                raise ValueError('Invalid date format. Use YYYY-MM-DD')
        else:
            raise ValueError('Birthday date must be of type datetime.date or string')

        age = calculate_age(birthday)

        # checking that birthday year is not out of age restrictions
        if age < 18:
            raise ValueError("You must be at least 18 years old")

        if age > 100:
            raise ValueError("Age cannot exceed 100 years.")

        return birthday_date

def calculate_age(birth_date):
    today = date.today()
    if birth_date > today:
        raise ValueError("Birthday date cannot be greater than today")
    age = today.year - birth_date.year
    # If birthday has not been yet
    if (today.month, today.day) < (birth_date.month, birth_date.day):
        age -= 1
    return age

def is_valid_email(email):
    try:
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    except AttributeError:
        return False
    except ValueError:
        return False