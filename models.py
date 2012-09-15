#!/usr/bin/env python

from sqlalchemy import create_engine
from sqlalchemy import Column
from sqlalchemy import Date
from sqlalchemy import Integer
from sqlalchemy import String


engine = create_engine('sqlite:///mydatabase.db', echo=True)

from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    created = Column(Date)
    updated = Column(Date)
    name = Column(String, nullable=False)
    profile_url = Column(String, nullable=False)
    access_token = Column(String, nullable=False)



metadata = Base.metadata


if __name__ == "__main__":
    metadata.create_all(engine)
