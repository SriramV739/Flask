from flask import Flask, render_template, request,logging
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin
from sqlalchemy import create_engine
from flask_socketio import SocketIO,send
from sqlalchemy.orm import sessionmaker

#test change
import logging,os
os.environ["TURSO_DATABASE_URL"]='libsql://verifyit-production-ricgagliardi.turso.io'
os.environ["TURSO_AUTH_TOKEN"]="eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9.eyJhIjoicnciLCJpYXQiOjE3MjI3OTMwMzMsImlkIjoiYzVmNzllN2EtMDRjNS00ZjVjLThlYzYtODhhM2UyNzUyZDE0In0.TiUAq88z4nyPVsyIFbLD8tEgYx9gWzyyxGGYKXaCG_6Z5FNI7HAYe5dk7Q4jWPKoRi4V4ML9ZFjxI540fMBfDQ"
    
app = Flask(__name__)
TURSO_DATABASE_URL = os.environ.get("TURSO_DATABASE_URL")
TURSO_AUTH_TOKEN = os.environ.get("TURSO_AUTH_TOKEN")
# app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:lwvverifyit1@db.lyphnmeqkudqpefwvmeq.supabase.co:5432/postgres' #'sqlite:///verifyit.db'
# app.config['SECRET_KEY']=('59d7ded4b4d238a1b4ac23fa')
app.config['SECRET_KEY']=(TURSO_AUTH_TOKEN)

socketio=SocketIO(app,logger=False)
socketio.init_app(app, cors_allowed_origins="*")
logging.getLogger('socketio').setLevel(logging.ERROR)
logging.getLogger('engineio').setLevel(logging.ERROR)
logging.getLogger('geventwebsocket.handler').setLevel(logging.ERROR)
TURSO_DATABASE_URL = os.environ.get("TURSO_DATABASE_URL")
TURSO_AUTH_TOKEN = os.environ.get("TURSO_AUTH_TOKEN")

dbUrl = f"sqlite+{TURSO_DATABASE_URL}/?authToken={TURSO_AUTH_TOKEN}&secure=true"
try:
    engine = create_engine(dbUrl, connect_args={'check_same_thread': False}, echo=True)
except:
    print("Can't create engine")

Session = sessionmaker(bind=engine)
dbSession = Session()

from game import routes
