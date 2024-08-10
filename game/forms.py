from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, IntegerField, FloatField
from wtforms.validators import Length, EqualTo, Email, DataRequired, ValidationError,InputRequired
from game.models import Games
from flask import session
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, delete, func
import os
class JoinForm(FlaskForm):
    name=StringField(label="Name",validators=[Length(min=1,max=15)])
    code=StringField(label="Code")
    submit=SubmitField(label='Join')
    
class StartGameForm(FlaskForm):
    def validate_code(self,code):
        TURSO_DATABASE_URL = os.environ.get("TURSO_DATABASE_URL")
        TURSO_AUTH_TOKEN = os.environ.get("TURSO_AUTH_TOKEN")
        dbUrl = f"sqlite+{TURSO_DATABASE_URL}/?authToken={TURSO_AUTH_TOKEN}&secure=true"
        try:
            engine = create_engine(dbUrl, connect_args={'check_same_thread': False}, echo=True)
        except:
            print("Can't create engine")

        Session = sessionmaker(bind=engine)
        dbSession = Session()
        try:
            handles=session.get("handles",[])
            if code.data in handles:
                pass
            else:
                countInDb=dbSession.query(Games).filter(Games.code==code.data).count()
                if countInDb>0:
                    print(countInDb)
                    raise ValidationError('Code already exists! Please try a different code')
        except:
            countInDb=dbSession.query(Games).filter(Games.code==code.data).count()
            if countInDb>0:
                print(countInDb)
                raise ValidationError('Code already exists! Please try a different code')
    code=StringField(validators=[DataRequired(),Length(min=3,max=11)])
    submit = SubmitField(label='Start')
    
class SubmitAnswerForm(FlaskForm):
    submitb=SubmitField(label='Submit')
