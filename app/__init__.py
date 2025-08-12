import os
from flask import Flask, render_template, redirect, url_for, request, jsonify
from dotenv import load_dotenv
import json
from peewee import *
import time
import hashlib
from urllib.parse import quote_plus
from playhouse.shortcuts import model_to_dict
import re


  

load_dotenv()
app = Flask(__name__)

if os.getenv("TESTING") == "true":
    print("Running in test mode")
    mydb = SqliteDatabase('file:memory?mode=memory&cache=shared', uri=True)
else:
    mydb = MySQLDatabase(os.getenv("MYSQL_DATABASE"),
                        user=os.getenv("MYSQL_USER"),
                        password=os.getenv("MYSQL_PASSWORD"),
                        host=os.getenv("MYSQL_HOST"),
                        port=3306)
  

class TimelinePost(Model):
    name = CharField()
    email = CharField()
    content = TextField()
    created_at = BigIntegerField(
        default=lambda: int(time.time() * 1000),  # milliseconds
        index=True
    )

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
    return render_template('index.html', **portfolio_data, url=os.getenv("URL"), title="MLH Fellow")

@app.route('/technical-projects')
def technical_projects():
    return render_template('pages/technical-projects.html', **portfolio_data, url=os.getenv("URL"), title="Technical Projects")

@app.route('/hobbies')
def hobbies():
    return render_template('pages/hobbies.html', **portfolio_data, url=os.getenv("URL"), title="Hobbies")

@app.route('/timeline')
def timeline():
    posts = get_time_line_post()["timeline_posts"]
    avatar_base_url = "https://gravatar.com/avatar"
    avatars = {}
    

    for p in posts:
        p["email"] = p["email"].lower().strip()
        email = p["email"]
        name = p.get("name", "User")
        if email not in avatars:
            ui_avatar_path = f"/{quote_plus(name)}/128/0D8ABC/FFFFFF/2/0.35/true/true/false/png"
            fallback_url = f"https://ui-avatars.com/api{ui_avatar_path}"
            fallback_url_encoded = quote_plus(fallback_url)

            hashed_email = hashlib.md5(email.encode('utf-8')).hexdigest()
            avatars[email] = f"{avatar_base_url}/{hashed_email}?d={fallback_url_encoded}"
    return render_template(
        'pages/timeline.html',
        **portfolio_data,
        posts=posts,
        avatars=avatars,
        url=os.getenv("URL"),
        title="Timeline"
    )


@app.route('/api/timeline_post', methods=['POST'])
def post_time_line_post():
    name = request.form.get('name', '')
    email = request.form.get('email', '')
    content = request.form.get('content', '')
    
    # Validate name
    if not name or not name.strip():
        return "Invalid name", 400
    
    # Validate email format
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not email or not re.match(email_pattern, email):
        return "Invalid email", 400
    
    # Validate content
    if not content or not content.strip():
        return "Invalid content", 400
    
    timeline_post = TimelinePost.create(name=name, email=email, content=content)

    return model_to_dict(timeline_post)

@app.route('/api/timeline_post', methods=['GET'])
def get_time_line_post():
    limit = request.args.get('limit', 10, type=int)
    cursor = request.args.get('cursor', None, type=int)
    direction = request.args.get('direction', 'next', type=str)
    query = TimelinePost.select()
    if cursor:
        if direction == 'next':
            query = query.where(TimelinePost.created_at < int(cursor)) # Filter Rows based on the create_at timestamp
        elif direction == 'prev':
            query = query.where(TimelinePost.created_at > int(cursor))
    
    query = query.order_by(TimelinePost.created_at.desc())
    items = query.limit(limit)
    if items:
        first_item_cursor = items[0].created_at
        last_item_cursor = items[-1].created_at
        has_next = TimelinePost.select().where(TimelinePost.created_at < last_item_cursor).exists()
        has_prev = TimelinePost.select().where(TimelinePost.created_at > first_item_cursor).exists()
        prev_cursor = first_item_cursor if has_prev else None
        next_cursor = last_item_cursor if has_next else None
    else:
        prev_cursor = None
        next_cursor = None
    response = {'timeline_posts': [model_to_dict(p) for p in items], 'next_cursor': next_cursor, 'prev_cursor': prev_cursor}
    return response

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