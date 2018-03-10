from app import *

db.create_all()

s1 = Source(title = 'Nasa')
s2 = Source(title = 'Manglasa')

db.session.add(s1)
db.session.add(s2)

db.session.commit()


a1 = Article(title= 'Mango',body="Tjos os mango", source_id=1)
a2 = Article(title= 'os Mango',body="Tjos sdfsdf s   os mango", source_id=2)
a3 = Article(title= 'security Mango',body="Tjos os maasdfasdf asdf ngo", source_id=1)

t1 = Tag(tag_name = "Mango")
t2 = Tag(tag_name = "security")

db.session.add(a1)
db.session.add(a2)
db.session.add(a3)
db.session.add(t1)
db.session.add(t2)

db.session.commit()

//

t = Tag.query.all()
a = Article.query.all()

t1 = t[0]
t2 = t[1]

a1 = a[0]
a2 = a[1]
a3 = a[2]
