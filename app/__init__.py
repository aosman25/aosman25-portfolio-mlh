import os
from flask import Flask, render_template,  redirect, url_for
from dotenv import load_dotenv
import json

load_dotenv()
app = Flask(__name__)

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
