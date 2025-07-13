from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, URL, Optional


class RegisterForm(FlaskForm):
    name = StringField("Your Name", validators=[DataRequired()])
    email = StringField("Your Email", validators=[DataRequired(), Email()])
    password = PasswordField("Enter a password", validators=[DataRequired()])
    submit = SubmitField("Register")


class LoginForm(FlaskForm):
    email = StringField("Enter your email", validators=[DataRequired(), Email()])
    password = PasswordField("Enter your password", validators=[DataRequired()])
    login = SubmitField("Login")


class CreatePostForm(FlaskForm):
    title = StringField("Blog Post Title", validators=[DataRequired()])
    subtitle = StringField("Subtitle", validators=[DataRequired()])
    img_url = StringField("Blog Image URL (optional)", validators=[URL(), Optional()])
    body = TextAreaField("Blog Content", validators=[DataRequired()])
    submit = SubmitField("Submit Post")
    
class CommentForm(FlaskForm):
    comment = TextAreaField("Comment", validators=[DataRequired()])
    submit = SubmitField("Submit Comment")
    
class ContactForm(FlaskForm):
    name = StringField("Your Name", validators=[DataRequired()])
    email = StringField("Your Email", validators=[DataRequired(), Email()])
    message = StringField("Message", validators=[DataRequired()])
    submit = SubmitField("Send")
