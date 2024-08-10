#from game import db
#from flask_login import UserMixin
from sqlalchemy import Column, Integer, Float, Date, String, VARCHAR, select, MetaData,ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm  import DeclarativeBase,Mapped,mapped_column,Session


class Base(DeclarativeBase):
    pass

class Game(Base):
    __tablename__ = "game"
    game_id = Column(Integer, primary_key=True)
    game_name = Column(String)
    game_status = Column(String)
    game_group = Column(String)
    game_description = Column(String)

class GameCategory(Base):
    __tablename__ = "game_category"
    game_category_id = Column(Integer, primary_key=True)
    game_id = Column(Integer, ForeignKey('game.game_id'))
    gc_categories = Column(String)
    no_questions = Column(Integer)

class Question(Base):
    __tablename__ = "question"
    question_id = Column(Integer, primary_key=True)
    title = Column(String)
    question_categories = Column(String)
    question_content=Column(String)
    followup=Column(String)
    choices=Column(String)
    correct_choice=Column(Integer)
    hints=Column(String)

class Games(Base):
    __tablename__ = "Games"
    id = Column(Integer, primary_key=True)
    game=Column(String)
    questions=Column(String)
    code = Column(String, nullable=False)
    time = Column(Integer)
    starttime=Column(Integer,)
    # players=db.relationship('Players',backref='owned_game',lazy=True,cascade='all,delete')


class Players(Base):
    __tablename__ = "Players"
    id=Column(Integer(),primary_key=True)
    name=Column(String)
    score=Column(Integer)
    # game_id=db.Column(db.Integer(),db.ForeignKey('Games.id'))
    game_id=Column(Integer)
    streak=Column(Integer)
    result=Column(String)
    submission=Column(String)

class Source(Base):
    __tablename__ = "source"
    source_id=Column(String,primary_key=True)
    name=Column(String)
    description=Column(String)
    hints=Column(String)

