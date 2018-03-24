from flask import Flask,abort,jsonify, redirect, request, render_template, session, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_,desc,func
from profanity import is_bad_word,add_bad_word,all_blocked_word
import requests
import os
import json
import time
import traceback
import logging
from newsapi import NewsApiClient

import schedule
import datetime
from threading import Thread

#-----------------------------------------------



#--- hosting related Variables
username='user1'
password='0233'
host='localhost'
db='p5'

URI = 'postgresql://'+username+':'+password+'@'+host+'/'+db

#--- PROGRAM Variables
TAG_NAME_CHAR_LIMIT = 18
USER_TAG_MAX_LIMIT = 8

#----User loggin related
USER_NAME_MAX_LIMIT = 20
USER_NAME_MIN_LIMIT = 1

USER_USERNAME__MAX_LIMIT = 20
USER_USERNAME_MIN_LIMIT = 6

USER_PASSWORD_MAX_LIMIT = 20
USER_PASSWORD_MIN_LIMIT = 6

USER_QUE_MAX_LIMIT = 50
USER_QUE_MIN_LIMIT = 1

USER_ANS_MAX_LIMIT = 20
USER_ANS_MIN_LIMIT = 1

COMMENT_BODY_MIN_LIMIT=1
COMMENT_BODY__MAX_LIMIT=5000

COMMENT_TITLE_MIN_LIMIT=1
COMMENT_TITLE__MAX_LIMIT=100


#-------------------------------------------------

ONLINE_USERS=0
MAX_ONLINE = 0
ADDED_TAG = 0
USER_SIGNUP =0
API_REQUEST = 0


tag_list = [ ] # tag_list for threads to featch news for


MIGRATING = 1

if os.environ.get('ENV') != 'production':
    # local host

    domain = 'http://localhost:5000'
    fe_domain = 'http://localhost:5001'


    RENEW_TIME = "21:34"

    NEWS_RENEW_TIME =  24*60*60
    WAIT_FOR_TAG_LIST = 1
    WAIT_BEFORE_EACH_API_REQUEST = 0
    WAIT_AFTER_429_ERRORCODE = 30

    ADDER_EACH_API_REQUEST = 0.10
    ADDER_429 = 10

    NEWS_PER_TAGNAME_TO_USER = 20
    NEWS_PER_TAGNAME_TO_USER_HIGHLIGHTS = 3
    TAG_DAYS_LIMIT = 30

else:
    domain = 'https://p-host.herokuapp.com'
    fe_domain = 'https://newsbytag.herokuapp.com'
    # production
    RENEW_TIME = "03:00"

    NEWS_RENEW_TIME = 24*60*60
    WAIT_FOR_TAG_LIST = 0.5
    WAIT_BEFORE_EACH_API_REQUEST = 0
    WAIT_AFTER_429_ERRORCODE = 30

    ADDER_EACH_API_REQUEST = 0.10
    ADDER_429 = 10

    NEWS_PER_TAGNAME_TO_USER = 20
    NEWS_PER_TAGNAME_TO_USER_HIGHLIGHTS = 3
    TAG_DAYS_LIMIT = 30
#-------------------------------------------------------------
#,the-hindu,the-verge,bbc-news
#----News sources
apiKey = '838b62c7059448b0ad8383231c8ac614'
roots = [
    # No relevancy
    #{'sources':'the-times-of-india','sortBy':'popularity','e_or_h':'h','pageSize':str(NEWS_PER_TAGNAME_TO_USER+1)}, #
    {'sources':'the-times-of-india,the-hindu,the-verge,bbc-news,google-news-in','sortBy':'popularity','e_or_h':'e','pageSize':str(NEWS_PER_TAGNAME_TO_USER+1)},
    {'sources':'', 'sortBy':'publishedAt','e_or_h':'e','pageSize':str(NEWS_PER_TAGNAME_TO_USER+1)},

    ]

#-----------------------------------

app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

newsapi = NewsApiClient(api_key=apiKey)

if os.environ.get('ENV') == 'production':
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
    app.config['DEBUG'] = False
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
else:
    app.debug = True
    db_uri = URI
    app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

tagger = db.Table('tagger',
            db.Column('id', db.Integer, primary_key=True),
            db.Column('tag_id', db.Integer, db.ForeignKey('tag.id')),
            db.Column('article_id', db.Integer, db.ForeignKey('article.id'))
)

connector = db.Table('connector',
            db.Column('id', db.Integer, primary_key=True),
            db.Column('tag_id', db.Integer, db.ForeignKey('tag.id')),
            db.Column('user_id', db.Integer, db.ForeignKey('user.id'))
)


class Article(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.Text)
    body = db.Column(db.Text)  #unique=True
    link = db.Column(db.Text)
    img_url = db.Column(db.Text)
    date_added = db.Column(db.DateTime,server_default=func.now())

class Record(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    online_max = db.Column(db.Integer)
    tag_added = db.Column(db.Integer)  #unique=True
    user_signup = db.Column(db.Integer)
    trending_tag = db.Column(db.Text)
    max_clicked = db.Column(db.Text)
    api_request = db.Column(db.Integer)
    timedate = db.Column(db.DateTime,server_default=func.now())


class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.Text)
    body = db.Column(db.Text)
    star = db.Column(db.Integer)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))


class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tag_name = db.Column(db.Text)
    clicks = db.Column(db.Integer)
    num_users = db.Column(db.Integer)
    is_used = db.Column(db.Integer)
    mod_date = db.Column(db.Integer)
    #test = db.Column(db.Integer)
#    com = db.Column(db.Integer)
    articles = db.relationship('Article', secondary= tagger, backref= db.backref('tags',lazy=True))
    #users = db.relationship('User', secondary= connector, backref= db.backref('tags',lazy=True)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name =  db.Column(db.Text)
    username = db.Column(db.Text)
    password = db.Column(db.Text)
    que = db.Column(db.Text)
    ans = db.Column(db.Text)
    tags = db.relationship('Tag', secondary= connector, backref= db.backref('users',lazy=True))
    comments = db.relationship('Comment',backref='user')



#if MIGRATING == 0:
#db.create_all()

#########################################################################

@app.before_first_request
def initialize():
    print ("Called only once, when the first request comes in")


@app.route('/record', methods=['GET'])
def record_user():
    global ONLINE_USERS, MAX_ONLINE
    flag = request.args.get('flag')
    if flag == 'signin':
        ONLINE_USERS += 1
        if ONLINE_USERS > MAX_ONLINE:
            MAX_ONLINE = ONLINE_USERS
    elif (flag == 'signout'):
        ONLINE_USERS -= 1

    return "nothing"

@app.route('/', methods=['GET'])
def index_get():

    if 'com' in request.args:
        com = request.args.get('com')
    else:
        com = 'overview'
#----------------------------------------------------------------------

    if com == 'overview':
        max_clicked = Tag.query.order_by(desc(Tag.clicks)).all()
        trending_tag = Tag.query.order_by(desc(Tag.num_users)).all()

        if max_clicked == []:
            max_clicked='No Tag Return'
        else:
            max_clicked = max_clicked[0].tag_name

        if trending_tag == []:
            trending_tag='No Tag Return'
        else:
            trending_tag = trending_tag[0].tag_name

        return render_template('index_admin.html',com='overview',TRENDING_TAG=trending_tag,MAX_CLICKED=max_clicked,ONLINE_USERS=ONLINE_USERS,MAX_ONLINE=MAX_ONLINE,ADDED_TAG=ADDED_TAG,USER_SIGNUP=USER_SIGNUP,API_REQUEST=API_REQUEST)

    elif com == 'tag_table':
        tags = Tag.query.all()
        return render_template('index_admin.html',com='tag_table',tags=tags)


    elif com == 'record_table':
        records = Record.query.all()
        return render_template('index_admin.html',com='record_table',records=records)


    elif com == 'user_table':
        users = User.query.all()
        return render_template('index_admin.html',com='user_table',users=users)

    elif com == 'comment_table':
        comments = Comment.query.all()
        return render_template('index_admin.html',com='comment_table',comments=comments)

    elif com == 'tag':
        tags = Tag.query.all()
        return render_template('index_admin.html',com='tag',tags=tags)

    elif com == 'user':
        users = User.query.all()
        return render_template('index_admin.html',com='user',users=users)

    elif com == 'comment':
        comments = Comment.query.all()
        return render_template('index_admin.html',com='comment',comments=comments)

    else:
        return "nothing selected"

@app.route('/news/highlights/username/<username>', methods=['GET'])
def highlights_get(username):

    user =  User.query.filter_by(username = username).first()
    response = []
    total_count = 0
    if user.tags != []:
        for tag in user.tags:
            if tag.articles != []:
                count=1
                for article in tag.articles:
                    if count > NEWS_PER_TAGNAME_TO_USER_HIGHLIGHTS:
                        break
                    else:
                        count+=1
                    res = {}
                    res['id'] = article.id
                    res['title'] = article.title
                    res['body'] = article.body
                    res['link'] = article.link
                    res['added'] = article.date_added
                    res['img_url'] = article.img_url
                    response.append(res)
                    total_count+=1

    return jsonify({'response' : response, 'count':str(total_count) })



@app.route('/news/tagname/<tag_name>', methods=['GET'])
def tag_name_get(tag_name):

    tags =  Tag.query.filter_by(tag_name = tag_name).all()
    response = []
    total_count = 0
    if tags:
        """
        if len(tags[0].articles) == 0:
            if tag_name not in tag_list:
                    tag_list.insert(0,tag_name)
        """
        tags[0].clicks = tags[0].clicks + 1
        tags[0].is_used = 1
        tags[0].mod_date = 1
        db.session.commit()


        articles = tags[0].articles
        if articles:
            count=1
            for article in articles:
                if count > NEWS_PER_TAGNAME_TO_USER:
                    break
                else:
                    count+=1
                res = {}
                res['id'] = article.id
                res['title'] = article.title
                res['body'] = article.body
                res['link'] = article.link
                res['added'] = article.date_added
                res['img_url'] = article.img_url
                response.append(res)
                total_count+=1



    return jsonify({'response' : response ,'count':total_count,'status':1})




@app.route('/tag/add/<user_name>/<tag_name>', methods=['GET'])
def tag_add_get(user_name, tag_name):

    global ADDED_TAG

    tag_name = tag_name.strip().title()
    if len(tag_name) > TAG_NAME_CHAR_LIMIT:
        print("returning error msg")
        return jsonify({'status':0,'msg':'!! Maximum '+ str(TAG_NAME_CHAR_LIMIT) +' charcter is allowed for tagname!!'})

    u = User.query.filter_by(username = user_name).first()

    if len(u.tags) >= USER_TAG_MAX_LIMIT:
        return jsonify({'status':0,'msg':'!! Maximum '+str(USER_TAG_MAX_LIMIT)+' tags can be added, delete less prior tags first!!'})

    u = User.query.filter_by(username=user_name).first()
    t = Tag.query.filter_by(tag_name = tag_name).all()

    if t != []:
        tag = t[0]
        print("word is already there")
        if tag in u.tags:
            res = {}
            res["tag_name"] = tag.tag_name
            res["id"]= tag.id
            res['username']=u.username
            return jsonify( {'added_tag': res,'status':1 } )
        else:
            tag.num_users += 1
            tag.users.append(u)
            db.session.add(tag)
            db.session.commit()

            res = {}
            res["tag_name"] = tag.tag_name
            res["id"]= tag.id
            res['username']=u.username
            return jsonify( {'added_tag': res,'status':1 } )

    else:
        for word in tag_name.split():
            if is_bad_word(word) == True:
                print("return true")
                return jsonify({'status':0,'msg':'!! Profanity word as tag name is not allowed !!'})
            """
        try:
            result = requests.get("http://www.purgomalum.com/service/containsprofanity?text="+tag_name)
            if result.status_code == 200:
                if result.text == 'true':
                   return jsonify({'status':0,'msg':'!! Profanity word as tag name is not allowed !!'})
        except:
            pass
        """
        tag = Tag(tag_name = tag_name,clicks=1,num_users=1,is_used=1, mod_date=1)
        db.session.add(tag)
        db.session.commit()
        print("hi")
        #parser(tag.tag_name)
        #Thread(target=parser, args=([tag.tag_name]).start()
        tag_list.insert(0,tag.tag_name)
        ADDED_TAG +=1
        #Thread(target=parser,args=(tag.tag_name,)).start()

        tag.users.append(u)
        db.session.add(tag)
        db.session.commit()

        res = {}
        res["tag_name"] = tag.tag_name
        res["id"]= tag.id
        res['username']=u.username
        return jsonify( {'added_tag': res,'status':1 } )

    return jsonify({'status':0,'msg':'!! Not Added !!'})

@app.route('/tag/delete/username/<username>/<tagname>', methods=['GET'])
def tag_delete_username_get(username,tagname):
    user = User.query.filter_by(username = username).first()
    if tagname == '*':
        #db.session.query(Table_name).filter_by(id.in_()).delete()
        print('I am here')
        for tag in user.tags:
            tag.num_users -= 1
        user.tags[:] = []
        db.session.commit()
        return "success"
    else:
        tag = Tag.query.filter_by(tag_name = tagname).first()
        user.tags.remove(tag)
        tag.num_users -= 1
        db.session.commit()
    res = {}
    res["tag_name"] = tag.tag_name
    res["id"]= tag.id

    db.session.commit()

    return jsonify( {'deleted_tag':res ,'status':1} )

@app.route('/tag/delete/<tagname>', methods=['GET'])
def tag_delete_get(tagname):

    if tagname == '*alltagdelete*':
        for tag in Tag.query.all():
            for article in tag.articles:
                db.session.delete(article)
            db.session.commit()

            for user in tag.users:
                    user.tags.remove(tag)

            db.session.delete(tag)
            db.session.commit()

        return redirect(url_for('index_get',com='tag'))

    tag = Tag.query.filter(Tag.tag_name == tagname).first()

    if tag == None:
        return jsonify( {'msg':'tag not found for given id'} )

    if 'flag' in request.args:
        add_bad_word(tag.tag_name)

    res = {}
    res["tag_name"] = tag.tag_name
    res["id"]= tag.id

    for user in tag.users:
        user.tags.remove(tag)
    db.session.commit()
    for article in tag.articles:
        db.session.delete(article)
    db.session.commit()

    db.session.delete(tag)
    db.session.commit()

    return redirect(url_for('index_get',com='tag'))


@app.route('/tag/trending/<int:top>', methods=['GET'])
def tag_trending_get(top = 10):
    tags = Tag.query.order_by(Tag.num_users.desc()).limit(10).all()

    output = []
    for tag in tags:
        t = {}
        t['id'] = tag.id
        t['tag_name'] = tag.tag_name
        output.append(t)

    return jsonify( {'trending_tag': output } )


@app.route('/tag/tagname/<tagname>', methods=['GET'])
def tag_get(tagname):

    count = Tag.query.filter_by(tag_name = tagname).count()

    return jsonify( {'status': count } )



@app.route('/tag/username/<username>', methods=['GET'])
def tag_username_get(username='rnmpatel'):

    output = []
    user = User.query.filter_by(username = username).all()
    if user != []:
        print("inside tag checking")
        tags = user[0].tags
        for tag in tags:
            t = {}
            t['id'] = tag.id
            t['tag_name'] = tag.tag_name
            output.append(t)

    return jsonify( {'user_tag': output } )


@app.route('/tag/match', methods=['GET'])
def autocomplete():
    results = []
    search = request.args.get('q')
    t =Tag.query.filter(Tag.tag_name.ilike('%' + str(search) + '%')).limit(8).all()
    for mv in t:
        results.append(mv.tag_name)
    return jsonify(json_list=results)
#####################################################################################

@app.route('/comment/delete/id/<id>', methods=['GET'])
def delete_comment_get(id):
    com = Comment.query.filter_by(id = id).first()
    usr = com.user
    usr.comments.remove(com)
    db.session.delete(com)
    db.session.commit()
    return "deleted"



@app.route('/comment', methods=['POST'])
def comment_post():
    username = request.form['username'].strip()
    title = request.form['title'].strip()
    body = request.form['body'].strip()
    star = int(request.form['rating'])

    if len(title) < COMMENT_TITLE_MIN_LIMIT:
               return jsonify( {'status': 0, 'msg':'!! Minimum length of $ Title $ should be '+str(COMMENT_TITLE_MIN_LIMIT)+' character !!'})
    if len(title) > COMMENT_TITLE__MAX_LIMIT:
               return jsonify( {'status': 0, 'msg':'!! Maximum length of $ Title $ should be '+str(COMMENT_TITLE__MAX_LIMIT)+' character !!'})

    if len(body) < COMMENT_BODY_MIN_LIMIT:
               return jsonify( {'status': 0, 'msg':'!! Minimum length of $ Body $ should be '+str(COMMENT_BODY_MIN_LIMIT)+' character !!'})
    if len(body) > COMMENT_BODY__MAX_LIMIT:
               return jsonify( {'status': 0, 'msg':'!! Maximum length of $ Body $ should be '+str(COMMENT_BODY__MAX_LIMIT)+' character !!'})


    u=User.query.filter_by(username=username).first()
    c=Comment(title=title,body=body,star=star,user=u)
    db.session.add(c)
    db.session.commit()

    return jsonify({'status':1})

###################################################################################

@app.route('/user/delete/username/<username>', methods=['GET'])
def delete_username_get(username):
    user = User.query.filter_by(username = username).first()

    res = requests.get(fe_domain+'/signout');

    for tag in user.tags:

            if 'flag' in request.args:
                add_bad_word(tag.tag_name)

            for user in tag.users:
                user.tags.remove(tag)

            for article in tag.articles:
                db.session.delete(article)
            db.session.commit()

            db.session.delete(tag)
            db.session.commit()


    db.session.delete(user)
    db.session.commit()

    return redirect(url_for('index_get'),com='user')

@app.route('/user/username/<username>', methods=['GET'])
def user_details_get(username):

    u = User.query.filter_by(username = username).all()
    if u == []:
        return jsonify( {'user':[],'status':0})
    else:
        t = {}
        user = u[0]
        t['id'] = user.id
        t['username'] = user.username
        t['name'] = user.name
        t['que'] = user.que
        t['ans'] = user.ans
    #arr = []
    #arr.append(t)
    return jsonify( {'user':t,'status':1})


@app.route('/user/update', methods=['POST'])
def user_details_update_get():

    user = User.query.filter_by(username = request.form['username']).first()
    if 'password' in request.form:
        password = request.form['password'].strip()
        if len(password) < USER_PASSWORD_MIN_LIMIT:
                   return jsonify( {'status': 0, 'msg':'!! Minimum length of $ Password $ should be '+str(USER_PASSWORD_MIN_LIMIT)+' character !!'})
        if len(password) > USER_PASSWORD_MAX_LIMIT:
                   return jsonify( {'status': 0, 'msg':'!! Maximum length of $ Password $ should be '+str(USER_PASSWORD_MAX_LIMIT)+' character !!'})

        user.password = password

    if 'name' in request.form:
        name = request.args.form['name'].strip()
        if len(name) < USER_NAME_MIN_LIMIT:
                   return jsonify( {'status': 0, 'msg':'!! Minimum length of $ Name $ should be '+str(USER_NAME_MIN_LIMIT)+' character !!'})
        if len(password) > USER_NAME_MAX_LIMIT:
                   return jsonify( {'status': 0, 'msg':'!! Maximum length of $ Name $ should be '+str(USER_NAME_MAX_LIMIT)+' character !!'})

        user.name = name

    if 'que' in request.form:
        que = request.args.form['que'].strip()
        if len(que) < USER_QUE_MIN_LIMIT:
                   return jsonify( {'status': 0, 'msg':'!! Minimum length of $ Question $ should be '+str(USER_QUE_MIN_LIMIT)+' character !!'})
        if len(que) > USER_QUE_MAX_LIMIT:
                   return jsonify( {'status': 0, 'msg':'!! Maximum length of $ Question $ should be '+str(USER_QUE_MAX_LIMIT)+' character !!'})

        user.que = que

    if 'ans' in request.form:
        ans = request.args.form['ans'].strip()
        if len(ans) < USER_ANS_MIN_LIMIT:
                   return jsonify( {'status': 0, 'msg':'!! Minimum length of $ Answer $ should be '+str(USER_ANS_MIN_LIMIT)+' character !!'})
        if len(password) > USER_ANS_MAX_LIMIT:
                   return jsonify( {'status': 0, 'msg':'!! Maximum length of $ Answer $ should be '+str(USER_ANS_MAX_LIMIT)+' character !!'})

        user.ans = ans

    db.session.commit()
    return jsonify( {'status': 1})

#####################################################################################
#sign in and SignOut and SignUp

@app.route('/signup', methods=['POST'])
def tag_signup_post():
    global USER_SIGNUP

    username = request.form['username'].strip()
    name = request.form['name'].strip()
    ans = request.form['ans'].strip()
    que = request.form['que'].strip()
    password = request.form['password'].strip()

    c = User.query.filter_by(username=username).count()
    if c != 0:
        return jsonify( {'status': 0, 'msg':'!! Username $ '+username+' $ is already exist !!'})


    if len(username) < USER_USERNAME_MIN_LIMIT:
               return jsonify( {'status': 0, 'msg':'!! Minimum length of $ Username $ should be '+str(USER_USERNAME_MIN_LIMIT)+' character !!'})
    if len(username) > USER_USERNAME__MAX_LIMIT:
               return jsonify( {'status': 0, 'msg':'!! Maximum length of $ Username $ should be '+str(USER_USERNAME__MAX_LIMIT)+' character !!'})

    if len(password) < USER_PASSWORD_MIN_LIMIT:
               return jsonify( {'status': 0, 'msg':'!! Minimum length of $ Password $ should be '+str(USER_PASSWORD_MIN_LIMIT)+' character !!'})
    if len(password) > USER_PASSWORD_MAX_LIMIT:
               return jsonify( {'status': 0, 'msg':'!! Maximum length of $ Password $ should be '+str(USER_PASSWORD_MAX_LIMIT)+' character !!'})

    if len(name) < USER_NAME_MIN_LIMIT:
               return jsonify( {'status': 0, 'msg':'!! Minimum length of $ Name $ should be '+str(USER_NAME_MIN_LIMIT)+' character !!'})
    if len(password) > USER_NAME_MAX_LIMIT:
               return jsonify( {'status': 0, 'msg':'!! Maximum length of $ Name $ should be '+str(USER_NAME_MAX_LIMIT)+' character !!'})

    if len(que) < USER_QUE_MIN_LIMIT:
               return jsonify( {'status': 0, 'msg':'!! Minimum length of $ Question $ should be '+str(USER_QUE_MIN_LIMIT)+' character !!'})
    if len(que) > USER_QUE_MAX_LIMIT:
               return jsonify( {'status': 0, 'msg':'!! Maximum length of $ Question $ should be '+str(USER_QUE_MAX_LIMIT)+' character !!'})

    if len(ans) < USER_ANS_MIN_LIMIT:
               return jsonify( {'status': 0, 'msg':'!! Minimum length of $ Answer $ should be '+str(USER_ANS_MIN_LIMIT)+' character !!'})
    if len(password) > USER_ANS_MAX_LIMIT:
               return jsonify( {'status': 0, 'msg':'!! Maximum length of $ Answer $ should be '+str(USER_ANS_MAX_LIMIT)+' character !!'})


    user = User(username = username, name=name, password=password, que=que, ans=ans)
    db.session.add(user)
    db.session.commit()
    USER_SIGNUP += 1

    return jsonify( {'status': 1} )



@app.route('/signin', methods=['POST'])
def tag_signin_post():
    username = request.form['username']
    password = request.form['password']

    count = User.query.filter_by(username=username, password=password).count()
    if count != 0:
                user = User.query.filter_by(username=username,password=password).first()
                t={'status':1}
    else:
        t = {'status':0}
    return jsonify(t)



##########################################################################

def parser():
        global WAIT_AFTER_429_ERRORCODE,  WAIT_BEFORE_EACH_API_REQUEST,  WAIT_FOR_TAG_LIST, API_REQUEST
        global ADDER_429,  ADDER_EACH_API_REQUEST
        print("Inside parser")
        while True:
            try:
                while tag_list == []:
                    #print("tag_list is empty so sleeping")
                    time.sleep(WAIT_FOR_TAG_LIST)

                tagname = tag_list.pop()

                tag = Tag.query.filter_by(tag_name=tagname).first()
                if tag.is_used == 0:
                    print("\n\nreturn because tag is not used :\n",tag.tag_name)
                    continue

                for article in tag.articles:
                        print("Deleted article : Tag Name :",tagname ,article.title)
                        db.session.delete(article)


                tag.articles[:] = []
                db.session.commit()

                #----------------------------------------------------------------

                #total_count = len(tag.articles)
                for root in roots:
                    print("Length of articles in tag is :",tagname,len(tag.articles))
                    if len(tag.articles) >= int((NEWS_PER_TAGNAME_TO_USER*3/4)):
                        break

                    if root['e_or_h'] == 'h':
                        url = 'https://newsapi.org/v2/top-headlines'
                    else:
                        url = 'https://newsapi.org/v2/everything'

                    if root['sources'] == "":
                        payload = {'q':tag.tag_name,'sortBy':root['sortBy'], 'apiKey':apiKey, 'language':'en','pageSize':root['pageSize']}
                    else:
                        payload = {'q':tag.tag_name, 'pageSize':root['pageSize'], 'sources':root['sources'], 'language':'en', 'sortBy':root['sortBy'], 'apiKey':apiKey}

                    no_429 = 0
                    while True:

                            time.sleep(WAIT_BEFORE_EACH_API_REQUEST)

                            response = requests.get(url, params=payload,timeout=20)
                            API_REQUEST +=1
                            print (response.url)
                            if response.status_code != 429:
                                break
                            print("Status code is 429 so sleeping")
                            if no_429 == 0:
                                WAIT_BEFORE_EACH_API_REQUEST += ADDER_EACH_API_REQUEST # 0.25
                                print('\n\n\nmodified each request wait :', WAIT_BEFORE_EACH_API_REQUEST)
                            if no_429 > 1:
                                WAIT_AFTER_429_ERRORCODE += ADDER_429  # 10
                                print("\n\n\nmodified 429 :",WAIT_AFTER_429_ERRORCODE)
                            time.sleep(WAIT_AFTER_429_ERRORCODE)

                    if response.status_code != 200:
                        print("response.status_code",response.status_code)
                        temp = json.loads(response.text)
                        print(temp['code'],temp['message'])
                        continue
                    temp = json.loads(response.text)
                    print("Tag Name:",tag.tag_name,"status",temp['status'],"TotalResult:",temp['totalResults'])
                    print("towards adder")
                    adder(tag.tag_name, temp)

                #------------------------------------------------------------------
                tag.is_used = 0
                tag.clicks = 0
                db.session.commit()
                print("tag click and is_usr reset")
            except Exception as e:
                tag.is_used = 0
                tag.clicks = 0
                db.session.commit()
                print("error basic :",e.__doc__)
                print("try catch pass in parser")
                logging.error(traceback.format_exc())
                pass
        return
                #----------------------------------------------------------------

def adder(tagname, response):
    global NEWS_PER_TAGNAME_TO_USER
    print("inside adder")
    try:
        t = Tag.query.filter_by(tag_name = tagname).first()

        if t != []:
            count = 1
            for article in response['articles']:
                if count > NEWS_PER_TAGNAME_TO_USER:
                    break
                else:
                    count += 1

                title = article['title']
                body = article['description']
                link = article['url']
                img_url = article['urlToImage']

                yes = 0
                articles = Article.query.filter(or_(Article.link == link,Article.title == title,Article.img_url == img_url)).all()
                for article in articles:
                    if article in t.articles:
                        a = article
                        yes = 1
                        break
                if yes == 0:
                    #,date_added=datetime.datetime.utcnow
                    a = Article(title= title, body= body, link = link, img_url = img_url)
                    db.session.add(a)
                    t.articles.append(a)
                    db.session.commit()

                print('Tag Updated :',t.tag_name,'Article:',a.title)

        else:
            print("tag is not found")

    except Exception as e:
        print("error basic :",e.__doc__)
        print("try catch pass in parser")
        logging.error(traceback.format_exc())
        pass

    return



def update_loop():

    global ONLINE_USERS, MAX_ONLINE, ADDED_TAG, USER_SIGNUP, API_REQUEST

    print("Inside update_loop")

    tags = Tag.query.all()
    for tag in tags:
        if tag.mod_date > TAG_DAYS_LIMIT:

            print("\n\nTag is deleted because of no use :",tag.tag_name)
            for user in tag.users:
                user.tags.remove(tag)

            for article in tag.articles:
                db.session.delete(article)

            db.session.delete(tag)

        else:
            tag.mod_date = tag.mod_date + 1
    db.session.commit()


    tags = Tag.query.all()
    my_tag_list = []
    for tag in tags:
        my_tag_list.append(tag.tag_name)
    print("list sent :",my_tag_list)
    tag_list.extend(my_tag_list)


    max_clicked = Tag.query.order_by(desc(Tag.clicks)).all()
    trending_tag = Tag.query.order_by(desc(Tag.num_users)).all()

    if max_clicked == []:
        max_clicked='No Tag Return'
    else:
        max_clicked = max_clicked[0].tag_name

    if trending_tag == []:
        trending_tag='No Tag Return'
    else:
        trending_tag = trending_tag[0].tag_name
    r = Record(online_max=ONLINE_USERS, tag_added=ADDED_TAG, user_signup=USER_SIGNUP, trending_tag=trending_tag, max_clicked=max_clicked, api_request=API_REQUEST)
    db.session.add(r)
    db.session.commit()


    ONLINE_USERS=0
    MAX_ONLINE = 0
    ADDED_TAG = 0
    USER_SIGNUP =0
    API_REQUEST = 0

    return



def repeater():
    while True:
        schedule.run_pending()
        time.sleep(60) # wait one minute



print("starting threads")
if MIGRATING == 0:
    Thread(target=parser).start()
    Thread(target=repeater).start()

schedule.every().day.at(RENEW_TIME).do(update_loop,'It is 03:00')


update_loop()

if "__main__" == __name__:
        print(__name__)
        app.run(use_reloader=False,threaded=True)
