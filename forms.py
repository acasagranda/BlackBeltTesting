from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField, RadioField, DateField, IntegerField
from wtforms.validators import DataRequired, EqualTo
from datetime import datetime, timezone



class AddSchoolForm(FlaskForm):
    location = StringField('School location: ')
    submit = SubmitField('Save this school')

class AddStudentForm(FlaskForm):
    first_name = StringField('First Name: ')
    last_name = StringField('Last Name: ')
    rank = SelectField('Current Rank: ', choices=[
                       'triple stripe', '1', '2', '3', '4', '5', '6', '7', '8'], validators=[DataRequired()])
    recerts = IntegerField('Number of completed Recertifications: ', default=0)
    DOB  = DateField('Date of Birth: ', validators=[DataRequired()])
    school_id = SelectField('School: ', coerce=int)
    which_test = SelectField('Which test? ', choices=['regular test','makeup test','not testing'])
    current = BooleanField('Currently a Student (uncheck to put in Archives): ')
    submit = SubmitField('Save this student.')

class StudentTestForm(FlaskForm):
    rank = SelectField('Current Rank: ', choices=[
                       'triple stripe', '1', '2', '3', '4', '5', '6', '7', '8'], validators=[DataRequired()])
    recerts = IntegerField('Number of completed Recertifications: ', default=0)
    level = SelectField('Level: ', choices = ["Adult","Junior"])
    submit = SubmitField('Edit this student.')
    
class PasswordForm(FlaskForm):
    oldpassword=PasswordField('Old Password',validators=[DataRequired()] )
    password=PasswordField('New Password', validators=[DataRequired()])
    password2=PasswordField('Repeat New Password', validators=[DataRequired(), EqualTo('password')])
    submit=SubmitField('Change Password')


class EmailForm(FlaskForm):
    email=StringField('Email')
    submit=SubmitField('Request username and temporary password.')

class AddTestForm(FlaskForm):
    testing_date  = DateField('Date: ', format='%Y-%m-%d')
    testing_number = IntegerField('Testing Number: ')
    submit = SubmitField('Save this Test')

class AddUserForm(FlaskForm):
    first_name = StringField('First Name: ')
    last_name = StringField('Last Name: ')
    email = StringField('Email (username): ')
    temp_password = StringField("Temporary Password: ")
    school_id = SelectField('School: ', coerce=int)
    role = SelectField('role', choices = ['instructor', 'admin'])
    submit = SubmitField('Save this user.')

class LoginForm(FlaskForm):
    email = StringField('Email (Username):  ', validators=[DataRequired()])
    password = PasswordField('Password:  ')
    remember = BooleanField('Remember Me')
    submit = SubmitField('Sign in')

