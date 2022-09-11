from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, IntegerField, FloatField
from wtforms.validators import Length, EqualTo, Email, DataRequired, ValidationError,InputRequired
class JoinForm(FlaskForm):
    name=StringField(label="Name")
    code=IntegerField(label="Code")
    submit=SubmitField(label='Join')
class StartGameForm(FlaskForm):
    submit = SubmitField(label='Start')