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
def remove_html_tags(text):
    """Remove html tags from a string"""
    import re
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text)
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
    return render_template("waitscreenplayer.html",game=Games.query.filter_by(id=gameid).first()
    ,player=Players.query.filter_by(id=playerid).first())
@app.route("/questionhost/<gameid>/<qnum>",methods=["GET","POST"])
def question_host_page(gameid,qnum):
    game=Games.query.filter_by(id=gameid).first()
    return render_template("questionhost.html",engine=engine,qnum=int(qnum),
    game=game)
@app.route("/question/<playerid>/<gameid>/<qnum>",methods=["GET","POST"])
def question_page(playerid,gameid,qnum):
    form=SubmitAnswerForm()
    qnum=int(qnum)
    game=Games.query.filter_by(id=gameid).first()
    player=Players.query.filter_by(id=int(playerid)).first()
    oqry="Select correct_choice FROM question_rows WHERE id=="+str(game.questions.split(',')[qnum])
    corrans=engine.execute(oqry).fetchall()[0][0]-1
    if request.method=="POST" and request.form.get("timeleft") is not None:
        timel=float(request.form.get("timeleft"))
        print(timel+1000000)
        ans=request.form.get("choice")
        if ans is None or timel==0:
            ans=""
        print(ans)
        player.submission+=(ans+';')
        if ans!="":
            if int(ans)==corrans:
                player.score+=500+float(request.form.get("timeleft"))*10+player.streak*20
                player.streak+=1
                player.result+="1;"
            else:
                player.streak=0
                player.result+="0;"
        else:
            player.streak=0
            player.result+="0;"
        db.session.commit()
        #rt="/submittedanswer/"+str(playerid)+"/"+str(gameid)+"/"+str(qnum)
        if timel>0:
            rt="/submittedanswer/"+str(playerid)+"/"+str(gameid)+"/"+str(qnum)
            return redirect(rt)
        else:
            rt="/resultplayer/"+str(player.id)+'/'+str(game.id)+'/'+str(qnum)
            return redirect(rt)
    return render_template("question.html",engine=engine,qnum=int(qnum),form=form
    ,player=player,game=game)
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

@app.route("/submittedanswer/<playerid>/<gameid>/<qnum>")
def submitted_answer_page(playerid,gameid,qnum):
    game=Games.query.filter_by(id=gameid).first()
    return render_template("submittedanswer.html",game=game,qnum=int(qnum),playerid=playerid)

@app.route("/resultplayer/<playerid>/<gameid>/<qnum>")
def player_result_page(playerid,gameid,qnum):
    qnum=int(qnum)
    game=Games.query.filter_by(id=gameid).first()
    oqry="Select correct_choice FROM question_rows WHERE id=="+str(game.questions.split(',')[qnum])
    corrans=engine.execute(oqry).fetchall()[0][0]-1
    subnums=[0]*len(engine.execute("Select choices FROM question_rows").fetchall()[int(game.questions.split(',')[qnum])][0].split('\n')[1:-2])
    for player in Players.query.filter_by(game=gameid):
        try:
            if player.submission.split(';')[qnum]!="":
                subnums[int(player.submission.split(';')[qnum])]+=1
        except:
            pass
    try:
        pans=(Players.query.filter_by(id=playerid).first().submission.split(';')[qnum])
    except:
        pans=""
    if pans!="":
        pans=int(pans)
    print("-"+str(pans))
    return render_template("resultplayer.html",player=Players.query.filter_by(id=playerid).first(),game=game,qnum=int(qnum)
    ,corrans=corrans,subnums=subnums,pans=pans,engine=engine)

@app.route("/leaderboardp/<playerid>/<gameid>/<qnum>")
def leaderboard_player_page(playerid,gameid,qnum):
    ps=Players.query.filter_by(game=gameid).order_by(Players.score.desc())
    return render_template("leaderboardplayer.html",ps=ps,playerid=playerid,gameid=gameid,qnum=int(qnum))

@app.route("/leaderboardh/<gameid>/<qnum>")
def leaderboard_host_page(gameid,qnum):
    ps=Players.query.filter_by(game=gameid).order_by(Players.score.desc())
    return render_template("leaderboardhost.html",ps=ps,game=Games.query.filter_by(id=gameid).first(),qnum=int(qnum))

@app.route("/playerfollowup/<playerid>/<gameid>/<qnum>")
def followup_player_page(playerid,gameid,qnum):
    game=Games.query.filter_by(id=gameid).first()
    q=engine.execute("Select followup FROM question_rows").fetchall()[int(game.questions.split(',')[int(qnum)])][0]
    return render_template("followupplayer.html",q=q,playerid=playerid,gameid=gameid,qnum=qnum,game=game)

@app.route("/resulthost/<gameid>/<qnum>")
def host_result_page(gameid,qnum):
    qnum=int(qnum)
    game=Games.query.filter_by(id=gameid).first()
    oqry="Select correct_choice FROM question_rows WHERE id=="+str(game.questions.split(',')[qnum])
    corrans=engine.execute(oqry).fetchall()[0][0]-1
    subnums=[0]*len(engine.execute("Select choices FROM question_rows").fetchall()[int(game.questions.split(',')[qnum])][0].split('\n')[1:-2])
    for player in Players.query.filter_by(game=gameid):
        try:
            if player.submission.split(';')[qnum]!="":
                subnums[int(player.submission.split(';')[qnum])]+=1
        except:
            pass
    return render_template("resulthost.html",game=game,qnum=int(qnum)
    ,corrans=corrans,subnums=subnums,engine=engine)

@app.route("/hostfollowup/<gameid>/<qnum>")
def followup_host_page(gameid,qnum):
    game=Games.query.filter_by(id=gameid).first()
    q=engine.execute("Select followup FROM question_rows").fetchall()[int(game.questions.split(',')[int(qnum)])][0]
    return render_template("followuphost.html",q=q,game=Games.query.filter_by(id=gameid).first(),qnum=int(qnum))

@app.route("/podium/<gameid>")
def podium_page(gameid):
    ps=Players.query.filter_by(game=gameid).order_by(Players.score.desc())
    return render_template("podium.html",ps=ps,game=Games.query.filter_by(id=gameid).first())

# @socketio.on('text')
# def text(data):
#     print(data)
#     #print("Message: "+msg.msg)
#     emit('print',data)
# @app.route("/question/<qnum>",methods=["GET","POST"])
# def question_page(qnum):
#     choices=remove_html_tags(engine.execute("Select choices FROM question_rows").fetchall()[int(qnum)][0]).split('\n')[1:-2]
#     answer=(engine.execute("Select correct_choice FROM question_rows").fetchall()[int(qnum)][0])
#     print(answer)
#     return render_template("temp.html",engine=engine,qnum=int(qnum),len=len(choices),choices=choices,answer=answer)
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

@socketio.on('tleft')
def timeleft(data):
    #print('fasdf')
    emit('tleft',data,broadcast=True)

@socketio.on('timeup')
def timeup(gid):
    
    emit('timeup',gid,broadcast=True)

@socketio.on('gotofollowup')
def gotofollowup(gid):
    emit('gotofollowup',gid,broadcast=True)

@socketio.on('gotolb')
def gotofollowup(gid):
    emit('gotolb',gid,broadcast=True)

@socketio.on('gotonextq')
def gotofollowup(data):
    game=Games.query.filter_by(id=data["gid"]).first()
    print(data["qon"],len(game.questions.split(','))-2)
    if int(data["qon"])==len(game.questions.split(','))-2:
        emit('gotofinal',data["gid"],broadcast=True)
    else:
        emit('gotonextq',data["gid"],broadcast=True)