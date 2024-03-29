from flask import Flask, render_template, request,logging
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin
from sqlalchemy import create_engine
from flask_socketio import SocketIO,send
#test change
import logging
    
import os
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:lwvverifyit1@db.lyphnmeqkudqpefwvmeq.supabase.co:5432/postgres' #'sqlite:///verifyit.db'
app.config['SECRET_KEY']=('59d7ded4b4d238a1b4ac23fa')
db = SQLAlchemy(app)
from game import models
#db.drop_all()
#db.create_all()
#db.drop_all()
#db.create_all()
with app.app_context():
    try:
        # Begin a transaction
        db.session.begin()

        # ... your code here ...

        # Commit the transaction if everything is successful
        db.session.commit()
    except Exception as e:
        # Roll back the transaction in case of an error
        db.session.rollback()
        raise e
socketio=SocketIO(app,logger=False)
socketio.init_app(app, cors_allowed_origins="*")
logging.getLogger('socketio').setLevel(logging.ERROR)
logging.getLogger('engineio').setLevel(logging.ERROR)
logging.getLogger('geventwebsocket.handler').setLevel(logging.ERROR)
# login_manager=LoginManager(app)
# login_manager.login_view = "login_page"
# login_manager.login_message_category="info"
from game import routes

