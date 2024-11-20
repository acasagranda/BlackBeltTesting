import os
# import csv

from datetime import datetime, timezone, date
from dotenv import load_dotenv
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

app.config['SECRET_KEY'] = os.getenv('skey')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('MYPROJECT_DBURL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


login_manager = LoginManager()
login_manager.init_app(app)



class Certificate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    test_id = db.Column(db.Integer, db.ForeignKey('test.id'), nullable=False)
    studenttest_id = db.Column(db.Integer, db.ForeignKey('student_test.id'), nullable=False)
    new_rank = db.Column(db.Integer)


class School(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    location = db.Column(db.String(50), unique=True)
    students = db.relationship('Student', backref=db.backref('school'), order_by="Student.last_name,Student.first_name")
    

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100), index=True)
    DOB = db.Column(db.DateTime())
    school_id = db.Column(db.Integer, db.ForeignKey('school.id'), nullable=False)
    rank = db.Column(db.Integer)
    recerts = db.Column(db.Integer)
    current = db.Column(db.Boolean, default=True)
    extra = db.Column(db.String(100))


class StudentTest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    test_id = db.Column(db.Integer, db.ForeignKey('test.id'), nullable=False)
    level = db.Column(db.String(10), index=True)
    testing_up = db.Column(db.Boolean, default=False)
    makeup_test = db.Column(db.Boolean, default=False)    #regular is False, makeup is true
    passed_regular = db.Column(db.Boolean, default=False)
    passed_makeup = db.Column(db.Boolean, default=False)
    limbo = db.Column(db.Boolean, default=False)  # just make limbo

    

class Test(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    testing_date = db.Column(db.DateTime())
    testing_number = db.Column(db.Integer)
    students = db.relationship('StudentTest', backref=db.backref('test'))

    

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True)
    password_hash = db.Column(db.String(228))
    role = db.Column(db.String(10), default='instructor')
    extra = db.Column(db.String(100))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    

def makeme():
    p = generate_password_hash('and')
    me = User(password_hash=p, role='admin', username='andrea')
    db.session.add(me)
    db.session.commit()

def makenonadmin():
    p = generate_password_hash('and')
    me = User(password_hash=p, username='nonadmin')
    db.session.add(me)
    db.session.commit()

def starttest():
    first = Test(testing_date=date(2024, 10, 12),testing_number=100)
    db.session.add(first)
    db.session.commit()



import routes
