from app import db
from sqlalchemy import Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column
from flask_login import UserMixin
from typing import List
from datetime import datetime


# Configure tables
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
