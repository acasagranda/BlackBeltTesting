from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField, RadioField
from wtforms.validators import DataRequired, EqualTo

class LoginForm(FlaskForm):
    username = StringField('Username:  ', validators=[DataRequired()])
    password = PasswordField('Password:  ')
    remember = BooleanField('Remember Me')
    submit = SubmitField('Sign in')