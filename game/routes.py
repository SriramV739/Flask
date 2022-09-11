'''from flask import Flask, render_template

app=Flask(__name__)
@app.route('/')
def index():
    return render_template('index.html')
def join():
    form=JoinForm()
    if form.submit.data and form.validate():
        newlink="/waiting/"+str(form.code.data)
        return redirect(newlink)
    return render_template("join.html",form=form)
if __name__=="__main__":
    app.run(debug=True)'''

#from game.load import engine
from game import app
from flask import render_template, redirect,url_for, flash, request
#from game.models import
from game.forms import JoinForm,StartGameForm
from game import db
from game.models import Game,Players
from sqlalchemy import Column, Integer, Float, Date, String, VARCHAR, select, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from flask_login import login_user,logout_user, login_required, current_user
try:
    engine = create_engine(
        'sqlite:///verifyit.db',echo=False)
except:
    print("Can't create 'engine")
db.create_all()
meta_data=MetaData()

conn=engine.connect()
@app.route("/")
@app.route("/home")
def index():
    return render_template("index.html")
@app.route("/players")
def player():
    return render_template("players.html")
@app.route("/join",methods=["GET","POST"])
def join_page():
    form=JoinForm()
    if form.submit.data and form.validate():
        #db.session.add()
        newlink="/waiting/"+str(form.code.data)
        return redirect(newlink)
    return render_template("join.html",form=form)
@app.route("/waiting/<name>/<id>")
def waiting_page(name,id):
    return render_template("waitscreenplayer.html")
@app.route("/question/<qnum>")
def question_page(qnum):
    return render_template("question.html",engine=engine,qnum=int(qnum))
@app.route('/start',methods=["GET","POST"])
def start_page():
    form=StartGameForm()
    if form.submit.data:
        gamechoice=request.form.get("game_choice")
        print(gamechoice)
    return render_template("start.html",engine=engine,form=form)