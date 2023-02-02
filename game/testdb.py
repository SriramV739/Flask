from numpy import genfromtxt
from time import time
from datetime import datetime
from sqlalchemy import Column, Integer, Float, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import MetaData, Table, String, Boolean



engine = create_engine(
        'postgresql://postgres:princely-tunic-670@db.cqxvknmoofzuhxbonmoj.supabase.co:5432/postgres',echo=False)

metadata_obj = MetaData()


# result = engine.execute('SELECT * FROM "games"')
# print(result.fetchall())
result = engine.execute('SELECT * FROM players')
print(result.fetchall())
