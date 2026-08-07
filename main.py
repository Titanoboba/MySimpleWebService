from pydantic import BaseModel, Field, field_validator, ConfigDict
from sql_connection import get_db

class User(BaseModel):
    name: str
    age: int
    email: str = Field(..., alias="email_address")

    # ORM connection
    config = ConfigDict(from_attributes=True)

    @field_validator('age')
    def check_age(cls, age: int) -> int:
        if (age <= 18) or (age >= 100):
            raise ValueError("age must be between 18 and 100")
        return age


with get_db() as connection:
    connection.execute()
    ...

if __name__ == '__main__':
    user1 = User(name = "John", age = 19, email_address="<EMAIL>")
    print(user1.name)
    print(user1.age)
    print(user1.email)
