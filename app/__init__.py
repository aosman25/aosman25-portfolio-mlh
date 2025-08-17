import os
from flask import Flask, render_template, redirect, url_for, request, jsonify
from dotenv import load_dotenv
import json
from peewee import *
import time
from urllib.parse import quote_plus
from playhouse.shortcuts import model_to_dict
from app.utils import generate_avatar
import re
from flask_redis import FlaskRedis
from faker import Faker


load_dotenv()
app = Flask(__name__)
fake = Faker()


if os.getenv("TESTING") == "true":
    import fakeredis
    print("Running in test mode")
    mydb = SqliteDatabase('file:memory?mode=memory&cache=shared', uri=True)
    # In-memory fake Redis client
    redis_client = fakeredis.FakeStrictRedis()
else:
    app.config['REDIS_URL'] = os.getenv('REDIS_URL')
    mydb = MySQLDatabase(os.getenv("MYSQL_DATABASE"),
                        user=os.getenv("MYSQL_USER"),
                        password=os.getenv("MYSQL_PASSWORD"),
                        host=os.getenv("MYSQL_HOST"),
                        port=3306)
    redis_client = FlaskRedis(app)
  

class TimelinePost(Model):
    name = CharField()
    email = CharField()
    content = TextField()
    created_at = BigIntegerField(default=lambda: int(time.time() * 1000), index=True)
    avatar_url = CharField()

    def save(self, *args, **kwargs):
        if not self.avatar_url:
            self.avatar_url = generate_avatar(self.email, self.name)
        return super().save(*args, **kwargs)

    class Meta:
        database = mydb

mydb.connect()
mydb.create_tables([TimelinePost])

with open("app/static/data/portfolio.json", "r", encoding="utf-8") as f:
    portfolio_data = json.load(f)

def populate_timeline_posts(n=100):
    for _ in range(n):
        name = fake.name()
        email = fake.email()
        content = fake.sentence(nb_words=12)

        TimelinePost.create(name=name, email=email, content=content)

@app.before_first_request
def init_db_population():
    if os.getenv("TESTING") == "false":
        populated = os.getenv("POPULATED_DB", "false").lower()
        if populated != "true":
            print("Populating database with fake timeline posts...")
            populate_timeline_posts(100)
        else:
            print("Skipping population because POPULATED_DB is set to true.")

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
    timeline_data = get_time_line_post()  # returns posts + cursors
    posts = timeline_data["timeline_posts"]
    next_cursor = timeline_data["next_cursor"]
    prev_cursor = timeline_data["prev_cursor"]

    return render_template(
        'pages/timeline.html',
        **portfolio_data,
        posts=posts,
        url=os.getenv("URL"),
        title="Timeline",
        next_cursor=next_cursor,
        prev_cursor=prev_cursor
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
    limit = request.args.get('limit', 4, type=int)
    cursor = request.args.get('cursor', None, type=int)
    direction = request.args.get('direction', 'next', type=str)
    cache_key = None
    
    if cursor:
        cache_key = f"timeline_post:limit={limit}:cursor={cursor}:direction={direction}"
        cached_response = redis_client.get(cache_key)
        if cached_response:
            return json.loads(cached_response)

    query = TimelinePost.select()
    if cursor:
        if direction == 'next':
            query = query.where(TimelinePost.created_at < int(cursor)) # Filter Rows based on the create_at timestamp
            query = query.order_by(TimelinePost.created_at.desc())
        elif direction == 'prev':
            query = query.where(TimelinePost.created_at > int(cursor))
            query = query.order_by(TimelinePost.created_at.asc())
    else:
        query = query.order_by(TimelinePost.created_at.desc())
    items = query.limit(limit)
    if direction == "prev":
        items = items[::-1]
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
    posts = [model_to_dict(p) for p in items]
    response = {'timeline_posts': posts, 'next_cursor': next_cursor, 'prev_cursor': prev_cursor}
    
    if cache_key:
        redis_client.set(cache_key, json.dumps(response), ex=3600)

    return response

@app.route('/api/timeline_post/<int:post_id>', methods=["DELETE"])
def delete_post(post_id):
    try:
        target_post = TimelinePost.get_by_id(post_id)
    except:
        return jsonify({"error": "Post Not Found!"}), 404
    TimelinePost.delete_by_id(post_id)
    return model_to_dict(target_post)

@app.route('/health', methods=['GET'])
def health_check():
    results = {}
    try:
        # Test portfolio pages including redirect for '/'
        page_routes = ['/', '/portfolio', '/technical-projects', '/hobbies', '/timeline']
        with app.test_client() as client:
            for route in page_routes:
                try:
                    resp = client.get(route, follow_redirects=True)  # Follow redirects
                    results[route] = {'status_code': resp.status_code, 'ok': resp.status_code == 200}
                except Exception as e:
                    results[route] = {'error': str(e)}

            # Test timeline API POST
            test_post_data = {
                'name': 'Health Check User',
                'email': 'healthcheck@example.com',
                'content': 'This is a test post for health check.'
            }
            post_resp = client.post('/api/timeline_post', data=test_post_data)
            if post_resp.status_code == 200:
                post_json = post_resp.get_json()
                results['/api/timeline_post POST'] = {'status_code': 200, 'post_id': post_json.get('id')}

                # Test timeline GET with cursor
                get_resp = client.get('/api/timeline_post', query_string={'limit': 1})
                results['/api/timeline_post GET'] = {'status_code': get_resp.status_code, 'ok': get_resp.status_code == 200}

                # Test DELETE
                delete_resp = client.delete(f"/api/timeline_post/{post_json.get('id')}")
                results['/api/timeline_post DELETE'] = {'status_code': delete_resp.status_code, 'ok': delete_resp.status_code == 200}
            else:
                results['/api/timeline_post POST'] = {'status_code': post_resp.status_code, 'ok': False}
        
        # Redis check
        try:
            redis_client.set('health_check', 'ok', ex=5)
            val = redis_client.get('health_check')
            results['redis'] = {'ok': val == b'ok' or val == 'ok'}
        except Exception as e:
            results['redis'] = {'error': str(e)}
        
        # DB connection check
        try:
            mydb.execute_sql('SELECT 1;')
            results['database'] = {'ok': True}
        except Exception as e:
            results['database'] = {'error': str(e)}
        
    except Exception as e:
        results['health_check'] = {'error': str(e)}
    
    return jsonify(results)

@app.errorhandler(404)
def page_not_found(e):
    return redirect(url_for('index'))