from dotenv import load_dotenv
from flask import Flask, render_template
import os

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("MY_SECRET_KEY")


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/blog")
def blog_posts():
    dummy_posts = [
        {
            "id": 1,
            "title": "Getting started with Flask",
            "subtitle": "A quick walkthrough or routes, views and templates.",
            "author": {"name": "David Deal"},
            "date": "June 25, 2025",
        },
        {
            "id": 2,
            "title": "Test 2",
            "subtitle": "Just testing layout.",
            "author": {"name": "David Deal"},
            "date": "June 26, 2025",
        },
        {
            "id": 3,
            "title": "Test 3",
            "subtitle": "Before setting up the DB.",
            "author": {"name": "David Deal"},
            "date": "June 27, 2025",
        },
        {
            "id": 4,
            "title": "Test 4",
            "subtitle": "And then maybe deploy.",
            "author": {"name": "David Deal"},
            "date": "June 28, 2025",
        },
    ]
    return render_template("blog.html", all_posts=dummy_posts)


if __name__ == "__main__":
    app.run(debug=True)
