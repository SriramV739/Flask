from game import db
#from flask_login import UserMixin
class Game(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    questions=db.Column(db.String())
    code = db.Column(db.Integer(), nullable=False)
    time = db.Column(db.Integer())
    players=db.relationship('Players',backref='owned_game',lazy=True)
#class Qcopies(db.Model):
    #question_content=db.Column(db.String(length))
class Players(db.Model):
    id=db.Column(db.Integer(),primary_key=True)
    name=db.Column(db.String(length=15))
    score=db.Column(db.Integer())
    game=db.Column(db.Integer(),db.ForeignKey('game.id'))
    streak=db.Column(db.Integer())
    result=db.Column(db.String())