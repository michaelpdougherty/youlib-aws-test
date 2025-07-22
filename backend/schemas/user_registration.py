from pydantic import BaseModel

class UserRegistration(BaseModel):
    email: str
    password: str
    firstName: str
    lastName: str
    zipCode: str
    libraryName: str