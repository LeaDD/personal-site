from dotenv import load_dotenv
from flask import Flask, render_template, redirect, url_for, flash
from sqlalchemy.orm import DeclarativeBase, relationship, Mapped, mapped_column
from flask_login import LoginManager, login_user, UserMixin, current_user, logout_user
import os
from forms import RegisterForm, LoginForm, CreatePostForm
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Integer, String, Text, ForeignKey
from typing import List
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from slugify import slugify


load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("MY_SECRET_KEY", "dev_key_for_local_testing")

bootstrap = Bootstrap5(app)

#############################################
# Configure Flask login manager
#############################################
login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


def admin_only(function):
    @wraps(function)
    def wrapper_function(*args, **kwargs):
        if current_user.admin == 1:
            return function()
        else:
            return abort(403)
    return wrapper_function


# TODO: gravatar

#############################################
# Create database
#############################################
class Base(DeclarativeBase):
    pass

app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DB_URI", "sqlite:///posts.db")
db = SQLAlchemy(model_class=Base)
db.init_app(app)

#############################################
# Configure models
#############################################
class User(UserMixin, db.Model):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(100), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    admin: Mapped[bool] = mapped_column(default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    posts: Mapped[List["BlogPost"]] = relationship(back_populates="author")
    comments: Mapped[List["Comment"]] = relationship(back_populates="comment_author")


class BlogPost(db.Model):
    __tablename__ = "blog_posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    author: Mapped["User"] = relationship(back_populates="posts")

    title: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    subtitle: Mapped[str] = mapped_column(String(250), nullable=False)
    date: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow, onupdate=datetime.utcnow
    )
    is_published: Mapped[bool] = mapped_column(default=True, nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    img_url: Mapped[str] = mapped_column(String(250), nullable=True)
    slug: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)

    comments: Mapped[List["Comment"]] = relationship(
        back_populates="parent_post",
        cascade="all, delete",  # Auto delete comments if a post is deleted
    )

    def generate_slug(self):
        self.slug = slugify(self.title)


class Comment(db.Model):
    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    comment: Mapped[str] = mapped_column(String(1000), nullable=False)

    commenter_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    comment_author: Mapped["User"] = relationship(back_populates="comments")
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    post_id: Mapped["BlogPost"] = mapped_column(
        ForeignKey("blog_posts.id"), nullable=False
    )
    parent_post: Mapped["BlogPost"] = relationship(back_populates="comments")

#############################################
# Routes
#############################################

# TODO: Admin only wrapper
# TODO: Protect routes
# TODO: Figure out how to create admin user
# TODO: Hide sandbox and admin panel buttons


# Home page
@app.route("/")
def home():
    return render_template("index.html")

# Blog main page
@app.route("/blog")
def blog_posts():
    print(current_user.admin)
    result = db.session.execute(db.select(BlogPost).order_by(BlogPost.date.desc()))
    posts=result.scalars().all()
    return render_template("blog.html", all_posts=posts)

# Register new user
@app.route("/register", methods=["GET", "POST"])
def register():
    registration_form = RegisterForm()
    if registration_form.validate_on_submit():
        user_email = registration_form.email.data
        if db.session.execute(db.Select(User).where(User.email == user_email)).scalar_one_or_none():
            flash("An account with that email is already registered. Please login.")
            return redirect(url_for("login"))
        else:
            hashed_and_salted_pw = generate_password_hash(
                registration_form.password.data, method="pbkdf2:sha256", salt_length=10
            )
            new_user = User(
                email=user_email,
                password=hashed_and_salted_pw,
                name=registration_form.name.data,
            )
            db.session.add(new_user)
            db.session.commit()

            login_user(new_user)
            return redirect(url_for("blog_posts"))
    return render_template("register.html", form=registration_form)

@app.route("/login", methods=["GET", "POST"])
def login():
    login_form = LoginForm()
    if login_form.validate_on_submit():
        email = login_form.email.data
        password = login_form.password.data
        
        # Find user by the email entered to see if they are registered
        user = db.session.execute(db.Select(User).where(User.email == email)).scalar_one_or_none()
        
        if not user:
            flash("Sorry, that email is not registered.")
        elif not check_password_hash(user.password, password):
            flash("Sorry, that password is invalid. Please try again.")
        elif check_password_hash(user.password, password):
            login_user(user)
            print(current_user.is_authenticated)
            return redirect(url_for("home"))
        else:
            print("Something is amiss")
    return render_template("login.html", form=login_form)

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("home"))

@app.route("/new-post", methods=["GET", "POST"])
def new_post():
    print(current_user.is_authenticated)
    form = CreatePostForm()
    if form.validate_on_submit():
        new_post = BlogPost(
            title = form.title.data,
            subtitle = form.subtitle.data,
            body = form.body.data,
            img_url = form.img_url.data or "",
            author = current_user
        )
        new_post.generate_slug()
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for("blog_posts"))
    return render_template("new-post.html", form=form)

# TODO: View post route

@app.route("/post/<int:post_id>", methods=["GET", "POST"])
def show_post(post_id):
    requested_post = db.get_or_404(BlogPost, post_id)
    return render_template("post.html", post=requested_post)
    


if __name__ == "__main__":
    app.run(debug=True)
