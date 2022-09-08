from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin
from sqlalchemy import create_engine


import os
app = Flask(__name__)
#app.config['SQLALCHEMY_DATABASE_URI'] = 'willset'
app.config['SECRET_KEY']=('59d7ded4b4d238a1b4ac23fa')
db = SQLAlchemy(app)

# login_manager=LoginManager(app)
# login_manager.login_view = "login_page"
# login_manager.login_message_category="info"
from game import routes

