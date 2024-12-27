from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField, RadioField, DateField, IntegerField
from wtforms.validators import DataRequired, EqualTo
from datetime import datetime, timezone



class AddSchoolForm(FlaskForm):
    location = StringField('School location: ')
    submit = SubmitField('Add this school')

class AddStudentForm(FlaskForm):
    first_name = StringField('First Name: ')
    last_name = StringField('Last Name: ')
    rank = SelectField('Current Rank: ', choices=[
                       'triple stripe', '1', '2', '3', '4', '5', '6', '7', '8'], validators=[DataRequired()])
    recerts = IntegerField('Number of completed Recertifications: ', default=0)
    DOB  = DateField('Date of Birth: ', validators=[DataRequired()])
    school_id = SelectField('School: ', coerce=int)
    which_test = SelectField('Which test? ', choices=['regular test','makeup test','not testing'])
    submit = SubmitField('Add this student.')

class AddTestForm(FlaskForm):
    testing_date  = DateField('Date: ', format='%Y-%m-%d')
    testing_number = IntegerField('Testing Number: ')
    submit = SubmitField('Save this Test')

class LoginForm(FlaskForm):
    username = StringField('Username:  ', validators=[DataRequired()])
    password = PasswordField('Password:  ')
    remember = BooleanField('Remember Me')
    submit = SubmitField('Sign in')

