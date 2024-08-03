# Define the tables
from sqlalchemy import Column, Integer, Float, Date, String, VARCHAR, select, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine, delete, func
from sqlalchemy.orm import sessionmaker
import time,os,sys
from sqlalchemy import create_engine
from sqlalchemy import String
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy import ForeignKey
from sqlalchemy import create_engine


class Base(DeclarativeBase):
    pass

class Game(Base):
    __tablename__ = "game"
    game_id = Column(Integer, primary_key=True)
    game_name = Column(String(100))
    game_status = Column(String(100))
    game_group = Column(String(100))
    game_description = Column(String(100))

class GameCategoryModel(Base):
    __tablename__ = "game_category"
    game_category_id = Column(Integer, primary_key=True)
    game_id = Column(Integer, ForeignKey('game.game_id'))
    gc_categories = Column(String(100))
    no_questions = Column(Integer)
