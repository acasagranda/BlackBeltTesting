# import csv
# import os
# import smtplib
# import string

from app import app, db, Certificate, School, Student, StudentTest, Test, User, login_manager  # Archive
# from collections import defaultdict
from datetime import datetime, timezone, timedelta
from flask import request, render_template, flash, redirect, url_for
from flask_login import current_user, login_user, logout_user, login_required
from forms import AddSchoolForm, AddStudentForm, AddTestForm, LoginForm  #, EmailForm2, PasswordForm2, AddstudentForm2, RegistrationForm2
# from secrets import choice



@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))


def adminonly(func):
    def wrapper():
        if current_user.role != 'admin':
            flash("You do not have access to that page")
            return redirect(url_for('options'))
        return func()
    return wrapper


# sign in page
@app.route('/', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if request.method == "POST":
        if form.validate_on_submit():
            user = User.query.filter_by(username=form.username.data).first()
            if user and user.check_password(form.password.data):
                login_user(user, remember=form.remember.data)
                # next_page = request.args.get('next')
                return redirect(url_for('options'))
        flash("Username or password is incorrect. Please try again.")
        return redirect(url_for('login'))

    return render_template('login.html', form=form)

@app.route("/addschool", methods=['GET', 'POST'], endpoint='addschool')
@login_required
@adminonly
def addschool():
    form = AddSchoolForm()
    if request.method == 'POST':
        if form.validate_on_submit:
            location = form.location.data
            db.session.add(School(location=location))
            db.session.commit()
            flash("New School has been added")
            return redirect(url_for('addschool'))
    return render_template('addschool.html', form=form)


@app.route("/addstudent", methods=['GET', 'POST'])
@login_required
def addstudent():
    form = AddStudentForm()
    form.school_id.choices = [(school.id, school.location) for school in School.query.order_by(School.location).all()]
    if request.method == 'POST':
        if form.validate_on_submit:
            first_name = form.first_name.data
            last_name = form.last_name.data
            DOB = form.DOB.data
            rank = form.rank.data
            if rank == 'triple stripe':
                rank = 0
            else:
                rank = int(rank)
            recerts = int(form.recerts.data)
            school_id = form.school_id.data
            which_test = form.which_test.data
            new_student = Student(first_name=first_name,last_name=last_name,DOB=DOB,rank=rank,recerts=recerts,school_id=school_id)
            db.session.add(new_student)
            db.session.commit()
            if which_test != "not testing":
                test = Test.query.order_by(Test.id.desc()).first()
                if test.testing_date.date() - DOB >= timedelta(days=365*18):
                    level = 'Adult'
                else:
                    level = 'Junior'
                if which_test == "regular test":
                    student_test = StudentTest(student_id=new_student.id,test_id=test.id,regular_test=True,level=level)
                else:
                    student_test = StudentTest(student_id=new_student.id,test_id=test.id,makeup_test=True,level=level)
                db.session.add(student_test)
                db.session.commit()
            flash("New Student has been added")
            return redirect(url_for('addstudent'))
    return render_template('addstudent.html', form=form)


@app.route("/addtest", methods=['GET', 'POST'], endpoint='addtest')
@login_required
@adminonly
def addtest():
    form = AddTestForm()
    if request.method == "POST":
        if form.validate_on_submit():
            testing_date = form.testing_date.data
            testing_number = form.testing_number.data
            db.session.add(Test(testing_date=testing_date,testing_number=testing_number))
            db.session.commit()
            flash("New test has been added.")
            return redirect(url_for('options'))
    test = Test.query.order_by(Test.id.desc()).first()
    form.testing_number.data = test.testing_number + 1
    return render_template('addtest.html', form=form)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


# gets to all pages
@app.route('/options')
@login_required
def options():
    # if current_user.role != 'admin':
    #     flash("You do not have access to this page")
    #     return redirect(url_for('/login'))
    return render_template('options.html')
