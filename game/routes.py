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
from bs4 import BeautifulSoup



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

class Question(Base):
    __tablename__ = "question"
    question_id = Column(Integer, primary_key=True)
    title = Column(String(100))
    question_categories = Column(String(100))
    question_content=Column(String(100))
    followup=Column(String(100))
    choices=Column(String(100))
    correct_choice=Column(Integer)
    hints=Column(String(100))

class Games(Base):
    __tablename__ = "Games"
    id = Column(Integer, primary_key=True)
    game=db.Column(db.String())
    questions=db.Column(db.String())
    code = db.Column(db.String(), nullable=False)
    time = db.Column(db.Integer())
    starttime=db.Column(db.Integer(),)
    # players=db.relationship('Players',backref='owned_game',lazy=True,cascade='all,delete')


class Players(Base):
    __tablename__ = "Players"
    id=db.Column(db.Integer(),primary_key=True)
    name=db.Column(db.String())
    score=db.Column(db.Integer())
    # game_id=db.Column(db.Integer(),db.ForeignKey('Games.id'))
    game_id=db.Column(db.Integer())
    streak=db.Column(db.Integer())
    result=db.Column(db.String())
    submission=db.Column(db.String())

class Source(Base):
    __tablename__ = "source"
    source_id=db.Column(db.String(),primary_key=True)
    name=db.Column(db.String())
    description=db.Column(db.String())
    hints=db.Column(db.String())


# class Games(Base):
#     __tablename__ = "Games"
#     id = Column(Integer, primary_key=True)
#     game = db.Column(db.String())
#     questions = db.Column(db.String())
#     code = db.Column(db.String(), nullable=False)
#     time = db.Column(db.Integer())
#     starttime = db.Column(db.Integer())
#     players = db.relationship('Players', backref='owned_game', lazy=True, cascade='all,delete')

# class Players(Base):
#     id = db.Column(db.Integer(), primary_key=True)
#     name = db.Column(db.String(length=15))
#     score = db.Column(db.Integer())
#     game_id = db.Column(db.Integer(), db.ForeignKey('(link unavailable)'))
#     streak = db.Column(db.Integer())
#     result = db.Column(db.String())
#     submission = db.Column(db.String())
#     owned_game = db.relationship("Games", backref="players")





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
dbSession = Session()
# session = Session(engine)


#select game.game_group, game.game_name, game.game_description, GameCategory.no_questions from
#game join game_category on game.game_name = game_category.game where game.game_status = 'Production'
#and game.game_group is not null order by game_group, name limit 4

query = dbSession.query(Game, GameCategory) \
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


#FIXFIXFIXFIXFIXFIXFIX
def hintsandsources(q,gameid,qnum):
    result = []

    for item in q.split("["):
        result.extend(item.split("]"))

    for i in range(len(result)):
        if i%2==1:
            fout.write(f"thisiscontent:{result}")
            fout.flush()
            content=dbSession.query(Source).filter(Source.description==result[i].strip().lower()).first()
            # qry="Select description FROM source WHERE name='"+result[i].strip().lower()+"'"
            # content=engine.execute(qry).fetchall()
            if content:
                result[i]="<span><!--"+content.name+"--></span>"
                #result[i]="<small style='display:none'>"+content[0][0]+"</small>"
            else:
                try:
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
                except:
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
        code=form.code.data
        fout.write("\n")
        fout.write("thisisthecode: "+code+"\n")
        fout.flush()
        if dbSession.query(Games).filter(Games.code==code).count()==0:
            flash("Invalid Code.",category="danger")
        else:
            game_id=dbSession.query(Games).filter(Games.code==code).first().id
            if dbSession.query(Players).filter(Players.name==form.name.data,Players.game_id==game_id).count()!=0:
                flash("Name already in use. Please choose another name.", category="danger")
            else:
                player_id=random.randint(100000, 999999)
                new_player = Players(
                id=player_id,
                name=form.name.data,
                score=0,
                game_id=game_id,
                streak=0,
                result='',
                submission=''
                )
                dbSession.add(new_player)
                dbSession.commit()

                newlink="/waiting/"+str(player_id)+"/"+\
                        str(game_id)
                return redirect(newlink)
    return render_template("join.html",form=form)
# def join_page():
#     form=JoinForm()
#     if form.submit.data and form.validate():
#         if Games.query.filter_by(code=form.code.data).count()==0:
#             flash("Invalid code",category="danger")
#         elif Players.query.filter_by(name=form.name.data,game=Games.query.filter_by(code=form.code.data).first().id).count()!=0:
#             flash("Name already in use. Please choose another name.", category="danger")
#         else:
#             db.dbSession.add(Players(name=form.name.data,score=0,game=Games.query.filter_by(code=form.code.data).first().id
#                                ,streak=0,submission="",result=""))
#             db.dbSession.commit()
#             newlink="/waiting/"+str(Players.query.filter_by(name=form.name.data,game=Games.query.filter_by(code=form.code.data).first().id).first().id)+"/"+\
#                     str(Games.query.filter_by(code=form.code.data).first().id)
#             return redirect(newlink)
#     return render_template("join.html",form=form)
playerscore={}
@app.route("/waiting/<playerid>/<gameid>")
def waiting_page(playerid,gameid):
    global pnames
    global numconnected
    if gameid not in numconnected:
        numconnected[gameid]=1
    else:
        numconnected[gameid]+=1
    return render_template("waitscreenplayer.html",game=dbSession.query(Games).filter(Games.id==gameid).first()
    ,player=dbSession.query(Players).filter(Players.id==playerid).first(),pnames=pnames[gameid],playerid=playerid)
currentquestion={}
totalcurrentchoice={}
@app.route("/questionhost/<gameid>/<qnum>",methods=["GET","POST"])
def question_host_page(gameid,qnum):
    global current
    global numanswered
    global pnames
    game=dbSession.query(Games).filter(Games.id==gameid).first()
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
    player=dbSession.query(Players).filter(Players.id==int(playerid)).first()
    game=dbSession.query(Games).filter(Games.id==int(gameid)).first()
    # player=Players.query.filter_by(id=int(playerid)).first()
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
        dbSession.commit()
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
        
        return Games.query.filter(id=pg).first().code
    except:
        return ""
def delete_players_helper1(pg):
    try:

        return Games.query.filter_by(id=pg).first().starttime
    except:
        return 100000000000

def question_query(superset,question_set):
    question_set=split_question(question_set)
    for i in question_set:
        if i not in superset:
            return False
    return True

def split_question(question_cat):
    res=[]
    question_cat=question_cat.replace(':',';').split(';')
    for cat in question_cat:
        if cat!='':
            if cat[0]==' ':
                res.append(cat[1:].lower())
            else:
                res.append(cat.lower())
    res=list(set(res))
    return res

@app.route('/start',methods=["GET","POST"])
def start_page():
    form=StartGameForm()
    fout.flush() 
    
    try:
        deleted_objects = Players.__table__.delete().where(float(delete_players_helper1(Players.game))<=time.time()-3600)
        db.dbSession.execute(deleted_objects)
        db.dbSession.commit()
        deleted_objects = Games.__table__.delete().where(Games.starttime<=time.time()-3600)
        db.dbSession.execute(deleted_objects)
        db.dbSession.commit()
    except:
        pass
    if form.validate_on_submit():
        if request.form.get("game_choice"):
            gamechoice = str(request.form.get("game_choice"))
            query = dbSession.query(Game, GameCategory) \
            .join(GameCategory, Game.game_id == GameCategory.game_id) \
            .filter(Game.game_status == 'Production') \
            .filter(Game.game_name == gamechoice) \
            .filter(Game.game_group.isnot(None)) \
            .order_by(Game.game_group, Game.game_name)
            
            results = query.all()
            total_questions=0
            for game, category in results:
                print(f"Game: {game.game_name}, Category: {game.game_group}, Number of Question: {category.no_questions},{category.gc_categories}")
            superset=[]
            catarr=[]
            for game,category in results:
                catarr.append(category.gc_categories) 
                total_questions+=category.no_questions  
            print(catarr)
            print("hello")

            query = dbSession.query(Question.question_categories, Question.question_id)\
            .order_by(func.random())

            results=query.all()
            
            question_arr=[]
            for question in results:
                arr=question.question_categories.lower().replace(':', ';').split(';')
                arr = list(map(str.strip, arr))
            
                #print(arr)
                found=0
                for cat in catarr:
                    catelements=cat.lower().replace(':', ';').split(';')
                    catelements = list(map(str.strip, catelements))
                    for catelement in catelements:
                        if catelement in arr:
                            found=1
                        else:
                            found=0
                            break
                    if found==1:
                        question_arr.append(question.question_id)
            random.shuffle(question_arr)
            question_arr=question_arr[:total_questions]
            qstr=''
            for i in question_arr:
                qstr+=i+','
            qstr=qstr[:-1]
            code1 = form.code.data
            game_id=random.randint(1, 1000000000) #come up with better solution to avoid collisions
            new_game = Games(
                id=game_id,
                game=gamechoice,
                questions=qstr,
                code=code1,
                time=0,
                starttime=time.time()
            )
            dbSession.add(new_game)

            # Commit the transaction
            dbSession.commit()




            fout.write(gamechoice)
            # if request.form.get("game_choice"):
            #     try:
            #         print(session.get("handles"))
            #     except:
            #         handles = session.get("handles", [])
            # query = dbSession.query(Game, GameCategory) \
            # .join(GameCategory, Game.game_id == GameCategory.game_id) \
            # .filter(Game.game_status == 'Production') \
            # .filter(Game.game_name == gamechoice) \
            # .filter(Game.game_group.isnot(None)) 
            # total_questions=0
            #     # Execute the query and fetch all results
            # results = query.all()
            # superset=[]
            # for game,category in results:
            #     total_questions+=category.no_questions
            #     curr_cat=category.gc_categories
            #     curr_cat_final=split_question(curr_cat)
            #     for cat in curr_cat_final:
            #         superset.append(cat)
            # print(f'total:{total_questions}')
            # superset=set(superset)
            # print(f'spuerset:{superset}')
            # result = dbSession.query(Question)\
            # .filter(question_query(superset, str(Question.question_categories)))\
            # .order_by(func.random())\
            # .limit(total_questions).all()
            # qstr=""
            # for question in result:
            #     qstr+=(str(question.title)+",")
            # fout.write(f'question:{qstr}')
            # # db.session.add(Games(game=gamechoice,code=code,time=0,questions=qstr, starttime=time.time()))
            # # db.session.commit()
            # fout.write("\n")
            # fout.flush()




            # session.modified = True
            # handles = session.get("handles", [])
            # if Games.query.filter_by(code=form.code.data) and form.code.data in session.get("handles",[]):
            #     update_statement = Games.__table__.update().where(Games.code==form.code.data).values(code="")
            #     db.dbSession.execute(update_statement)
            #     db.dbSession.commit()
            #     #deleted_objects = Players.__table__.delete().where(str(func.delete_players_helper(Players.game))==str(form.code.data))
            #     #a=db.session.execute(deleted_objects)
            #     #db.session.commit()
            #     #deleted_objects = Games.__table__.delete().where(Games.code==form.code.data)

            #     #db.session.execute(deleted_objects)
            #     #db.session.commit()
            # handles.append(form.code.data)
            # session["handles"] = handles
            # session["handles"].append(form.code.data)


            

            # qry="Select * FROM game_category WHERE game='"+gamechoice+"'"
            # gamerow=engine.execute(qry).fetchall()[0]
            # qry="Select title FROM question WHERE categories LIKE '%%"+gamerow[6]+"%%'" ##might need to change to gamerow[1]
            # pqs=list(engine.execute(qry).fetchall())
            # qs=random.sample(pqs,gamerow[2])
            # qstr=""
            # for element in qs:
            #     qstr+=(str(element[0])+",")
            code = form.code.data
            
            #     code = random.randint(100000, 999999)
            # gameid=str(Games.query.filter_by(code=code).first().id)
            global curentgame
            currentgame[game_id]=gamechoice
            nl="/waiting/host/"+str(game_id)
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
    
    query = dbSession.query(Game, GameCategory) \
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
    players=dbSession.query(Players).filter(Players.game_id==id).all()
    # players=Players.query.filter_by(game=id)
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
    qstr=''
    qstring=dbSession.query(Games.questions).filter(Games.id==id).first().questions
    qstring=qstring.split(',')
    for i in qstring:
        quest=dbSession.query(Question).filter(Question.question_id==i).first()
        q1.append(quest.question_content)
        currentchoice.append(quest.choices)
        correct.append(quest.correct_choice-1)
        followup.append(quest.followup)
        hint.append(quest.hints)
    # for i in engine.execute("select DISTINCT categories, no_questions from game_category where game = '"+currentgame[id]+"' and no_questions > 0").fetchall():
    #     for j in engine.execute("select * from(select DISTINCT title, question_content, followup, choices, correct_choice, hints, bug_path_name,text_color,background_color,'class' from question q, game_category gc where gc.categories = '"+i[0]+"' and game = '"+currentgame[id]+"' and status = 'Production' and  array_remove(regexp_split_to_array(lower(btrim(gc.categories, ' ')), '[;|:]\s*'), '') <@ array_remove(regexp_split_to_array(lower(btrim(q.categories,  ' ')), '[;|:]\s*'), '')) as c order by random() limit '"+str(i[1])+"'").fetchall():
    #         q1.append(j[1])
    #         currentchoice.append(j[3])
    #         correct.append(j[4]-1)
    #         followup.append(j[2])
    #         hint.append(j[5])
    current[id]=[q1,followup,currentchoice,correct,hint] 
    return render_template("waitscreenhost.html",game=dbSession.query(Games).filter(Games.id==id).first(),form=form,pnames=pnames[id])
@app.route("/submittedanswer/<playerid>/<gameid>/<qnum>")
def submitted_answer_page(playerid,gameid,qnum):
    global numanswered
    numanswered[gameid]+=1
    game=dbSession.query(Games).filter(Games.id==int(gameid)).first()
    return render_template("submittedanswer.html",game=game,qnum=int(qnum),playerid=playerid,numconnected=numconnected[gameid],numanswered=numanswered[gameid])

@app.route("/resultplayer/<playerid>/<gameid>/<qnum>")
def player_result_page(playerid,gameid,qnum):
    qnum=int(qnum)
    global current
    game=dbSession.query(Games).filter(Games.id==int(gameid)).first()
    # oqry="Select correct_choice FROM question WHERE title='"+str(game.questions.split(',')[qnum])+"'"
    # corrans=engine.execute(oqry).fetchall()[0][0]-1
    # oqry="Select choices FROM question WHERE title='"+str(game.questions.split(',')[qnum])+"'"
    subnums=[0]*len(current[gameid][0])
    dbSession.query(Players).filter(Players.game_id==gameid)
    for player in dbSession.query(Players).filter(Players.game_id==gameid).all():
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

    pans=(dbSession.query(Players).filter(Players.id==playerid).first().submission.split(';')[-2])
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
    return render_template("resultplayer.html",player=dbSession.query(Players).filter(Players.id==playerid).first(),game=game,qnum=int(qnum)
    ,corrans=current[gameid][3][int(qnum)],choices=clean(current[gameid][2][int(qnum)])
    ,subnums=subnums,pans=pans,engine=engine,q=q,playerid=playerid)

@app.route("/leaderboardp/<playerid>/<gameid>/<qnum>")
def leaderboard_player_page(playerid,gameid,qnum):
    ps=dbSession.query(Players).filter(Players.game_id==gameid).order_by(Players.score.desc()).all()
    return render_template("leaderboardplayer.html",ps=ps,playerid=playerid,gameid=gameid,qnum=int(qnum))

@app.route("/leaderboardh/<gameid>/<qnum>")
def leaderboard_host_page(gameid,qnum):
    global numanswered
    numanswered[gameid]=0
    ps=dbSession.query(Players).filter(Players.game_id==gameid).order_by(Players.score.desc()).all()
    # ps=Players.query.filter_by(game=gameid).order_by(Players.score.desc())
    game=dbSession.query(Games).filter(Games.id==int(gameid)).first()
    global current
    return render_template("leaderboardhost.html",ps=ps,game=dbSession.query(Games).filter(Games.id==int(gameid)).first(),qnum=int(qnum),totalquestions=len(game.questions.split(','))-2,code=game.code,totalnum=len(current[gameid][0])-1)

@app.route("/playerfollowup/<playerid>/<gameid>/<qnum>")
def followup_player_page(playerid,gameid,qnum):
    game=dbSession.query(Games).filter(Games.id==int(gameid)).first()
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
    game=dbSession.query(Games).filter(Games.id==int(gameid)).first()
    # oqry="Select correct_choice FROM question WHERE title='"+str(game.questions.split(',')[qnum])+"'"
    # # corrans=engine.execute(oqry).fetchall()[0][0]-1
    # oqry="Select choices FROM question WHERE title='"+str(game.questions.split(',')[qnum])+"'"
    # subnums=[0]*len(engine.execute(oqry).fetchall()[0][0].split("\n"))
    global current
    subnums=[0]*len(clean(current[gameid][2][int(qnum)]))
    for player in dbSession.query(Players).filter(Players.game_id==gameid).all():
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
    game=dbSession.query(Games).filter(Games.id==int(gameid)).first()
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
    return render_template("followuphost.html",q=q,game=dbSession.query(Games).filter(Games.id==int(gameid)).first(),qnum=int(qnum),code=game.code)

@app.route("/podium/<gameid>")
def podium_page(gameid):
    ps=dbSession.query(Players).filter(Players.game_id==gameid).order_by(Players.score.desc()).all()
    return render_template("podium.html",ps=ps,game=dbSession.query(Games).filter(Games.id==int(gameid)).first())

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
    players=dbSession.query(Players).filter(Players.game==gid).all()
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
