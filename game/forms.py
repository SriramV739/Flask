from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, IntegerField, FloatField
from wtforms.validators import Length, EqualTo, Email, DataRequired, ValidationError,InputRequired
from game.models import Games
from flask import session
class JoinForm(FlaskForm):
    name=StringField(label="Name",validators=[Length(min=1,max=15)])
    code=StringField(label="Code")
    submit=SubmitField(label='Join')
class StartGameForm(FlaskForm):
    def validate_code(self,code):
        try:
            print(session['handles'])
            if code.data in session['handles']:
                pass
            else:
                if Games.query.filter_by(code=code.data).count() > 0:
                    print(Games.query.filter_by(code=code.data).count())
                    raise ValidationError('Code already exists! Please try a different code')
        except:
            if Games.query.filter_by(code=code.data).count() > 0:
                    print(Games.query.filter_by(code=code.data).count())
                    raise ValidationError('Code already exists! Please try a different code')
    code=StringField(validators=[DataRequired(),Length(min=5,max=20)])
    submit = SubmitField(label='Start')
class SubmitAnswerForm(FlaskForm):
    submitb=SubmitField(label='Submit')