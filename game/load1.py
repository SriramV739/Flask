from numpy import genfromtxt
from time import time
from datetime import datetime
from sqlalchemy import Column, Integer, Float, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import MetaData, Table, String, Boolean



engine = create_engine('sqlite:///verifyit.db')
metadata_obj = MetaData()

file_name = "/Users/sriram/Downloads/Flask/csv/game_rows.csv" #sample CSV file used:  http://www.google.com/finance/historical?q=NYSE%3AT&ei=W4ikVam8LYWjmAGjhoHACw&output=csv
data = Load_Data(file_name) 

civics_rows = Table('civics_rows', metadata_obj,
    Column('game_group', String, primary_key=True),
    Column('is_available_single_player', Boolean, nullable=False),
    Column('game_status', String(60)),
    Column('name', String(60)),
    Column('designer', String(50), nullable=False),
    Column('description', String(50), nullable=False)
)

metadata_obj.create_all(engine)

for i in data:
            record = civics_rows(**{
                #'date' : datetime.strptime(i[0], '%d-%b-%y').date(),
                'game_group' : i[0],
                'is_available_single_player' : i[1],
                'game_status' : i[2],
                'name' : i[3],
                'designer' : i[4],
                'description': i[5]
            })
            s.add(record) #Add all the records

        s.commit() #Attempt to commit all the records
    except:
        s.rollback() #Rollback the changes on error
    finally:
        s.close() #Close the connection
    #print "Time elapsed: " + str(time() - t) + " s." #0.091s


'''PRAGMA table_info(user){}
CREATE TABLE user(
        user_id INTEGER NOT NULL PRIMARY KEY,
        user_name VARCHAR(16) NOT NULL,
        email_address VARCHAR(60),
        nickname VARCHAR(50) NOT NULL
)
PRAGMA table_info(user_prefs){}
CREATE TABLE user_prefs(
        pref_id INTEGER NOT NULL PRIMARY KEY,
        user_id INTEGER NOT NULL REFERENCES user(user_id),
        pref_name VARCHAR(40) NOT NULL,
        pref_value VARCHAR(100)
)'''

result = engine.execute('SELECT * FROM "civics_rows"')
print(result.fetchall())