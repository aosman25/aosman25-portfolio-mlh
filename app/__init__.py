import os
from flask import Flask, render_template, request
from dotenv import load_dotenv
import json

load_dotenv()
app = Flask(__name__)

with open("app/static/data/portfolio.json", "r", encoding="utf-8") as f:
    portfolio_data = json.load(f)

@app.route('/')
def index():
    return render_template('index.html', **portfolio_data, url=os.getenv("URL"))

@app.route('/hobbies')
def hobbies():
    return render_template('pages/hobbies.html', **portfolio_data, url=os.getenv("URL"))
