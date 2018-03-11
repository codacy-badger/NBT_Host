from flask import Flask,abort,jsonify, redirect, request, render_template
from flask_sqlalchemy import SQLAlchemy

# sqlalchey full text searchabal imports

import feed
import datetime
#import flask_whooshalchemy as wa
from threading import Thread
import time

app = Flask(__name__)
app.debug = True
db_uri = 'postgresql://user1:0233@localhost/feedreader'
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
    tag_name = db.Column(db.Text, nullable=False)
    articles = db.relationship('Article', secondary= tagger, backref= db.backref('tags',lazy=True))
    #users = db.relationship('User', secondary= connector, backref= db.backref('tags',lazy=True)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name =  db.Column(db.Text, nullable=False)
    username = db.Column(db.Text, nullable=False)
    password = db.Column(db.Text, nullable=False)
    tags = db.relationship('Tag', secondary= connector, backref= db.backref('users',lazy=True))


class Article(db.Model):

   # __searchable__ = ['title','body']


    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.Text, nullable=False)
    body = db.Column(db.Text, nullable=False)
    link = db.Column(db.Text, nullable=False)
    guid = db.Column(db.String(255), nullable=False)
    unread = db.Column(db.Boolean, default=True, nullable=False)
    source_id = db.Column(db.Integer, db.ForeignKey('source.id'), nullable=False)
    source = db.relationship('Source', backref=db.backref('articles', lazy=True))
    date_added = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    #search_vector = db.Column(TSVectorType('title', 'body'))  # changing sa(sqlalchemy) to db


    #date_published = db.Column(db.DateTime)
    __table_args__ = (
        db.UniqueConstraint('source_id', 'guid', name='uc_source_guid'),
    )

    @classmethod
    def insert_from_feed(cls, source_id, feed_articles):
        stmt = Article.__table__.insert()
        articles = []
        for article in feed_articles:
            articles.append({
                'title': article['title'],
                'body': article['summary'],
                'link': article['link'],
                'guid': article['id'],
                'source_id': source_id,
                #'date_published': article['published']
            })
        db.engine.execute(stmt, articles)



class Source(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.Text, nullable=False)
    subtitle = db.Column(db.Text, nullable=False)
    link = db.Column(db.Text, nullable=False)
    feed = db.Column(db.Text, nullable=False)
    date_added = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    @classmethod
    def insert_from_feed(cls, feed, feed_source):
        link = feed_source['link']
        title = feed_source['title']
        subtitle = feed_source['subtitle']
        source = Source(feed=feed, link=link, title=title, subtitle=subtitle)
        db.session.add(source)
        db.session.commit()
        return source

#wa.whoosh_index(app, Article)


#########################################################################


@app.route('/', methods=['GET'])
def index_get():
    query = Article.query
    query = query.filter(Article.unread == True)
    orderby = request.args.get('orderby', 'added')
    if orderby == 'added':
        query = query.order_by(Article.date_added.desc())
    #elif orderby == 'published':
    #    query = query.order_by(Article.date_published.desc())
    elif orderby == 'title':
        query = query.order_by(Article.title)
    elif orderby == 'source':
        query = query.join(Source).order_by(Source.title)
    articles = query.all()
    return render_template('index.html', articles=articles)

@app.route('/read/<int:article_id>', methods=['GET'])
def read_article_get(article_id):
    article = Article.query.get(article_id)
    article.unread = False
    db.session.commit()
    return redirect(article.link)

@app.route('/sources', methods=['GET'])
def sources_get():
    query = Source.query
    query = query.order_by(Source.title)
    sources = query.all()
    return render_template('sources.html', sources=sources)

@app.route('/sources', methods=['POST'])
def sources_post():
    feed_url = request.form['feed']
    parsed = feed.parse(feed_url)
    feed_source = feed.get_source(parsed)
    source = Source.insert_from_feed(feed_url, feed_source)
    feed_articles = feed.get_articles(parsed)
    Article.insert_from_feed(source.id, feed_articles)
    return redirect('/sources')

####################################################################


@app.route('/news/tagid/<int:id>', methods=['GET'])
def tag_id_get(id):

    tag =  Tag.query.filter_by(id = id).first()

    if tag == None:
         return jsonify({'msg':"Tag is not found"})

    articles = tag.articles
    response = []
    for article in articles:
        res = {}

        res['id'] = article.id
        res['title'] = article.title
        res['body'] = article.body
        res['link'] = article.link
        #res['added'] = article.date_added
        #res[] = article.

        response.append(res)


    return jsonify({'response' : response })


@app.route('/news/tagname/<name>', methods=['GET'])
def tag_name_get(name):


    tag =  Tag.query.filter_by(tag_name = name).first()

    if tag == None:
         return jsonify({'msg':"Tag is not found"})

    articles = tag.articles
    response = []
    for article in articles:
        res = {}

        res['id'] = article.id
        res['title'] = article.title
        res['body'] = article.body
        res['link'] = article.link
        res['added'] = article.date_added
        #res[] = article.

        response.append(res)


    return jsonify({'response' : response })


@app.route('/tag/add/<user_name>/<tag_name>', methods=['GET'])
def tag_add_get(user_name, tag_name):

    user = User.query.filter_by(username=user_name).first()
    tag = Tag(tag_name = tag_name)
    tag.users.append(user)
    db.session.add(tag)
    db.session.commit()

    #index_one(tag)

    res = {}
    res["tag_name"] = tag.tag_name
    res["id"]= tag.id
    res['username']=user.username
    return jsonify( {'added_tag': res } )


@app.route('/tag/delete/<int:id>', methods=['GET'])
def tag_delete_get(id):

    if id == 0:
        db.session.query(Tag).delete()
        db.session.commit()
        return jsonify({'msg':"Deleted all tags"})

    tag = Tag.query.filter(Tag.id == id).first()

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


    tags = Tag.query.limit(top)
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

#####################################################################################
#sign in and SignOut and SignUp

@app.route('/signup', methods=['POST','GET'])
def tag_signup_post():
    username = request.form['username']
    name = request.form['name']
    password = request.form['password']

    user = User(username = username, name=name, password=password)
    db.session.add(user)
    db.session.commit()

    t={'userid': user.id,
        'username' : user.name,
       }

    return jsonify( {'result': t} )



@app.route('/signin', methods=['POST','GET'])
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


#General Function



def index_one(tag):
    # indexing each tag by searching
    return

def index_all():
    #started index
    return

def update_source(src):
    parsed = feed.parse(src.feed)
    feed_articles = feed.get_articles(parsed) # type is default argument which shows formate to be extracted from the parsed data
    Article.insert_from_feed(src.id, feed_articles)
    print('Updated ' + src.feed)


def update_loop():
    while True:
        with app.app_context():
            query = Source.query    # get all sources
            for src in query.all():
                try:
                    update_source(src)  # update news of sources one by one
                except:
                    continue

        t = Thread(target=index_all)
        t.start()        # indexting all tags with given articles

        time.sleep(5)


thread = Thread(target=update_loop)
thread.start()

if "__main__" == __name__:
    app.run()
