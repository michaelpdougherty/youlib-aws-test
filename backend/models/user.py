from sqlalchemy import Column, Integer, String
from db.session import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String, nullable=False)
    password = Column(String, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    zip_code = Column(String, nullable=False)
    library_name = Column(String, nullable=False)