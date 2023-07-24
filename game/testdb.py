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
#result = engine.execute("select categories, no_questions from game_category where game = 'LWV Demo' and no_questions > 0")
#result1=engine.execute("select * from (select DISTINCT title, question_content, followup, choices, correct_choice, hints, bug_path_name,text_color,background_color,'class' from question q, game_category gc where gc.categories = 'LWV Demo' and game = 'LWV Demo' and status = 'Production' and  array_remove(regexp_split_to_array(lower(btrim(gc.categories, ' ')), '[;|:]\s*'), '') <@ array_remove(regexp_split_to_array(lower(btrim(q.categories,  ' ')), '[;|:]\s*'), '') ) order by random() limit 4")
#result2=engine.execute(" select categories, no_questions from game_category where game = 'Civic Engagement-Mixed Civics and News' and no_questions > 0")
result3=engine.execute("select * from (select distinct title, question_content, followup, choices, correct_choice, hints, bug_path_name,text_color,background_color,'class' from question q, game_category gc where gc.categories = 'LWV Demo' and game = 'LWV Demo' and status = 'Production') as c order by random() limit 4")
print(result3.fetchall()[0][1])