from game import db
#from flask_login import UserMixin
class Games(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    game=db.Column(db.String())
    questions=db.Column(db.String())
    code = db.Column(db.String(), nullable=False)
    time = db.Column(db.Integer())
    starttime=db.Column(db.Integer(),)
    players=db.relationship('Players',backref='owned_game',lazy=True,cascade='all,delete')
class Players(db.Model):
    id=db.Column(db.Integer(),primary_key=True)
    name=db.Column(db.String(length=15))
    score=db.Column(db.Integer())
    game=db.Column(db.Integer(),db.ForeignKey('games.id'))
    streak=db.Column(db.Integer())
    result=db.Column(db.String())
    submission=db.Column(db.String())