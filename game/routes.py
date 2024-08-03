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
fout=open("/private/tmp/flaskout",'a')
#from game.load import engine
import game.dbModel, game.forms
from flask import render_template, redirect,url_for, flash, request, session
from game.models import *
from game.forms import JoinForm,StartGameForm,SubmitAnswerForm
from game import db,socketio,app
from game.models import Games,Players
from sqlalchemy import Column, Integer, Float, Date, String, VARCHAR, select, MetaData,ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine, delete, func
from sqlalchemy.orm import sessionmaker
from flask_login import login_user,logout_user, login_required, current_user
import random
from flask_socketio import SocketIO,send, emit
from engineio.payload import Payload
import time,os,sys
from sqlalchemy.orm  import DeclarativeBase,Mapped,mapped_column,Session
import bs4


class Base(DeclarativeBase):
    pass

class Game(Base):
    __tablename__ = "game"
    game_id = Column(Integer, primary_key=True)
    game_name = Column(String(100))
    game_status = Column(String(100))
    game_group = Column(String(100))
    game_description = Column(String(100))

class GameCategory(Base):
    __tablename__ = "game_category"
    game_category_id = Column(Integer, primary_key=True)
    game_id = Column(Integer, ForeignKey('game.game_id'))
    gc_categories = Column(String(100))
    no_questions = Column(Integer)


Payload.max_decode_packets = 1000
removed={}
numconnected={}
numanswered={}
pnames={}
currentgame={}
current={}





TURSO_DATABASE_URL = os.environ.get("TURSO_DATABASE_URL")
TURSO_AUTH_TOKEN = os.environ.get("TURSO_AUTH_TOKEN")

dbUrl = f"sqlite+{TURSO_DATABASE_URL}/?authToken={TURSO_AUTH_TOKEN}&secure=true"

try:
    engine = create_engine(dbUrl, connect_args={'check_same_thread': False}, echo=True)
except:
    print("Can't create engine")

Session = sessionmaker(bind=engine)
session = Session()
# session = Session(engine)


#select game.game_group, game.game_name, game.game_description, GameCategory.no_questions from
#game join game_category on game.game_name = game_category.game where game.game_status = 'Production'
#and game.game_group is not null order by game_group, name limit 4

query = session.query(Game, GameCategory) \
    .join(GameCategory, Game.game_id == GameCategory.game_id) \
    .filter(Game.game_status == 'Production') \
    .filter(Game.game_group.isnot(None)) \
    .order_by(Game.game_group, Game.game_name) \
    .limit(20)

# Execute the query and fetch all results
results = query.all()
# Print the results
for game, category in results:
    print(f"Game: {game.game_name}, Category: {category.gc_categories}, Number of Question: {category.no_questions}")

# try:
#     engine = create_engine(
#         'postgresql://postgres.cqxvknmoofzuhxbonmoj:princely-tunic-670@aws-0-us-west-1.pooler.supabase.com:5432/postgres',echo=False)


def clean(html_code):

    soup = BeautifulSoup(html_code, 'html.parser')

    # Find all the <li> elements within the <ol> tag
    list_items = soup.find('ol').find_all('li')

    # Extract the text content from the <li> elements
    result = [item.text for item in list_items]

    return(result)
def remove_html_tags(text):
    """Remove html tags from a string"""
    import re
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text)



def hintsandsources(q,gameid,qnum):
    result = []

    for item in q.split("["):
        result.extend(item.split("]"))

    for i in range(len(result)):
        if i%2==1:
            qry="Select description FROM source WHERE name='"+result[i].strip().lower()+"'"
            content=engine.execute(qry).fetchall()
            if content:
                result[i]="<span><!--"+content[0][0]+"--></span>"
                #result[i]="<small style='display:none'>"+content[0][0]+"</small>"
            else:
                #try:
                    result[i]=int(result[i].strip())
                    hints=current[gameid][4][int(qnum)]
                    #oqry="Select hints FROM question WHERE title='"+(str(game.questions.split(',')[int(qnum)])).replace("'","''")+"'"
                    #hints=engine.execute("Select hints FROM question WHERE title LIKE '%%"+(str(game.questions.split(',')[int(qnum)])).replace("'","''")+"%%'").fetchall()[0][0]            
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
                    result[i]="<span><!--"+li_list[result[i]-1]+"--></span>"
                #except:
                    result[i]=str(result[i])
    q = " ".join(result)
    return q
@app.route("/")
@app.route("/home")
def index():
    return render_template("index.html")
@app.route("/players")
def player():
    return render_template("players.html")
@app.route("/aboutus")
def aboutus():
    return render_template("aboutus.html")
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
playerscore={}
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
currentquestion={}
totalcurrentchoice={}
@app.route("/questionhost/<gameid>/<qnum>",methods=["GET","POST"])
def question_host_page(gameid,qnum):
    global current
    global numanswered
    global pnames
    game=Games.query.filter_by(id=gameid).first()
    # q=engine.execute("Select question_content FROM question WHERE title LIKE '%%"+(str(game.questions.split(',')[int(qnum)])).replace("'","''")+"%%'").fetchall()[0][0]
    # choices=engine.execute("Select choices FROM question WHERE title LIKE '%%"+(str(game.questions.split(',')[int(qnum)])).replace("'","''")+"%%'").fetchall()[0][0].split('\n')

    # #oqry="Select question_content FROM question WHERE title='"+str(game.questions.split(',')[int(qnum)])+"'"
    # #q=engine.execute(oqry).fetchall()[0][0]
      # #q=engine.execute(oqry).fetchall()[0][0]
    q=current[gameid][0][int(qnum)]
    # result = []

    # for item in q.split("["):
    #     result.extend(item.split("]"))

    # for i in range(len(result)):
    #     if i%2==1:
    #         qry="Select description FROM source WHERE name='"+result[i].strip().lower()+"'"
    #         content=engine.execute(qry).fetchall()
    #         if content:
    #             result[i]="<span><!--"+content[0][0]+"--></span>"
    #             #result[i]="<small style='display:none'>"+content[0][0]+"</small>"
    #         else:
    #             try:
    #                 result[i]=int(result[i].strip())
    #                 hints=current[gameid][4][int(qnum)]
    #                 #oqry="Select hints FROM question WHERE title='"+(str(game.questions.split(',')[int(qnum)])).replace("'","''")+"'"
    #                 #hints=engine.execute("Select hints FROM question WHERE title LIKE '%%"+(str(game.questions.split(',')[int(qnum)])).replace("'","''")+"%%'").fetchall()[0][0]            
    #                 li_list = []
    #                 start_pos = 0
    #                 while True:
    #                     start_li = hints.find("<li>", start_pos)
    #                     if start_li == -1:
    #                         break
    #                     end_li = hints.find("</li>", start_li)
    #                     li_content = hints[start_li+4:end_li].strip()
    #                     li_list.append(li_content)
    #                     start_pos = end_li
    #                 result[i]="<span><!--"+li_list[result[i]-1]+"--></span>"
    #             except:
    #                 result[i]=str(result[i])
    # q = " ".join(result)
    q=hintsandsources(q,gameid,qnum)
    
    return render_template("questionhost.html",engine=engine,qnum=int(qnum),q=q,
    game=game,numconnected=numconnected[gameid],pnames=pnames[gameid],numanswered=numanswered[gameid],code=game.code,choices=clean(current[gameid][2][int(qnum)]),total=len(current[gameid][0]))

# @app.route("/singlequestion/<qnum>",methods=["GET","POST"])
# def question_page(qnum):
#     choices=remove_html_tags(engine.execute("Select choices FROM question").fetchall()[int(qnum)][0]).split('\n')[1:-2]
#     answer=(engine.execute("Select correct_choice FROM question").fetchall()[int(qnum)][0])
#     return render_template("question2.html",engine=engine,qnum=int(qnum),len=len(choices),choices=choices,answer=answer)

@app.route("/followup/<qnum>",methods=["GET","POST"])
def followup(qnum):
    return render_template("followup.html",engine=engine,qnum=int(qnum))


@app.route("/question/<playerid>/<gameid>/<qnum>",methods=["GET","POST"])
def multiquestion_page(playerid,gameid,qnum):
    global current
    form=SubmitAnswerForm()
    qnum=int(qnum)
    game=Games.query.filter_by(id=gameid).first()
    player=Players.query.filter_by(id=int(playerid)).first()
    # oqry="Select correct_choice FROM question WHERE title=%s"
    # try:
    #     question_title = game.questions.split(',')[qnum]#.replace("'", "")
    #     corrans=engine.execute(oqry,(question_title)).fetchall()[0][0]-1

    # except:
    #     pass
    #oqry="Select correct_choice FROM question WHERE title='"+question_title+"'"
    if request.method=="POST" and request.form.get("timeleft") is not None:
        timel=float(request.form.get("timeleft"))
        ans=request.form.get("choice")
        if ans is None or timel==0:
            ans=""
        player.submission+=(ans+';')
        corrans=current[gameid][3][int(qnum)]
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
    # oqry="Select question_content FROM question WHERE title=%s"
    # #oqry="Select question_content FROM question WHERE title='"+str(game.questions.split(',')[int(qnum)])+"'"
    # #q=engine.execute(oqry).fetchall()[0][0]
    q=current[gameid][0][int(qnum)]
    q=hintsandsources(q,gameid,qnum)
    # result = []
    # # try:
    # #     q=engine.execute(oqry,(str(game.questions.split(',')[int(qnum)]))).fetchall()[0][0]
    # for item in q.split("["):
    #     result.extend(item.split("]"))
    # # except:
    # #     pass
    

    

    # for i in range(len(result)):
    #     if i%2==1:
    #         qry="Select description FROM source WHERE name='"+result[i].strip().lower()+"'"
    #         content=engine.execute(qry).fetchall()
    #         if content:
    #             result[i]="<span><!--"+content[0][0]+"--></span>"
    #             #result[i]="<small style='display:none'>"+content[0][0]+"</small>"
    #         else:
    #             try:
    #                 result[i]=int(result[i].strip())
    #                 #oqry="Select hints FROM question WHERE title='"+str(game.questions.split(',')[int(qnum)])+"'"
    #                 #hints=engine.execute(oqry).fetchall()[0][0]            
    #                 li_list = []
    #                 start_pos = 0
    #                 while True:
    #                     start_li = hints.find("<li>", start_pos)
    #                     if start_li == -1:
    #                         break
    #                     end_li = hints.find("</li>", start_li)
    #                     li_content = hints[start_li+4:end_li].strip()
    #                     li_list.append(li_content)
    #                     start_pos = end_li
    #                 result[i]="<span><!--"+li_list[result[i]-1]+"--></span>"
    #             #except:
    #                 result[i]=str(result[i])
    # q = " ".join(result)
    # currentchoice.pop(0)
    # currentchoice.pop(len(currentchoice)-1)
    return render_template("question.html",engine=engine,qnum=int(qnum),form=form,q=q
    ,player=player,game=game,playerid=playerid,currentchoice=clean(current[gameid][2][int(qnum)]),total=len(current[gameid][0]))

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
    try:
        db.session.execute(deleted_objects)
        db.session.commit()
        deleted_objects = Games.__table__.delete().where(Games.starttime<=time.time()-3600)
        db.session.execute(deleted_objects)
        db.session.commit()
    except:
        pass
    if form.validate_on_submit():

        if request.form.get("game_choice"):
            try:
                print(session["handles"])
            except:
                session["handles"]=[]
            
            session.modified = True
            if Games.query.filter_by(code=form.code.data) and form.code.data in session["handles"]:
                update_statement = Games.__table__.update().where(Games.code==form.code.data).values(code="")
                db.session.execute(update_statement)
                db.session.commit()
                #deleted_objects = Players.__table__.delete().where(str(func.delete_players_helper(Players.game))==str(form.code.data))
                #a=db.session.execute(deleted_objects)
                #db.session.commit()
                #deleted_objects = Games.__table__.delete().where(Games.code==form.code.data)

                #db.session.execute(deleted_objects)
                #db.session.commit()
            session["handles"].append(form.code.data)
            gamechoice = str(request.form.get("game_choice"))
            print(gamechoice)

            qry="Select * FROM game_category WHERE game='"+gamechoice+"'"
            gamerow=engine.execute(qry).fetchall()[0]
            qry="Select title FROM question WHERE categories LIKE '%%"+gamerow[6]+"%%'" ##might need to change to gamerow[1]
            pqs=list(engine.execute(qry).fetchall())
            qs=random.sample(pqs,gamerow[2])
            qstr=""
            for element in qs:
                qstr+=(str(element[0])+",")
            code = form.code.data
            
            #     code = random.randint(100000, 999999)
            db.session.add(Games(game=gamechoice,code=code,time=0,questions=qstr, starttime=time.time()))
            db.session.commit()
            gameid=str(Games.query.filter_by(code=code).first().id)
            global curentgame
            currentgame[gameid]=gamechoice
            nl="/waiting/host/"+str(Games.query.filter_by(code=code).first().id)
            return redirect(nl)
        else:
    
            flash("Please choose a game.",category="danger")
    if form.errors!={}:
        # for err_msg in form.errors.values():
        #     flash(f'{err_msg}', category='danger')
        flash("This code is already in use. Please choose a different code.",category="danger")
    dict1={}
    arr=[[]]
    arr1=["Civics","News","Voting"]
    arr.append(['Play a Demo','LWV Demo','asdfa',4])
    
    query = session.query(Game, GameCategory) \
        .join(GameCategory, Game.game_id == GameCategory.game_id) \
        .filter(Game.game_status == 'Production') \
        .filter(Game.game_group.isnot(None)) \
        .order_by(Game.game_group, Game.game_name)
    # Execute the query and fetch all results
    results = query.all()
    pass_to_start=[]
    for game,category in results:
        pass_to_start.append([game.game_group,game.game_name,category.no_questions])
    common_names={}
    for i in pass_to_start:
        if i[0]+i[1] not in common_names:
            common_names[i[0]+i[1]]=i[2]
        else:
            common_names[i[0]+i[1]]+=i[2]
    done=set()
    pass_final=[]
    for i in pass_to_start:
        if i[0]+i[1] not in done:
            done.add(i[0]+i[1])
            pass_final.append([i[0],i[1],common_names[i[0]+i[1]]])
    pass_to_start=pass_final
    # for i in results:
    #     if i[1] in dict1:
    #         dict1[i[1]]+=i[3]
    #     else:
    # for i in results:
    #     if i[1] in dict1:
    #         dict1[i[1]]+=i[3]
    #     else:
    #         dict1[i[1]]=i[3]
    # visited=[]
    # for i in results:
    #     if i[0] in arr1:
    #         if i[1] not in visited:
    #             visited.append(i[1])
    #             arr.append([i[0],i[1],i[2],dict1[i[1]]])
    # for i in results:
    #     if i[0] not in arr1:
    #         if i[1] not in visited:
    #             visited.append(i[1])
    #             arr.append([i[0],i[1],i[2],dict1[i[1]]])

    # arr3=[]
    # for i in range(len(arr)):
    #     if len(arr[i])==0:
    #         arr3.append(i)
    # for i in arr3:
    #     arr.pop(i)
    return render_template("start.html",engine=engine,form=form,arr=pass_to_start)
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
    if form.submit.data:
        pass
    currentchoice=[]
    global currentgame
    global currentquestion
    q1=[]
    followup=[]
    correct=[]
    hint=[]
    global current
    for i in engine.execute("select DISTINCT categories, no_questions from game_category where game = '"+currentgame[id]+"' and no_questions > 0").fetchall():
        for j in engine.execute("select * from(select DISTINCT title, question_content, followup, choices, correct_choice, hints, bug_path_name,text_color,background_color,'class' from question q, game_category gc where gc.categories = '"+i[0]+"' and game = '"+currentgame[id]+"' and status = 'Production' and  array_remove(regexp_split_to_array(lower(btrim(gc.categories, ' ')), '[;|:]\s*'), '') <@ array_remove(regexp_split_to_array(lower(btrim(q.categories,  ' ')), '[;|:]\s*'), '')) as c order by random() limit '"+str(i[1])+"'").fetchall():
            q1.append(j[1])
            currentchoice.append(j[3])
            correct.append(j[4]-1)
            followup.append(j[2])
            hint.append(j[5])
    current[id]=[q1,followup,currentchoice,correct,hint] 
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
    global current
    game=Games.query.filter_by(id=gameid).first()
    # oqry="Select correct_choice FROM question WHERE title='"+str(game.questions.split(',')[qnum])+"'"
    # corrans=engine.execute(oqry).fetchall()[0][0]-1
    # oqry="Select choices FROM question WHERE title='"+str(game.questions.split(',')[qnum])+"'"
    subnums=[0]*len(current[gameid][0])
    for player in Players.query.filter_by(game=gameid):
        try:
            if player.submission.split(';')[qnum]!="":
                subnums[int(player.submission.split(';')[qnum])]+=1
        except:
            global numconnected
            global removed
   
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

    pans=(Players.query.filter_by(id=playerid).first().submission.split(';')[-2])
    if pans!="":
        pans=int(pans)
    # qry="Select question_content FROM question WHERE title='"+game.questions.split(',')[qnum]+"'"
    # #HINTS AND SOURCES
    # q=engine.execute(qry).fetchall()[0][0]
    q=current[gameid][0][int(qnum)]

    # result = []

    # for item in q.split("["):
    #     result.extend(item.split("]"))

    # for i in range(len(result)):
    #     if i%2==1:
    #         qry="Select description FROM source WHERE name='"+result[i].strip().lower()+"'"
    #         content=engine.execute(qry).fetchall()
    #         if content:
    #             result[i]="<span><!--"+content[0][0]+"--></span>"
    #             #result[i]="<small style='display:none'>"+content[0][0]+"</small>"
    #         else:
    #             #try:
    #                 result[i]=int(result[i].strip())
    #                 #oqry="Select hints FROM question WHERE title='"+str(game.questions.split(',')[int(qnum)])+"'"
    #                 #hints=engine.execute(oqry).fetchall()[0][0]            
    #                 li_list = []
    #                 start_pos = 0
    #                 while True:
    #                     start_li = hints.find("<li>", start_pos)
    #                     if start_li == -1:
    #                         break
    #                     end_li = hints.find("</li>", start_li)
    #                     li_content = hints[start_li+4:end_li].strip()
    #                     li_list.append(li_content)
    #                     start_pos = end_li
    #                 result[i]="<span><!--"+li_list[result[i]-1]+"--></span>"
    #             # except:
    #             #     result[i]=str(result[i])
    # q = " ".join(result)
    q=hintsandsources(q,gameid,qnum)
    # if pans!="":
    #         if int(pans)==corrans:
    #             player.score+=float(request.form.get("timeleft"))*10
    #             player.streak+=1
    #             player.result+="1;"
    #         else:
    #             player.streak=0
    #             player.result+="0;"
    # else:
    #     player.streak=0
    #     player.result+="0;"
    # db.session.commit()
    return render_template("resultplayer.html",player=Players.query.filter_by(id=playerid).first(),game=game,qnum=int(qnum)
    ,corrans=current[gameid][3][int(qnum)],choices=clean(current[gameid][2][int(qnum)])
    ,subnums=subnums,pans=pans,engine=engine,q=q,playerid=playerid)

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
    global current
    return render_template("leaderboardhost.html",ps=ps,game=Games.query.filter_by(id=gameid).first(),qnum=int(qnum),totalquestions=len(game.questions.split(','))-2,code=game.code,totalnum=len(current[gameid][0])-1)

@app.route("/playerfollowup/<playerid>/<gameid>/<qnum>")
def followup_player_page(playerid,gameid,qnum):
    game=Games.query.filter_by(id=gameid).first()
    # oqry="Select followup FROM question WHERE title='"+str(game.questions.split(',')[int(qnum)])+"'"
    # q=engine.execute(oqry).fetchall()[0][0]
    q=current[gameid][1][int(qnum)]

    # result = []

    # for item in q.split("["):
    #     result.extend(item.split("]"))

    # for i in range(len(result)):
    #     if i%2==1:
    #         qry="Select description FROM source WHERE name='"+result[i].strip().lower()+"'"
    #         content=engine.execute(qry).fetchall()
    #         if content:
    #             result[i]="<span><!--"+content[0][0]+"--></span>"
    #             #result[i]="<small style='display:none'>"+content[0][0]+"</small>"
    #         else:
    #             try:
    #                 result[i]=int(result[i].strip())
    #                 oqry="Select hints FROM question WHERE title='"+str(game.questions.split(',')[int(qnum)])+"'"
    #                 hints=engine.execute(oqry).fetchall()[0][0]            
    #                 li_list = []
    #                 start_pos = 0
    #                 while True:
    #                     start_li = hints.find("<li>", start_pos)
    #                     if start_li == -1:
    #                         break
    #                     end_li = hints.find("</li>", start_li)
    #                     li_content = hints[start_li+4:end_li].strip()
    #                     li_list.append(li_content)
    #                     start_pos = end_li
    #                 result[i]="<span><!--"+li_list[result[i]-1]+"--></span>"
    #             except:
    #                 result[i]=str(result[i])
    # q = " ".join(result)
    q=hintsandsources(q,gameid,qnum)
    return render_template("followupplayer.html",engine=engine,q=q,playerid=playerid,gameid=gameid,qnum=qnum,game=game)

@app.route("/resulthost/<gameid>/<qnum>")
def host_result_page(gameid,qnum):
    global numanswered
    numanswered[id]=0
    qnum=int(qnum)
    game=Games.query.filter_by(id=gameid).first()
    # oqry="Select correct_choice FROM question WHERE title='"+str(game.questions.split(',')[qnum])+"'"
    # # corrans=engine.execute(oqry).fetchall()[0][0]-1
    # oqry="Select choices FROM question WHERE title='"+str(game.questions.split(',')[qnum])+"'"
    # subnums=[0]*len(engine.execute(oqry).fetchall()[0][0].split("\n"))
    global current
    subnums=[0]*len(clean(current[gameid][2][int(qnum)]))
    for player in Players.query.filter_by(game=gameid):
        try:
            if player.submission.split(';')[qnum]!="":
                subnums[int(player.submission.split(';')[qnum])]+=1
        except:
            global numconnected
            global removed
           
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
    # qry="Select question_content FROM question WHERE title='"+game.questions.split(',')[qnum]+"'"
    #HINTS AND SOURCES
    # q=engine.execute(qry).fetchall()[0][0]
    q=current[gameid][0][int(qnum)]

    # result = []

    # for item in q.split("["):
    #     result.extend(item.split("]"))

    # for i in range(len(result)):
    #     if i%2==1:
    #         qry="Select description FROM source WHERE name='"+result[i].strip().lower()+"'"
    #         content=engine.execute(qry).fetchall()
    #         if content:
    #             result[i]="<span><!--"+content[0][0]+"--></span>"
    #             #result[i]="<small style='display:none'>"+content[0][0]+"</small>"
    #         else:
    #             try:
    #                 result[i]=int(result[i].strip())
    #                 #oqry="Select hints FROM question WHERE title='"+str(game.questions.split(',')[int(qnum)])+"'"
    #                 #hints=engine.execute(oqry).fetchall()[0][0]            
    #                 li_list = []
    #                 start_pos = 0
    #                 while True:
    #                     start_li = hints.find("<li>", start_pos)
    #                     if start_li == -1:
    #                         break
    #                     end_li = hints.find("</li>", start_li)
    #                     li_content = hints[start_li+4:end_li].strip()
    #                     li_list.append(li_content)
    #                     start_pos = end_li
    #                 result[i]="<span><!--"+li_list[result[i]-1]+"--></span>"
    #             except:
    #                  result[i]=str(result[i])
    # q = " ".join(result)
    q=hintsandsources(q,gameid,qnum)
    
    return render_template("resulthost.html",game=game,qnum=int(qnum),q=q
    ,corrans=current[gameid][3][int(qnum)],choices=clean(current[gameid][2][int(qnum)]),engine=engine,code=game.code,subnums=subnums)

@app.route("/hostfollowup/<gameid>/<qnum>")
def followup_host_page(gameid,qnum):
    game=Games.query.filter_by(id=gameid).first()
    # oqry="Select followup FROM question WHERE title='"+str(game.questions.split(',')[int(qnum)])+"'"
    # q=engine.execute(oqry).fetchall()[0][0] 
    q=current[gameid][1][int(qnum)]
  
    # result = []

    # for item in q.split("["):
    #     result.extend(item.split("]"))

    # for i in range(len(result)):
    #     if i%2==1:
    #         qry="Select description FROM source WHERE name='"+result[i].strip().lower()+"'"
    #         content=engine.execute(qry).fetchall()
    #         if content:
    #             result[i]="<span><!--"+content[0][0]+"--></span>"
    #             #result[i]="<small style='display:none'>"+content[0][0]+"</small>"
    #         else:
    #             try:
    #                 result[i]=int(result[i].strip())
    #                 oqry="Select hints FROM question WHERE title='"+str(game.questions.split(',')[int(qnum)])+"'"
    #                 hints=engine.execute(oqry).fetchall()[0][0]            
    #                 li_list = []
    #                 start_pos = 0
    #                 while True:
    #                     start_li = hints.find("<li>", start_pos)
    #                     if start_li == -1:
    #                         break
    #                     end_li = hints.find("</li>", start_li)
    #                     li_content = hints[start_li+4:end_li].strip()
    #                     li_list.append(li_content)
    #                     start_pos = end_li
    #                 
    #                 result[i]="<span><!--"+li_list[result[i]-1]+"--></span>"
    #             except:
    #                 result[i]=str(result[i])
    # q = " ".join(result)
    q=hintsandsources(q,gameid,qnum)
    #global current
    return render_template("followuphost.html",q=q,game=Games.query.filter_by(id=gameid).first(),qnum=int(qnum),code=game.code)

@app.route("/podium/<gameid>")
def podium_page(gameid):
    ps=Players.query.filter_by(game=gameid).order_by(Players.score.desc())
    return render_template("podium.html",ps=ps,game=Games.query.filter_by(id=gameid).first())

# @socketio.on('text')
# def text(data):
#     emit('print',data)
# @app.route("/question/<qnum>",methods=["GET","POST"])
# def question_page(qnum):
#     choices=remove_html_tags(engine.execute("Select choices FROM question").fetchall()[int(qnum)][0]).split('\n')[1:-2]
#     answer=(engine.execute("Select correct_choice FROM question").fetchall()[int(qnum)][0])
#     return render_template("temp.html",engine=engine,qnum=int(qnum),len=len(choices),choices=choices,answer=answer)
@socketio.on('newc')
def newc(gid):
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
    emit('addnewc',{"players": pnames[gid],"gameid":gid},broadcast=True)
@socketio.on('oneanswer')
def oneanswer(data):
    emit('oneanswer',data,brodcast=True)
@socketio.on('gamehasstarted')
def gamehasstarted(data):
    emit('gamehasstarted',data,broadcast=True)

@socketio.on('tleft')
def timeleft(data):
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
#     if int(data["qon"])==len(game.questions.split(','))-2:
#         emit('gotofinal',data["gid"],broadcast=True)
#     else:
#         emit('gotonextq',data["gid"],broadcast=True)
def gotonextq(data):
    emit('gotonextq',data,broadcast=True)

@socketio.on('gotofinal')
def gotofinal(data):
    emit('gotofinal',data,broadcast=True)
