from flask import Flask,abort,jsonify, redirect, request, render_template, session, url_for
from flask_sqlalchemy import SQLAlchemy
from profanity import is_bad_word
import requests
import os
import json
import time

import datetime
from threading import Thread

#-----------------------------------------------
TESTING = 0


#--- hosting related Variables
username='user1'
password='0233'
host='localhost'
db='p3'

URI = 'postgresql://'+username+':'+password+'@'+host+'/'+db

#--- PROGRAM Variables
TAG_NAME_CHAR_LIMIT = 18
USER_TAG_MAX_LIMIT = 5

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



tag_list = [ ] # tag_list for threads to featch news for

#----News sources
apiKey = '838b62c7059448b0ad8383231c8ac614'
roots = [
    {'sources':'the-times-of-india','sortBy':'publishedAt','e_or_h':'h'}, #
    {'sources':'the-hindu','sortBy':'publishedAt','e_or_h':'h'},
    {'sources':'bbc-news','sortBy':'publishedAt','e_or_h':'h'},
    {'sources':'','sortBy':'publishedAt','e_or_h':'h'},
    {'sources':'the-times-of-india','sortBy':'popularity','e_or_h':'e'},
    {'sources':'the-hindu','sortBy':'popularity','e_or_h':'e'},
    {'sources':'','sortBy':'popularity','e_or_h':'e'}
]

NEWS_RENEW_TIME = 24*60*60
NEWS_FROM_EACH_SOURCE = 10
WAIT_FOR_TAG_LIST = 5
WAIT_BEFOR_EACH_API_REQUEST = 1
WAIT_AFTER_429_ERRORCODE = 60


NEWS_PER_TAGNAME_TO_USER = 20
NEWS_PER_TAGNAME_TO_USER_HIGHLIGHTS = 5

#-----------------------------------

app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

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
    title = db.Column(db.Text  ,default="Title is not available")
    body = db.Column(db.Text, default="Body is not available")
    link = db.Column(db.Text, nullable=False,unique=True,default="https://www.grammarly.com/blog/articles/")
    img_url = db.Column(db.Text,default="https://www.google.co.in/search?q=image+of+nature&newwindow=1&tbm=isch&source=iu&ictx=1&fir=K4ZYBhoGJrlOPM%253A%252CVQ9FGsDbUMuBBM%252C_&usg=__Wwf5MVVZ4c9GR0SO67BrQMr3pek%3D&sa=X&ved=0ahUKEwiVoYPr2-7ZAhVHQo8KHYuZBIUQ9QEIMDAD#imgrc=K4ZYBhoGJrlOPM:")
    date_added = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    #__table_args__ = (UniqueConstraint('link', name='link_id'),

    #                 )

"""

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.Text, nullable=False,unique=True)
    body = db.Column(db.Integer)
    star = db.Column(db.Integer)

"""

class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tag_name = db.Column(db.Text, nullable=False,unique=True)
    clicks = db.Column(db.Integer)
    num_users = db.Column(db.Integer)
    is_used = db.Column(db.Integer)
    #test = db.Column(db.Integer)
    articles = db.relationship('Article', secondary= tagger, backref= db.backref('tags',lazy=True))
    #users = db.relationship('User', secondary= connector, backref= db.backref('tags',lazy=True)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name =  db.Column(db.Text, nullable=False)
    username = db.Column(db.Text, nullable=False)
    password = db.Column(db.Text, nullable=False)
    que = db.Column(db.Text, nullable=False)
    ans = db.Column(db.Text, nullable=False)
    tags = db.relationship('Tag', secondary= connector, backref= db.backref('users',lazy=True))



db.create_all()

#########################################################################

@app.route('/', methods=['GET'])
def index_get():

    articles = Article.query.all()
    return render_template('index.html', articles=articles)


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



@app.route('/news/tagname/<name>', methods=['GET'])
def tag_name_get(name):

    tags =  Tag.query.filter_by(tag_name = name).all()
    response = []
    total_count = 0
    if tags:

        tags[0].clicks = tags[0].clicks + 1
        tags[0].is_used = 1
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

    tag_name = tag_name.strip().title()
    if len(tag_name) > TAG_NAME_CHAR_LIMIT:
        print("returning error msg")
        return jsonify({'status':0,'msg':'!! Maximum '+ str(TAG_NAME_CHAR_LIMIT) +' charcter is allowed for tagname!!'})

    u = User.query.filter_by(username = user_name).first()
    print("length of user tags",len(u.tags))
    if len(u.tags) >= USER_TAG_MAX_LIMIT:
        return jsonify({'status':0,'msg':'!! Maximum '+str(USER_TAG_MAX_LIMIT)+' tags can be added, delete less prior tags first!!'})
    print("after here")
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
        if is_bad_word(tag_name) == True:
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
        tag = Tag(tag_name = tag_name,clicks=1,num_users=1,is_used=1)
        db.session.add(tag)
        db.session.commit()
        print("hi")
        #parser(tag.tag_name)
        #Thread(target=parser, args=([tag.tag_name]).start()
        tag_list.insert(0,tag.tag_name)
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

    if tagname == '*':
        db.session.query(Tag).delete()
        db.session.commit()
        return jsonify({'msg':"Deleted all tags"})

    tag = Tag.query.filter(Tag.tag_name == tagname).first()

    if tag == None:
        return jsonify( {'msg':'tag not found for given id'} )


    res = {}
    res["tag_name"] = tag.tag_name
    res["id"]= tag.id

    db.session.delete(tag)
    db.session.commit()

    return jsonify( {'deleted_tag':res } )


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

    user = User.query.filter_by(username = username).first()
    tags = user.tags
    output = []
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
    for mv in Tag.query.filter(Tag.tag_name.ilike('%' + str(search) + '%')).limit(8).all():
        results.append(mv.tag_name)
    return jsonify(json_list=results)


#####################################################################################

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

        while True:
            try:
                while not tag_list:
                    #print("tag_list is empty so sleeping")
                    time.sleep(WAIT_FOR_TAG_LIST)

                tagname = tag_list.pop()
                print("insider Parser value of tagname:",tagname)
                tag = Tag.query.filter_by(tag_name=tagname).first()
                tag.clicks = 0
                if tag.is_used == 0:
                    print("\n\nreturn because tag is not used :\n",tag.tag_name)
                    continue
                tag.is_used = 0
                print("Tag selected : ",tag.tag_name,'\n')
                #----------------------------------------------------------------


                for root in roots:

                    if root['e_or_h'] == 'e':
                        url = 'https://newsapi.org/v2/top-headlines'
                    else:
                        url = 'https://newsapi.org/v2/everything'

                    if root['sources'] == "":
                        payload = {'q':tag.tag_name,'sortBy':root['sortBy'], 'apiKey':apiKey}
                    else:
                        payload = {'q':tag.tag_name,'sources':root['sources'], 'sortBy':root['sortBy'], 'apiKey':apiKey}


                    while True:
                    #    try:
                            time.sleep(WAIT_BEFOR_EACH_API_REQUEST)
                            response = requests.get(url, params=payload)
                            print (response.url)
                            if response.status_code != 429:
                                break
                            print("Status code is 429 so sleeping")
                            time.sleep(WAIT_AFTER_429_ERRORCODE)
                    #    except:
                    #        break
                    if response.status_code != 200:
                        print("response.status_code",response.status_code)
                        temp = json.loads(response.text)
                        print(temp['code'],temp['message'])
                        continue
                    temp = json.loads(response.text)
                    print("Tag Name:",tag.tag_name,"status",temp['status'],"TotalResult:",temp['totalResults'])
                    print("towards adder")
                    adder(tag.tag_name, temp)
            except:
                pass
        return
                #----------------------------------------------------------------

def adder(tagname, response):
    try:
        t = Tag.query.filter_by(tag_name = tagname).first()

        if t.articles:
            for article in t.articles:
                print("deleted article :" ,article.title)
                db.session.delete(article)

        t.articles[:] = []
        db.session.commit()

        if t:
            count = 1
            for article in response['articles']:
                if count > NEWS_FROM_EACH_SOURCE:
                    break
                else:
                    count += 1

                title = article['title']
                body = article['description']
                link = article['url']
                img_url = article['urlToImage']

                a = Article.query.filter_by(link=link).all()
                if a:
                    a=a[0]
                    print("setted previous article as same")
                else:
                    a = Article(title= title, body= body, link = link, img_url = img_url)
                    db.session.add(a)
                    db.session.commit()
                print('Tag Updated :',t.tag_name,'Article:',a.title)
                t.articles.append(a)
                db.session.commit()
        else:
            print("tag is not found")
    except:
        pass
    return

def update_loop():
    while True:
        if TESTING == 1:
            time.sleep(9000000)
        tags = Tag.query.all()
        list = []
        for tag in tags:
            list.append(tag.tag_name)
            if tag.articles:
                for article in tag.articles:
                    db.session.delete(article)
                tag.articles[:] = []
                db.session.commit()


        tag_list.extend(list)
        time.sleep(NEWS_RENEW_TIME)
        #time.sleep(60)
    return

Thread(target=parser).start()
Thread(target=update_loop).start()


if "__main__" == __name__:
        app.run()
