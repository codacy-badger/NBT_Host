from flask import Flask,abort,jsonify, redirect, request, render_template, session, url_for
from flask_sqlalchemy import SQLAlchemy
import requests


import json
from datetime import time

import datetime
from threading import Thread

#--- Variables
username='user1'
password='0233'
host='localhost'
db='pnews2'


app = Flask(__name__)

if os.environ.get('ENV') == 'production':
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
    app.config['DEBUG'] = False
else:
    app.debug = True
    db_uri = 'postgresql://'+username+':'+password+'@'+host+'/'+db
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

class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tag_name = db.Column(db.Text, nullable=False,unique=True)
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

class Log(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id =  db.Column(db.Text, nullable=False)
    article_id = db.Column(db.Text, nullable=False)

class Article(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.Text, nullable=False ,default="Title is not available")
    body = db.Column(db.Text, nullable=False,default="Body is not available")
    link = db.Column(db.Text, nullable=False,unique=True,default="https://www.grammarly.com/blog/articles/")
    img_url = db.Column(db.Text, nullable=False,default="https://www.google.co.in/search?q=image+of+nature&newwindow=1&tbm=isch&source=iu&ictx=1&fir=K4ZYBhoGJrlOPM%253A%252CVQ9FGsDbUMuBBM%252C_&usg=__Wwf5MVVZ4c9GR0SO67BrQMr3pek%3D&sa=X&ved=0ahUKEwiVoYPr2-7ZAhVHQo8KHYuZBIUQ9QEIMDAD#imgrc=K4ZYBhoGJrlOPM:")
    date_added = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    #__table_args__ = (UniqueConstraint('link', name='link_id'),
    #                 )
#########################################################################

@app.route('/', methods=['GET'])
def index_get():

    articles = Article.query.all()
    return render_template('index.html', articles=articles)


@app.route('/read/<username>/<int:article_id>', methods=['GET'])
def read_article_get(article_id,username):
    user = User.query.filter_by(username = username).first()
    article = Article.query.filter_by(id = article_id).first()
    log = Log(user_id = user.id, article_id = article_id)
    db.session.add(log)
    db.session.commit()
    return redirect(article.link)


@app.route('/news/highlights/username/<username>', methods=['GET'])
def highlights_get(username):

    user =  User.query.filter_by(username = username).first()
    response = []
    if user.tags:
        for tag in user.tags:
            if tag.articles:
                article = tag.articles[0]

                res = {}
                res['id'] = article.id
                res['title'] = article.title
                res['body'] = article.body
                res['link'] = article.link
                res['added'] = article.date_added
                res['img_url'] = article.img_url
                response.append(res)

    return jsonify({'response' : response })



@app.route('/news/tagid/<int:id>', methods=['GET'])
def tag_id_get(id):

    tag =  Tag.query.filter_by(id = id).first()
    response = []

    if tag != None:
        articles = tag.articles
        if articles:
            for article in articles:
                res = {}
                res['id'] = article.id
                res['title'] = article.title
                res['body'] = article.body
                res['link'] = article.link
                res['added'] = article.date_added
                res['img_url'] = article.img_url
                response.append(res)


    return jsonify({'response' : response })


@app.route('/news/tagname/<name>', methods=['GET'])
def tag_name_get(name):


    tag =  Tag.query.filter_by(tag_name = name).order_by(id).first()
    response = []
    if tag != None:
        articles = tag.articles
        if articles:
            for article in articles:
                res = {}
                res['id'] = article.id
                res['title'] = article.title
                res['body'] = article.body
                res['link'] = article.link
                res['added'] = article.date_added
                res['img_url'] = article.img_url
                response.append(res)


    return jsonify({'response' : response })

tag_list = [ ] # tag_list

@app.route('/tag/add/<user_name>/<tag_name>', methods=['GET'])
def tag_add_get(user_name, tag_name):

    u = User.query.filter_by(username = user_name).first()
    if tag_name.capitalize() in u.tags:
        tag = Tag(tag_name = tag_name.capitalize())
    else:

        user = User.query.filter_by(username=user_name).first()
        t = Tag.query.filter_by(tag_name = tag_name.capitalize() ).all()
        if t:
            tag = t[0]
        else:
            try:
                result = requests.get("http://www.purgomalum.com/service/containsprofanity?text="+tag_name)
                if result.status_code == 200:
                    if result.text == 'true':
                       return jsonify({'status':0})
            except:
                pass

            tag = Tag(tag_name = tag_name.capitalize())
            db.session.add(tag)
            db.session.commit()
            print("hi")
            #parser(tag.tag_name)
            #Thread(target=parser, args=([tag.tag_name]).start()
            tag_list.insert(0,tag.tag_name)
            #Thread(target=parser,args=(tag.tag_name,)).start()
        tag.users.append(user)
        db.session.add(tag)
        db.session.commit()

    res = {}
    res["tag_name"] = tag.tag_name
    res["id"]= tag.id
    res['username']=user.username
    return jsonify( {'added_tag': res,'status':1 } )



@app.route('/tag/delete/username/<username>/<tagname>', methods=['GET'])
def tag_delete_username_get(username,tagname):
    user = User.query.filter_by(username = username).first()
    if tagname == '*':
        #db.session.query(Table_name).filter_by(id.in_()).delete()
        print('I am here')
        user.tags[:] = []
        db.session.commit()
        return "success"
    else:
        tag = Tag.query.filter_by(tag_name = tagname).first()
        user.tags.remove(tag)
    res = {}
    res["tag_name"] = tag.tag_name
    res["id"]= tag.id

    db.session.commit()

    return jsonify( {'deleted_tag':res } )

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

    tags = Tag.query.limit(10).all()
    output = []
    for tag in tags:
        t = {}
        t['id'] = tag.id
        t['tag_name'] = tag.tag_name
        output.append(t)

    return jsonify( {'trending_tag': output } )



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
    t = {}
    if u:
        user = u[0]
        t['id'] = user.id
        t['username'] = user.username
        t['name'] = user.name
        t['que'] = user.que
        t['ans'] = user.ans
    #arr = []
    #arr.append(t)
    return jsonify( {'user':t})


@app.route('/user/update/username/<username>', methods=['GET'])
def user_details_update_get(username):

    user = User.query.filter_by(username = username).first()
    if 'password' in request.args:
        user.password = request.args.get('password')
    if 'name' in request.args:
        user.name = request.args.get('name')
    if 'que' in request.args:
        user.que = request.args.get('que')
    if 'ans' in request.args:
        user.ans = request.args.get('ans')
    db.session.commit()
    return jsonify( {'status': '1'})

#####################################################################################
#sign in and SignOut and SignUp

@app.route('/signup', methods=['POST'])
def tag_signup_post():

    username = request.form['username']
    name = request.form['name']
    ans = request.form['ans']
    que = request.form['que']
    password = request.form['password']

    user = User(username = username, name=name, password=password, que=que, ans=ans)
    db.session.add(user)
    db.session.commit()

    t={'userid': user.id,
        'username' : user.name,
       }

    return jsonify( {'result': t} )



@app.route('/signin', methods=['POST'])
def tag_signin_post():
    username = request.form['username']
    password = request.form['password']

    count = User.query.filter_by(username=username, password=password).count()
    if count != 0:
                user = User.query.filter_by(username=username,password=password).first()
                t={'userid': user.id,
                    'username' : user.username,
                    'response':1
                }
    else:
        t = {'response':0}
    return jsonify(t)

##########################################################################

with app.app_context():
    db.create_all()


def parser():
        while True:
            while not tag_list:
                #print("tag_list is empty so sleeping")
                time.sleep(1)

            tagname = tag_list.pop()
            print("insider Parser value of tagname:",tagname)
            tag = Tag.query.filter_by(tag_name=tagname).first()
            print("Tag selected : ",tag.tag_name,'\n')
            #----------------------------------------------------------------
            while True:
                payload = {'q':tag.tag_name,'sources':'the-times-of-india', 'sortBy':'popularity', 'apiKey':'838b62c7059448b0ad8383231c8ac614'}
                url = 'https://newsapi.org/v2/top-headlines'
                print("\n\n",payload['sources'],"\n\n")
                print(url)
                response = requests.get(url, params=payload)
                print (response.url)
                if response.status_code != 429:
                    break
                print("Status code is 429 so sleeping")
                time.sleep(100)
            if response.status_code != 200:
                print("response.status_code",response.status_code)
                temp = json.loads(response.text)
                print(temp['code'],temp['message'])
                continue
            temp = json.loads(response.text)
            print("Tag Name:",tag.tag_name,"status",temp['status'],"TotalResult:",temp['totalResults'])
            print("towards adder")
            adder(tag.tag_name, temp)
            #----------------------------------------------------------------
            while True:
                payload = {'q':tag.tag_name,'sources':'the-hindu', 'sortBy':'popularity', 'apiKey':'838b62c7059448b0ad8383231c8ac614'}
                url = 'https://newsapi.org/v2/top-headlines'
                print("\n\n",payload['sources'],"\n\n")
                print(url)
                response = requests.get(url, params=payload)
                print (response.url)
                if response.status_code != 429:
                    break
                print("Status code is 429 so sleeping")
                time.sleep(100)
            if response.status_code != 200:
                print("response.status_code",response.status_code)
                temp = json.loads(response.text)
                print(temp['code'],temp['message'])
                continue
            temp = json.loads(response.text)
            print("Tag Name:",tag.tag_name,"status",temp['status'],"TotalResult:",temp['totalResults'])
            print("towards adder")
            adder(tag.tag_name, temp)

            #----------------------------------------------------------------
            #----------------------------------------------------------------
            while True:
                payload = {'q':tag.tag_name,'sources':'bbc-news', 'sortBy':'popularity', 'apiKey':'838b62c7059448b0ad8383231c8ac614'}
                url = 'https://newsapi.org/v2/top-headlines'
                print("\n\n",payload['sources'],"\n\n")
                print(url)
                response = requests.get(url, params=payload)
                print (response.url)
                if response.status_code != 429:
                    break
                print("Status code is 429 so sleeping")
                time.sleep(100)
            if response.status_code != 200:
                print("response.status_code",response.status_code)
                temp = json.loads(response.text)
                print(temp['code'],temp['message'])
                continue
            temp = json.loads(response.text)
            print("Tag Name:",tag.tag_name,"status",temp['status'],"TotalResult:",temp['totalResults'])
            print("towards adder")
            adder(tag.tag_name, temp)

            #----------------------------------------------------------------
            while True:
                payload = {'q':tag.tag_name,'sources':'google-news-in', 'sortBy':'popularity', 'apiKey':'838b62c7059448b0ad8383231c8ac614'}
                url = 'https://newsapi.org/v2/everything'
                print("\n\n",payload['sources'],"\n\n")
                print(url)
                response = requests.get(url, params=payload)
                print (response.url)
                if response.status_code != 429:
                    break
                print("Status code is 429 so sleeping")
                time.sleep(100)
            if response.status_code != 200:
                print("response.status_code",response.status_code)
                temp = json.loads(response.text)
                print(temp['code'],temp['message'])
                continue
            temp = json.loads(response.text)
            print("Tag Name:",tag.tag_name,"status",temp['status'],"TotalResult:",temp['totalResults'])
            print("towards adder")
            adder(tag.tag_name, temp)

            #-----------------------------------------------------------------
            #----------------------------------------------------------------
            while True:
                payload = {'q':tag.tag_name,'sources':'bbc-news', 'sortBy':'popularity', 'apiKey':'838b62c7059448b0ad8383231c8ac614'}
                url = 'https://newsapi.org/v2/everything'
                print("\n\n",payload['sources'],"\n\n")
                print(url)
                response = requests.get(url, params=payload)
                print (response.url)
                if response.status_code != 429:
                    break
                print("Status code is 429 so sleeping")
                time.sleep(100)
            if response.status_code != 200:
                print("response.status_code",response.status_code)
                temp = json.loads(response.text)
                print(temp['code'],temp['message'])
                continue
            temp = json.loads(response.text)
            print("Tag Name:",tag.tag_name,"status",temp['status'],"TotalResult:",temp['totalResults'])
            print("towards adder")
            adder(tag.tag_name, temp)

            #-----------------------------------------------------------------
            #----------------------------------------------------------------
            while True:
                payload = {'q':tag.tag_name,'sources':'the-times-of-india', 'sortBy':'popularity', 'apiKey':'838b62c7059448b0ad8383231c8ac614'}
                url = 'https://newsapi.org/v2/everything'
                print("\n\n",payload['sources'],"\n\n")
                print(url)
                response = requests.get(url, params=payload)
                print (response.url)
                if response.status_code != 429:
                    break
                print("Status code is 429 so sleeping")
                time.sleep(100)
            if response.status_code != 200:
                print("response.status_code",response.status_code)
                temp = json.loads(response.text)
                print(temp['code'],temp['message'])
                continue
            temp = json.loads(response.text)
            print("Tag Name:",tag.tag_name,"status",temp['status'],"TotalResult:",temp['totalResults'])
            print("towards adder")
            adder(tag.tag_name, temp)

            #-----------------------------------------------------------------
            #----------------------------------------------------------------
            while True:
                payload = {'q':tag.tag_name,'sources':'the-hindu', 'sortBy':'popularity', 'apiKey':'838b62c7059448b0ad8383231c8ac614'}
                url = 'https://newsapi.org/v2/everything'
                print("\n\n",payload['sources'],"\n\n")
                print(url)
                response = requests.get(url, params=payload)
                print (response.url)
                if response.status_code != 429:
                    break
                print("Status code is 429 so sleeping")
                time.sleep(100)
            if response.status_code != 200:
                print("response.status_code",response.status_code)
                temp = json.loads(response.text)
                print(temp['code'],temp['message'])
                continue
            temp = json.loads(response.text)
            print("Tag Name:",tag.tag_name,"status",temp['status'],"TotalResult:",temp['totalResults'])
            print("towards adder")
            adder(tag.tag_name, temp)

            #-----------------------------------------------------------------
            #-----------------------------------------------------------------
            while True:
                payload = {'q':tag.tag_name, 'sortBy':'popularity', 'apiKey':'838b62c7059448b0ad8383231c8ac614'}
                url = 'https://newsapi.org/v2/everything'
                print("\n\n","everything","\n\n")
                print(url)

                response = requests.get(url, params=payload)

                print (response.url)
                if response.status_code != 429:
                    break
                print("Status code is 429 so sleeping")
                time.sleep(100)
            if response.status_code != 200:
                print("response.status_code",response.status_code)
                temp = json.loads(response.text)
                print(temp['code'],temp['message'])
                continue
            temp = json.loads(response.text)
            print("Tag Name:",tag.tag_name,"status",temp['status'],"TotalResult:",temp['totalResults'])
            print("towards adder")
            adder(tag.tag_name, temp)

        return


def adder(tagname, response):
    try:
        t = Tag.query.filter_by(tag_name = tagname).first()
        if t:
            for article in response['articles']:
                title = article['title']
                body = article['description']
                link = article['url']
                img_url = article['urlToImage']

                a = Article.query.filter_by(link=link).all()
                if a:
                    a=a[0]
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
        time.sleep(60*60*24)
        tags = Tag.query.all()
        list = []
        for tag in tags:
            list.append(tag.tag_name)
        tag_list.extend(list)
        time.sleep(60*60*24)
    return

Thread(target=parser).start()
Thread(target=update_loop).start()

db.create_all()
if "__main__" == __name__:
   app.run()
