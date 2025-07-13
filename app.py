from dotenv import load_dotenv
from flask import Flask, render_template, redirect, url_for, flash, abort
from sqlalchemy.orm import DeclarativeBase, relationship, Mapped, mapped_column
from flask_login import LoginManager, login_user, UserMixin, current_user, logout_user
import os
from forms import RegisterForm, LoginForm, CreatePostForm, CommentForm
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Integer, String, Text, ForeignKey, Boolean, text
from typing import List
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from slugify import slugify
from functools import wraps
import hashlib
from flask_migrate import Migrate

if os.getenv("RENDER") is None:
    load_dotenv()

app = Flask(__name__)
secret = os.getenv("MY_SECRET_KEY")
if not secret:
    raise RuntimeError("Missing MY_SECRET_KEY! Set it in your environment variables.")
app.config["SECRET_KEY"] = secret

bootstrap = Bootstrap5(app)

#############################################
# Configure Flask login manager
#############################################
login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

def gravatar_url(email, size=50):
    email_hash = hashlib.md5(email.strip().lower().encode('utf-8')).hexdigest()
    return f"https://www.gravatar.com/avatar/{email_hash}?s={size}&d=identicon"

app.jinja_env.globals["gravatar_url"] = gravatar_url


def admin_only(function):
    @wraps(function) # Ensures the wrapped func keeps its name, docstring, etc so that tools like Flask (which uses route names) don’t get confused.
    # Without @wraps, Flask might think the route is called wrapper_function instead of delete_post, which breaks url_for() and debugging tools.
    def wrapper_function(*args, **kwargs):
        if current_user.admin == 1:
            return function(*args, **kwargs)
        else:
            return abort(403)
    return wrapper_function


#############################################
# Create database
#############################################
class Base(DeclarativeBase):
    pass

app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DB_URI", "sqlite:///posts.db")
db = SQLAlchemy(model_class=Base)
db.init_app(app)
migrate = Migrate(app, db)

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
    is_hidden: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("0"))

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

    post_id: Mapped[int] = mapped_column(
        ForeignKey("blog_posts.id"), nullable=False
    )
    parent_post: Mapped["BlogPost"] = relationship(back_populates="comments")

#############################################
# Routes
#############################################

# TODO: Protect routes
# TODO: Figure out how to create admin user


# Home page
@app.route("/")
def home():
    return render_template("index.html")

# Blog main page
@app.route("/blog")
def blog_posts():
    result = db.session.execute(
        db.select(BlogPost).where(BlogPost.is_hidden == False).order_by(BlogPost.date.desc())
    )
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

# Login user
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
            return redirect(url_for("home"))
        else:
            print("Something is amiss")
    return render_template("login.html", form=login_form)

# Logout user
@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("home"))

# Add a new post. Admin only function.
@app.route("/new-post", methods=["GET", "POST"])
@admin_only
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

# Show post detail in a new page
@app.route("/post/<slug>", methods=["GET", "POST"])
def show_post(slug):
    comment_form = CommentForm()
    requested_post = db.session.execute(db.Select(BlogPost).where(BlogPost.slug == slug)).scalar_one_or_none()
    if comment_form.validate_on_submit():
        new_comment = Comment(
            comment = comment_form.comment.data,
            comment_author = current_user,
            parent_post = requested_post
        )
        db.session.add(new_comment)
        db.session.commit()
        
        return redirect(url_for("show_post", slug=slug))    
    return render_template("post.html", post=requested_post, form=comment_form)
    
# Mark a post is_hidden so as to not render it in the blog_posts page    
@app.route("/delete-post/<int:post_id>", methods=["POST"])
@admin_only
def delete_post(post_id):
    post_to_hide = db.get_or_404(BlogPost, post_id)
    post_to_hide.is_hidden = True    
    db.session.commit()
    return redirect(url_for("blog_posts"))

# Edit an existing post
@app.route("/edit-post/<slug>", methods=["GET", "POST"])
@admin_only
def edit_post(slug):
    post = db.session.execute(db.Select(BlogPost).where(BlogPost.slug == slug)).scalar_one_or_none()
    edit_form = CreatePostForm(
        title=post.title,
        subtitle=post.subtitle,
        img_url=post.img_url or "",
        body=post.body
    )
    if edit_form.validate_on_submit():
        post.title = edit_form.title.data
        post.subtitle = edit_form.subtitle.data
        post.img_url = edit_form.img_url.data
        post.author = current_user
        post.body = edit_form.body.data
        
        db.session.commit()
        return redirect(url_for("show_post", slug=slug))
        
    return render_template("new-post.html", post=post, form=edit_form, is_edit=True)

# TODO: Sandbox page route

# TODO: Admin panel route

# TODO: Wire up contact form and explore mail handling applications.


if __name__ == "__main__":
    app.run(debug=True)
