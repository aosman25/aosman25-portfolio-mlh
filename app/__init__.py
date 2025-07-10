import os
from flask import Flask, render_template, redirect, url_for, request, jsonify
from dotenv import load_dotenv
import json
from peewee import *
import datetime
from playhouse.shortcuts import model_to_dict

load_dotenv()
app = Flask(__name__)

mydb = MySQLDatabase(os.getenv("MYSQL_DATABASE"), 
                     user=os.getenv("MYSQL_USER"),
                     password=os.getenv("MYSQL_PASSWORD"),
                     host=os.getenv("MYSQL_HOST"),
                     port=3306)

class TimelinePost(Model):
    name = CharField()
    email = CharField()
    content = TextField()
    created_at = DateTimeField(default=datetime.datetime.now)

    class Meta:
        database = mydb

mydb.connect()
mydb.create_tables([TimelinePost])

with open("app/static/data/portfolio.json", "r", encoding="utf-8") as f:
    portfolio_data = json.load(f)

@app.route('/')
def index():
    return redirect(url_for('portfolio'))

@app.route('/portfolio')
def portfolio():
    return render_template('index.html', **portfolio_data, url=os.getenv("URL"))

@app.route('/technical-projects')
def technical_projects():
    return render_template('pages/technical-projects.html', **portfolio_data, url=os.getenv("URL"))

@app.route('/hobbies')
def hobbies():
    return render_template('pages/hobbies.html', **portfolio_data, url=os.getenv("URL"))

@app.route('/api/timeline_post', methods=['POST'])
def post_time_line_post():
    name = request.form['name']
    email = request.form['email']
    content = request.form['content']
    timeline_post = TimelinePost.create(name=name, email=email, content=content)

    return model_to_dict(timeline_post)

@app.route('/api/timeline_post', methods=['GET'])
def get_time_line_post():
    return {
        'timeline_posts': [
            model_to_dict(p)
            for p in 
            TimelinePost.select().order_by(TimelinePost.created_at.desc())
        ]
    }

@app.route('/api/timeline_post/<int:post_id>', methods=["DELETE"])
def delete_post(post_id):
    try:
        target_post = TimelinePost.get_by_id(post_id)
    except:
        return jsonify({"error": "Post Not Found!"}), 404
    TimelinePost.delete_by_id(post_id)
    return model_to_dict(target_post)

@app.errorhandler(404)
def page_not_found(e):
    return redirect(url_for('index'))