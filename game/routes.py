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
from flask import render_template, redirect,url_for, flash, request, session
#from game.models import
from game.forms import JoinForm,StartGameForm,SubmitAnswerForm
from game import db,socketio
from game.models import Games,Players
from sqlalchemy import Column, Integer, Float, Date, String, VARCHAR, select, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine, delete, func
from sqlalchemy.orm import sessionmaker
from flask_login import login_user,logout_user, login_required, current_user
import random
from flask_socketio import SocketIO,send, emit
from engineio.payload import Payload
import time
Payload.max_decode_packets = 1000
#print("sdfsfkj")
removed={}
numconnected={}
numanswered={}
pnames={}
def remove_html_tags(text):
    """Remove html tags from a string"""
    import re
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text)
try:
    engine = create_engine(
        'postgresql://postgres:princely-tunic-670@db.cqxvknmoofzuhxbonmoj.supabase.co:5432/postgres',echo=False)

except:
    print("Can't create 'engine")
#db.drop_all()
#db.create_all()
meta_data=MetaData()

conn=engine.connect()

@app.route("/")
@app.route("/home")
def index():
    #print("Hello Index")
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
    global pnames
    global numconnected
    if gameid not in numconnected:
        numconnected[gameid]=1
    else:
        numconnected[gameid]+=1
    return render_template("waitscreenplayer.html",game=Games.query.filter_by(id=gameid).first()
    ,player=Players.query.filter_by(id=playerid).first(),pnames=pnames[gameid],playerid=playerid)
@app.route("/questionhost/<gameid>/<qnum>",methods=["GET","POST"])
def question_host_page(gameid,qnum):
    global numanswered
    global pnames
    game=Games.query.filter_by(id=gameid).first()
    oqry="Select question_content FROM question WHERE title=%s"
    #oqry="Select question_content FROM question WHERE title='"+str(game.questions.split(',')[int(qnum)])+"'"
    #q=engine.execute(oqry).fetchall()[0][0]
    q=engine.execute(oqry,(str(game.questions.split(',')[int(qnum)]))).fetchall()[0][0]
    result = []

    for item in q.split("["):
        result.extend(item.split("]"))

    #print(result)
    for i in range(len(result)):
        if i%2==1:
            #print(result[i])
            qry="Select description FROM source WHERE name='"+result[i].strip().lower()+"'"
            content=engine.execute(qry).fetchall()
            if content:
                result[i]="<span><!--"+content[0][0]+"--></span>"
                #result[i]="<small style='display:none'>"+content[0][0]+"</small>"
            else:
                #try:
                    result[i]=int(result[i].strip())
                    oqry="Select hints FROM question WHERE title='"+str(game.questions.split(',')[int(qnum)])+"'"
                    hints=engine.execute(oqry).fetchall()[0][0]            
                    li_list = []
                    start_pos = 0
                    while True:
                        start_li = hints.find("<li>", start_pos)
                        if start_li == -1:
                            break
                        end_li = hints.find("</li>", start_li)
                        li_content = hints[start_li+4:end_li].strip()
                        li_list.append(li_content)
                        start_pos = end_li
                    #print("________________________________________________________________")
                    #print(li_list)
                    result[i]="<span><!--"+li_list[result[i]-1]+"--></span>"
                # except:
                #     result[i]=str(result[i])
    #print(result)
    q = " ".join(result)
    return render_template("questionhost.html",engine=engine,qnum=int(qnum),q=q,
    game=game,numconnected=numconnected[gameid],pnames=pnames[gameid],numanswered=numanswered[gameid])

@app.route("/singlequestion/<qnum>",methods=["GET","POST"])
def question_page(qnum):
    choices=remove_html_tags(engine.execute("Select choices FROM question").fetchall()[int(qnum)][0]).split('\n')[1:-2]
    answer=(engine.execute("Select correct_choice FROM question").fetchall()[int(qnum)][0])
    #print(answer)
    return render_template("question2.html",engine=engine,qnum=int(qnum),len=len(choices),choices=choices,answer=answer)

@app.route("/followup/<qnum>",methods=["GET","POST"])
def followup(qnum):
    return render_template("followup.html",engine=engine,qnum=int(qnum))


@app.route("/question/<playerid>/<gameid>/<qnum>",methods=["GET","POST"])
def multiquestion_page(playerid,gameid,qnum):
    form=SubmitAnswerForm()
    qnum=int(qnum)
    game=Games.query.filter_by(id=gameid).first()
    player=Players.query.filter_by(id=int(playerid)).first()
    oqry="Select correct_choice FROM question WHERE title=%s"
    try:
        question_title = game.questions.split(',')[qnum]#.replace("'", "")
        corrans=engine.execute(oqry,(question_title)).fetchall()[0][0]-1

    except:
        pass
    #oqry="Select correct_choice FROM question WHERE title='"+question_title+"'"
    if request.method=="POST" and request.form.get("timeleft") is not None:
        timel=float(request.form.get("timeleft"))
        #print(timel+1000000)
        ans=request.form.get("choice")
        if ans is None or timel==0:
            ans=""
        #print(ans)
        player.submission+=(ans+';')
        if ans!="":
            if int(ans)==corrans:
                player.score+=float(request.form.get("timeleft"))*10
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
    oqry="Select question_content FROM question WHERE title=%s"
    #oqry="Select question_content FROM question WHERE title='"+str(game.questions.split(',')[int(qnum)])+"'"
    #q=engine.execute(oqry).fetchall()[0][0]
    result = []
    try:
        q=engine.execute(oqry,(str(game.questions.split(',')[int(qnum)]))).fetchall()[0][0]
        for item in q.split("["):
            result.extend(item.split("]"))
    except:
        pass
    

    

    #print(result)
    for i in range(len(result)):
        if i%2==1:
            #print(result[i])
            qry="Select description FROM source WHERE name='"+result[i].strip().lower()+"'"
            content=engine.execute(qry).fetchall()
            if content:
                result[i]="<span><!--"+content[0][0]+"--></span>"
                #result[i]="<small style='display:none'>"+content[0][0]+"</small>"
            else:
                #try:
                    result[i]=int(result[i].strip())
                    oqry="Select hints FROM question WHERE title='"+str(game.questions.split(',')[int(qnum)])+"'"
                    hints=engine.execute(oqry).fetchall()[0][0]            
                    li_list = []
                    start_pos = 0
                    while True:
                        start_li = hints.find("<li>", start_pos)
                        if start_li == -1:
                            break
                        end_li = hints.find("</li>", start_li)
                        li_content = hints[start_li+4:end_li].strip()
                        li_list.append(li_content)
                        start_pos = end_li
                    #print("________________________________________________________________")
                    #print(li_list)
                    result[i]="<span><!--"+li_list[result[i]-1]+"--></span>"
                # except:
                #     result[i]=str(result[i])
    #print(result)
    q = " ".join(result)
    return render_template("question.html",engine=engine,qnum=int(qnum),form=form,q=q
    ,player=player,game=game,playerid=playerid)

def delete_players_helper(pg):
    try:
        
        return Games.query.filter_by(id=pg).first().code
    except:
        return ""
def delete_players_helper1(pg):
    try:

        return Games.query.filter_by(id=pg).first().starttime
    except:
        return 100000000000


@app.route('/start',methods=["GET","POST"])
def start_page():
    form=StartGameForm()
    deleted_objects = Players.__table__.delete().where(float(delete_players_helper1(Players.game))<=time.time()-3600)
    db.session.execute(deleted_objects)
    db.session.commit()
    deleted_objects = Games.__table__.delete().where(Games.starttime<=time.time()-3600)
    db.session.execute(deleted_objects)
    db.session.commit()
    if form.validate_on_submit():

        if request.form.get("game_choice"):
            try:
                print(session["handles"])
            except:
                session["handles"]=[]
            
            session.modified = True
            #print(session["handles"])
            if Games.query.filter_by(code=form.code.data) and form.code.data in session["handles"]:
                update_statement = Games.__table__.update().where(Games.code==form.code.data).values(code="")
                db.session.execute(update_statement)
                db.session.commit()
                #deleted_objects = Players.__table__.delete().where(str(func.delete_players_helper(Players.game))==str(form.code.data))
                #a=db.session.execute(deleted_objects)
                #print(a.rowcount)
                #db.session.commit()
                #deleted_objects = Games.__table__.delete().where(Games.code==form.code.data)

                #db.session.execute(deleted_objects)
                #db.session.commit()
            session["handles"].append(form.code.data)
            gamechoice = str(request.form.get("game_choice"))
            qry="Select * FROM game_category WHERE game='"+gamechoice+"'"
            gamerow=engine.execute(qry).fetchall()[0]
           # print(gamerow)
            qry="Select title FROM question WHERE categories LIKE '%%"+gamerow[6]+"%%'" ##might need to change to gamerow[1]
            pqs=list(engine.execute(qry).fetchall())
            #print(pqs)
            qs=random.sample(pqs,gamerow[2])
            #print(qs)
            qstr=""
            for element in qs:
                qstr+=(str(element[0])+",")
            #print(qstr)
            #print(gamerow)
            print(gamechoice)
            code = form.code.data
            
            #     code = random.randint(100000, 999999)
            db.session.add(Games(game=gamechoice,code=code,time=0,questions=qstr, starttime=time.time()))
            db.session.commit()
            nl="/waiting/host/"+str(Games.query.filter_by(code=code).first().id)
            return redirect(nl)
        else:
    
            flash("Please choose a game.",category="danger")
    if form.errors!={}:
        # for err_msg in form.errors.values():
        #     flash(f'{err_msg}', category='danger')
        flash("This code is already in use. Please choose a different code.",category="danger")
    return render_template("start.html",engine=engine,form=form)
@app.route("/waiting/host/<id>",methods=["GET","POST"])

def waiting_host_page(id):
    global numconnected
    numconnected[id]=0
    global numanswered
    numanswered[id]=0
    form=StartGameForm()
    players=Players.query.filter_by(game=id)
    global pnames
    pnames[id]=[]
    for p in players:
        pnames[id].append(p.name)
    global removed
    if id in removed:
        for i in removed[id]:
            if i in pnames[id]:
                pnames[id].remove(i)
    pnames[id]=list(set(pnames[id]))
    print(pnames,id,flush=True)
    if form.submit.data:
        pass
        #print("a")
    return render_template("waitscreenhost.html",game=Games.query.filter_by(id=id).first(),form=form,pnames=pnames[id])
@app.route("/submittedanswer/<playerid>/<gameid>/<qnum>")
def submitted_answer_page(playerid,gameid,qnum):
    global numanswered
    numanswered[gameid]+=1
    game=Games.query.filter_by(id=gameid).first()
    return render_template("submittedanswer.html",game=game,qnum=int(qnum),playerid=playerid,numconnected=numconnected[gameid],numanswered=numanswered[gameid])

@app.route("/resultplayer/<playerid>/<gameid>/<qnum>")
def player_result_page(playerid,gameid,qnum):
    qnum=int(qnum)
    #print("specific result")
    game=Games.query.filter_by(id=gameid).first()
    oqry="Select correct_choice FROM question WHERE title='"+str(game.questions.split(',')[qnum])+"'"
    corrans=engine.execute(oqry).fetchall()[0][0]-1
    oqry="Select choices FROM question WHERE title='"+str(game.questions.split(',')[qnum])+"'"
    subnums=[0]*len(engine.execute(oqry).fetchall()[0][0].split("\n"))
    for player in Players.query.filter_by(game=gameid):
        try:
            if player.submission.split(';')[qnum]!="":
                subnums[int(player.submission.split(';')[qnum])]+=1
        except:
            global numconnected
            global removed
            print("playerleft",flush=True)
            print(type(gameid))
            print(type(player.name))
            print(numconnected[gameid])
            global pnames
            #Players.query.filter_by(id=Players.id).delete()
            #db.session.commit()
            if player.name in pnames[gameid]:
                pnames[gameid].remove(player.name)
                numconnected[gameid]-=1
                if gameid not in removed:
                    removed[gameid]=[player.name]
                    #numconnected[gameid]-=1
                else:
                    #if player.name not in removed[gameid]:
                        #numconnected[gameid]-=1
                    removed[gameid].append(player.name)
                    removed[gameid]=list(set(removed[gameid]))
            pass

    pans=(Players.query.filter_by(id=playerid).first().submission.split(';')[-1])
    if pans!="":
        pans=int(pans)
    #print("-"+str(pans))
    qry="Select question_content FROM question WHERE title='"+game.questions.split(',')[qnum]+"'"
    #HINTS AND SOURCES
    q=engine.execute(qry).fetchall()[0][0]
    result = []

    for item in q.split("["):
        result.extend(item.split("]"))

    #print(result)
    for i in range(len(result)):
        if i%2==1:
            #print(result[i])
            qry="Select description FROM source WHERE name='"+result[i].strip().lower()+"'"
            content=engine.execute(qry).fetchall()
            if content:
                result[i]="<span><!--"+content[0][0]+"--></span>"
                #result[i]="<small style='display:none'>"+content[0][0]+"</small>"
            else:
                #try:
                    result[i]=int(result[i].strip())
                    oqry="Select hints FROM question WHERE title='"+str(game.questions.split(',')[int(qnum)])+"'"
                    hints=engine.execute(oqry).fetchall()[0][0]            
                    li_list = []
                    start_pos = 0
                    while True:
                        start_li = hints.find("<li>", start_pos)
                        if start_li == -1:
                            break
                        end_li = hints.find("</li>", start_li)
                        li_content = hints[start_li+4:end_li].strip()
                        li_list.append(li_content)
                        start_pos = end_li
                    #print("________________________________________________________________")
                    #print(li_list)
                    result[i]="<span><!--"+li_list[result[i]-1]+"--></span>"
                # except:
                #     result[i]=str(result[i])
    #print(result)
    q = " ".join(result)
    #print(q)
    return render_template("resultplayer.html",player=Players.query.filter_by(id=playerid).first(),game=game,qnum=int(qnum)
    ,corrans=corrans,subnums=subnums,pans=pans,engine=engine,q=q,playerid=playerid)

@app.route("/leaderboardp/<playerid>/<gameid>/<qnum>")
def leaderboard_player_page(playerid,gameid,qnum):
    ps=Players.query.filter_by(game=gameid).order_by(Players.score.desc())
    return render_template("leaderboardplayer.html",ps=ps,playerid=playerid,gameid=gameid,qnum=int(qnum))

@app.route("/leaderboardh/<gameid>/<qnum>")
def leaderboard_host_page(gameid,qnum):
    global numanswered
    numanswered[gameid]=0
    ps=Players.query.filter_by(game=gameid).order_by(Players.score.desc())
    game=Games.query.filter_by(id=gameid).first()
    return render_template("leaderboardhost.html",ps=ps,game=Games.query.filter_by(id=gameid).first(),qnum=int(qnum),totalquestions=len(game.questions.split(','))-2)

@app.route("/playerfollowup/<playerid>/<gameid>/<qnum>")
def followup_player_page(playerid,gameid,qnum):
    game=Games.query.filter_by(id=gameid).first()
    oqry="Select followup FROM question WHERE title='"+str(game.questions.split(',')[int(qnum)])+"'"
    q=engine.execute(oqry).fetchall()[0][0]
   
    result = []

    for item in q.split("["):
        result.extend(item.split("]"))

    print(result)
    for i in range(len(result)):
        if i%2==1:
            #print(result[i])
            qry="Select description FROM source WHERE name='"+result[i].strip().lower()+"'"
            content=engine.execute(qry).fetchall()
            if content:
                result[i]="<span><!--"+content[0][0]+"--></span>"
                #result[i]="<small style='display:none'>"+content[0][0]+"</small>"
            else:
                #try:
                    result[i]=int(result[i].strip())
                    oqry="Select hints FROM question WHERE title='"+str(game.questions.split(',')[int(qnum)])+"'"
                    hints=engine.execute(oqry).fetchall()[0][0]            
                    li_list = []
                    start_pos = 0
                    while True:
                        start_li = hints.find("<li>", start_pos)
                        if start_li == -1:
                            break
                        end_li = hints.find("</li>", start_li)
                        li_content = hints[start_li+4:end_li].strip()
                        li_list.append(li_content)
                        start_pos = end_li
                    #print("________________________________________________________________")
                    #print(li_list)
                    result[i]="<span><!--"+li_list[result[i]-1]+"--></span>"
                # except:
                #     result[i]=str(result[i])
    #print(result)
    q = " ".join(result)
    return render_template("followupplayer.html",engine=engine,q=q,playerid=playerid,gameid=gameid,qnum=qnum,game=game)

@app.route("/resulthost/<gameid>/<qnum>")
def host_result_page(gameid,qnum):
    global numanswered
    numanswered[id]=0
    qnum=int(qnum)
    game=Games.query.filter_by(id=gameid).first()
    oqry="Select correct_choice FROM question WHERE title='"+str(game.questions.split(',')[qnum])+"'"
    corrans=engine.execute(oqry).fetchall()[0][0]-1
    #print("c"+str(corrans))
    oqry="Select choices FROM question WHERE title='"+str(game.questions.split(',')[qnum])+"'"
    subnums=[0]*len(engine.execute(oqry).fetchall()[0][0].split("\n"))
    #print("s"+str(len(subnums)))
    #subnums=[0]*len(engine.execute("Select choices FROM question").fetchall()[int(game.questions.split(',')[qnum])][0].split('\n')[1:-2])
    for player in Players.query.filter_by(game=gameid):
        try:
            if player.submission.split(';')[qnum]!="":
                subnums[int(player.submission.split(';')[qnum])]+=1
                #print("before",flush=True)
                print(player.submission.split(';')[qnum],flush=True)
                #print("after",flush=True)
        except:
            global numconnected
            global removed
            #print("playerleft1",flush=True)
            #print(type(gameid))
            #print(type(player.name))
            #print(numconnected[gameid])
            global pnames
            #Players.query.filter_by(id=Players.id).delete()
            #db.session.commit()
            if player.name in pnames[gameid]:
                pnames[gameid].remove(player.name)
                numconnected[gameid]-=1
                if gameid not in removed:
                    removed[gameid]=[player.name]
                    #numconnected[gameid]-=1
                else:
                    # if player.name not in removed[gameid]:
                    #     numconnected[gameid]-=1
                    removed[gameid].append(player.name)
                    removed[gameid]=list(set(removed[gameid]))
            pass
            #print(int(player.submission.split(';')[qnum]))
    qry="Select question_content FROM question WHERE title='"+game.questions.split(',')[qnum]+"'"
    #HINTS AND SOURCES
    q=engine.execute(qry).fetchall()[0][0]
    result = []

    for item in q.split("["):
        result.extend(item.split("]"))

    #print(result)
    for i in range(len(result)):
        if i%2==1:
            #print(result[i])
            qry="Select description FROM source WHERE name='"+result[i].strip().lower()+"'"
            content=engine.execute(qry).fetchall()
            if content:
                result[i]="<span><!--"+content[0][0]+"--></span>"
                #result[i]="<small style='display:none'>"+content[0][0]+"</small>"
            else:
                #try:
                    result[i]=int(result[i].strip())
                    oqry="Select hints FROM question WHERE title='"+str(game.questions.split(',')[int(qnum)])+"'"
                    hints=engine.execute(oqry).fetchall()[0][0]            
                    li_list = []
                    start_pos = 0
                    while True:
                        start_li = hints.find("<li>", start_pos)
                        if start_li == -1:
                            break
                        end_li = hints.find("</li>", start_li)
                        li_content = hints[start_li+4:end_li].strip()
                        li_list.append(li_content)
                        start_pos = end_li
                    #print("________________________________________________________________")
                    #print(li_list)
                    result[i]="<span><!--"+li_list[result[i]-1]+"--></span>"
                # except:
                #     result[i]=str(result[i])
    #print(result)
    q = " ".join(result)
    #print(q)    
    return render_template("resulthost.html",game=game,qnum=int(qnum),q=q
    ,corrans=corrans,subnums=subnums,engine=engine)

@app.route("/hostfollowup/<gameid>/<qnum>")
def followup_host_page(gameid,qnum):
    game=Games.query.filter_by(id=gameid).first()
    oqry="Select followup FROM question WHERE title='"+str(game.questions.split(',')[int(qnum)])+"'"
    q=engine.execute(oqry).fetchall()[0][0]    
    result = []

    for item in q.split("["):
        result.extend(item.split("]"))

    #print(result)
    for i in range(len(result)):
        if i%2==1:
            #print(result[i])
            qry="Select description FROM source WHERE name='"+result[i].strip().lower()+"'"
            content=engine.execute(qry).fetchall()
            if content:
                result[i]="<span><!--"+content[0][0]+"--></span>"
                #result[i]="<small style='display:none'>"+content[0][0]+"</small>"
            else:
                #try:
                    result[i]=int(result[i].strip())
                    oqry="Select hints FROM question WHERE title='"+str(game.questions.split(',')[int(qnum)])+"'"
                    hints=engine.execute(oqry).fetchall()[0][0]            
                    li_list = []
                    start_pos = 0
                    while True:
                        start_li = hints.find("<li>", start_pos)
                        if start_li == -1:
                            break
                        end_li = hints.find("</li>", start_li)
                        li_content = hints[start_li+4:end_li].strip()
                        li_list.append(li_content)
                        start_pos = end_li
                    #print("________________________________________________________________")
                    #print(li_list)
                    result[i]="<span><!--"+li_list[result[i]-1]+"--></span>"
                # except:
                #     result[i]=str(result[i])
    #print(result)
    q = " ".join(result)
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
#     choices=remove_html_tags(engine.execute("Select choices FROM question").fetchall()[int(qnum)][0]).split('\n')[1:-2]
#     answer=(engine.execute("Select correct_choice FROM question").fetchall()[int(qnum)][0])
#     print(answer)
#     return render_template("temp.html",engine=engine,qnum=int(qnum),len=len(choices),choices=choices,answer=answer)
@socketio.on('newc')
def newc(gid):
    #print(gid)
    #print(request.path.split('/')[2])
    players=Players.query.filter_by(game=gid)
    global pnames
    pnames[gid]=[]
    for p in players:
        pnames[gid].append(p.name)
    pnames[gid]=list(set(pnames[gid]))
    global removed
    if gid in removed:
        for i in removed[gid]:
            if i in pnames[gid]:
                pnames[gid].remove(i)
    #numconnected=max(numconnected,len(pnames))
    print(pnames[gid])
    emit('addnewc',{"players": pnames[gid],"gameid":gid},broadcast=True)
@socketio.on('oneanswer')
def oneanswer(data):
    #print("LKJSLKDJFLKSDJFKLSDJFLKSD")
    emit('oneanswer',data,brodcast=True)
@socketio.on('gamehasstarted')
def gamehasstarted(data):
    print('ghs')
    emit('gamehasstarted',data,broadcast=True)

@socketio.on('tleft')
def timeleft(data):
    #print('fasdf')
    emit('tleft',data,broadcast=True)

@socketio.on('timeup')
def timeup(data):
    emit('timeup',data,broadcast=True)

@socketio.on('gotofollowup')
def gotofollowup(data):
    emit('gotofollowup',data,broadcast=True)

@socketio.on('gotolb')
def gotolb(data):
    emit('gotolb',data,broadcast=True)

@socketio.on('gotonextq')
# def gotonextq(data):
#     game=Games.query.filter_by(id=data["gid"]).first()
#     #print(data["qon"],len(game.questions.split(','))-2)
#     if int(data["qon"])==len(game.questions.split(','))-2:
#         emit('gotofinal',data["gid"],broadcast=True)
#     else:
#         emit('gotonextq',data["gid"],broadcast=True)
def gotonextq(data):
    emit('gotonextq',data,broadcast=True)

@socketio.on('gotofinal')
def gotofinal(data):
    emit('gotofinal',data,broadcast=True)
