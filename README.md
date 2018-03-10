#Phost# is the api hosting program via which we will get new news by giving tagname and it will return whole bunch of news from various already provided source of rss feed urls.





 *)  How to deploy it ?

->  Open terminal in current repository then fire command 
            python3 app.py
    and it will run web server of flask and application will be hosted at " IP: localhost(127.0.0.1), port: 5000 "
    
 **  API **

1) /news/tagname/<tag-name>
2) /news/tagid/<tag-id>

3) /tag/add/<tag-name>
4) /tag/delete/tagname/<tag-name>
5) /tag/delete/tagid/<tag-id>
6) /tag/trending/<top-row-no>

