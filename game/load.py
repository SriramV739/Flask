import numpy
from time import time
from datetime import datetime
from sqlalchemy import Column, Integer, Float, Date, String, VARCHAR, select, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import csv
import pandas as pd

#creating engine

try:
    engine = create_engine(
        'sqlite:///verifyit.db',echo=False)
except:
    print("Can't create 'engine")

meta_data=MetaData()


conn=engine.connect()

#diff file paths

csv_file_path="/Users/sriram/Downloads/Flask/csv/question.csv"
csv1_file_path="/Users/sriram/Downloads/Flask/csv/author.csv"
csv2_file_path="/Users/sriram/Downloads/Flask/csv/game_category.csv"
csv3_file_path="/Users/sriram/Downloads/Flask/csv/game_leader.csv" 
csv4_file_path="/Users/sriram/Downloads/Flask/csv/game.csv"
csv5_file_path="/Users/sriram/Downloads/Flask/csv/play.csv"
csv6_file_path="/Users/sriram/Downloads/Flask/csv/question.csv"
csv7_file_path="/Users/sriram/Downloads/Flask/csv/source.csv"
csv8_file_path="/Users/sriram/Downloads/Flask/csv/status.csv"

arr=[csv_file_path,csv1_file_path,csv2_file_path,csv3_file_path,csv4_file_path,csv5_file_path,csv6_file_path,csv7_file_path,csv8_file_path]
arr1=["question","author","game_category","game_leader","game","play","question","source","status"]

#reading into db


for i in range(len(arr)):
    with open(arr[i], 'r') as file:
        df = pd.read_csv(file,quotechar='"',doublequote=True)
    try:
        with engine.begin() as connection:
            df.to_sql(arr1[i], con=connection, index_label='id', if_exists='replace')
            #print('Done, ok!')
    except:
        print('Something went wrong!')

print(engine.execute("select categories, no_questions from game_category where game = $1 -- e.g. 'Voting-TX Mixed News and Civics' and no_questions > 0").fetchall())

