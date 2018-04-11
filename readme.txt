Steps to deploy project on localhost:

Pre-requirement :

* Linux Based OS, postgresql environment with "pgadmin" GUI client.
* Set-up project virtual environment to venv given in project directory
  by command "source ./venv/bin/activate"
*   To install postgresql enter this command in terminal:

    *) sudo apt-get update
    *) sudo apt-get install postgresql postgresql-contrib

* Download pgadmin from software center directly and create database named "p8" from GUI this GUI tool.



1) First complete deployment of Pconsume project.
2) Open terminal in current directory.
3) Run command : "python3 app.py".
4) It will start server on localhost:5001.
5) Open any web browser and enter url "localhost:5000", this will open site.

* To reset python environment to main global computer environment:
  by command "deactivate"
