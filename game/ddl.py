import numpy
from time import time
from datetime import datetime
from sqlalchemy import Column, Integer, Float, Date, String, VARCHAR, select, MetaData, Table, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import csv
import pandas as pd
engine = create_engine('sqlite:///verifyit.db')

metadata_obj = MetaData()

author_rows = Table('author', metadata_obj,
    Column('name', String(64), primary_key=True),
    Column('tag_line', String(64)),
)


game_category_rows = Table('game_category', metadata_obj,
    Column('bug_path_name', String(64)),
    Column('text_color', String(64)),
    Column('background_color', String(64)),
    Column('class', String(64)),
    Column('game', String(64)),
    Column('categories', String(64)),
    Column('no_questions', Integer),
)


game_leader_rows = Table('game_leader', metadata_obj,
    Column('city', String(64)),
    Column('leader_handle', String(64)),
    Column('current_play', Integer),
    Column('created_at', DateTime),
    Column('is_teacher', Boolean),
    Column('school', String(64)),
    Column('grade', Integer),
)


game_rows = Table('game', metadata_obj,
    Column('game_group', String(64)),
    Column('play_code', String(64)),
    Column('when', DateTime), #check again
    Column('name', String(64)),
    Column('designer', Boolean),
    Column('description', String(64)),
)


play_rows = Table('play', metadata_obj,
    Column('game_leader', String(64)),
    Column('play_code', Boolean),
    Column('game_status', String(64)),
    Column('location', String(64)),
    Column('game', String(64)),
    Column('play', Integer),
)

question_rows = Table('question', metadata_obj,
    Column('last_modified', DateTime), #check date
    Column('question_content', String(500)), #have to redefine this String(512)
    Column('title', String(64)),
    Column('location', String(64)),
    Column('game', String(64)),
    Column('play', Integer),
)

source_rows = Table('source', metadata_obj,
    Column('name', String(64)),
    Column('hints', String(512)), #have to redefine this String(512)
    Column('description', String(512)), #check String(512)
)


status_rows = Table('status', metadata_obj,
    Column('name', String(64)),
)
#fix this entire entry



metadata_obj.create_all(engine)

