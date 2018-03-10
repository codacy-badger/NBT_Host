from flask import Flask,abort, redirect, request, render_template
from flask_sqlalchemy import SQLAlchemy

import feed
import datetime

from threading import Thread
import time

app = Flask(__name__)
app.debug = True
db_uri = 'postgresql://user1:0233@localhost/test'
app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

with app.app_context():
    db.create_all()

tagger = db.Table('tagger',
            db.Column('id', db.Integer, primary_key=True),
            db.Column('tag_id', db.Integer, db.ForeignKey('tag.id')),
            db.Column('article_id', db.Integer, db.ForeignKey('article.id'))
)

class Article(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.Text, nullable=False)
    body = db.Column(db.Text, nullable=False)
    source_id = db.Column(db.Integer, db.ForeignKey('source.id'), nullable=False)
    source = db.relationship('Source', backref=db.backref('articles', lazy=True))


class Source(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.Text, nullable=False)

class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tag_name = db.Column(db.Text, nullable=False)
    articles = db.relationship('Article', secondary= tagger, backref= db.backref('tags',lazy=True))
