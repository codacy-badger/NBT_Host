import feedparser

def parse(url):
    return feedparser.parse(url)

def get_source(parsed):
    feed = parsed['feed']
    return {
        'link': feed['link'],
        'title': feed['title'],
        'subtitle': feed['subtitle'],
    }

def get_articles(parsed,type=1):

    articles = []


    if type == 1 :                                  

        entries = parsed['entries']
        for entry in entries:
            articles.append({
                'id': entry['id'],
                'link': entry['link'],
                'title': entry['title'],
                'summary': entry['summary'],
            #   'published': entry['published],
            })


    elif type == 2 :
        pass
        
    return articles
