import os

from dotenv import load_dotenv
from flask import render_template
from flask import Flask

load_dotenv()
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

@app.route("/")
def home():
    return render_template(
        "index.html"
    )