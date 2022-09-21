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
from game.forms import JoinForm,StartGameForm,SubmitAnswerForm
from game import db,socketio
from game.models import Games,Players
from sqlalchemy import Column, Integer, Float, Date, String, VARCHAR, select, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from flask_login import login_user,logout_user, login_required, current_user
import random
from flask_socketio import SocketIO,send, emit

try:
    engine = create_engine(
        'sqlite:///verifyit.db',echo=False)
except:
    print("Can't create 'engine")
#db.drop_all()
#db.create_all()
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
        if Games.query.filter_by(code=form.code.data).count()==0:
            flash("Invalid code",category="danger")
        elif Players.query.filter_by(name=form.name.data,game=Games.query.filter_by(code=form.code.data).first().id).count()!=0:
            flash("Name already in use. Please choose another name.", category="danger")
        else:
            db.session.add(Players(name=form.name.data,score=0,game=Games.query.filter_by(code=form.code.data).first().id
                               ,streak=0,submission="",result=""))
            db.session.commit()
            newlink="/waiting/"+str(Players.query.filter_by(name=form.name.data,game=Games.query.filter_by(code=form.code.data).first().id).first().id)+"/"+\
                    str(Games.query.filter_by(code=form.code.data).first().id)
            return redirect(newlink)
    return render_template("join.html",form=form)
@app.route("/waiting/<playerid>/<gameid>")
def waiting_page(playerid,gameid):
    return render_template("waitscreenplayer.html",game=Games.query.filter_by(id=gameid).first())
@app.route("/question/<playerid>/<gameid>/<qnum>",methods=["GET","POST"])
def question_page(playerid,gameid,qnum):
    form=SubmitAnswerForm()
    player=Players.query.filter_by(id=int(playerid)).first()
    oqry="Select correct_choice FROM question_rows WHERE id=="+qnum
    corrans=engine.execute(oqry).fetchall()[0][0]-1
    print(corrans)
    if form.submit.data:
        ans=request.form.get("choice")
        player.submission+=(ans+';')
        if int(ans)==corrans:
            player.streak+=1
            player.result+="1;"
        else:
            player.streak=0
            player.result+="0;"
    return render_template("question.html",engine=engine,qnum=int(qnum),form=form)
@app.route('/start',methods=["GET","POST"])
def start_page():
    form=StartGameForm()
    if form.submit.data:

        if request.form.get("game_choice"):
            gamechoice = int(request.form.get("game_choice"))
            gamerow=engine.execute("Select * FROM game_category_rows").fetchall()[gamechoice]
            qry="Select id FROM question_rows WHERE categories LIKE '%"+gamerow[6]+"%'"
            pqs=list(engine.execute(qry).fetchall())
            #print(pqs)
            qs=random.sample(pqs,gamerow[7])
            print(qs)
            qstr=""
            for element in qs:
                qstr+=(str(element[0])+",")
            print(qstr)
            print(gamerow)
            print(gamechoice)
            code = random.randint(100000, 999999)
            while Games.query.filter_by(code=str(code)).count() > 0:
                code = random.randint(100000, 999999)
            db.session.add(Games(game=gamechoice,code=code,time=0,questions=qstr))
            db.session.commit()
            nl="/waiting/host/"+str(Games.query.filter_by(code=code).first().id)
            return redirect(nl)
        else:
            flash("Please choose a game.",category="danger")
    return render_template("start.html",engine=engine,form=form)
@app.route("/waiting/host/<id>",methods=["GET","POST"])
def waiting_host_page(id):
    form=StartGameForm()
    players=Players.query.filter_by(game=id)
    pnames=[]
    for p in players:
        pnames.append(p.name)
    if form.submit.data:
        print("a")
    return render_template("waitscreenhost.html",game=Games.query.filter_by(id=id).first(),form=form,pnames=pnames)

# @socketio.on('text')
# def text(data):
#     print(data)
#     #print("Message: "+msg.msg)
#     emit('print',data)

@socketio.on('newc')
def newc(gid):
    #print(gid)
    #print(request.path.split('/')[2])
    players=Players.query.filter_by(game=gid)
    pnames=[]
    for p in players:
        pnames.append(p.name)
    print(pnames)
    emit('addnewc',{"players": pnames,"gameid":gid},broadcast=True)

@socketio.on('gamehasstarted')
def gamehasstarted(gid):
    print('ghs')
    emit('gamehasstarted',gid,broadcast=True)

