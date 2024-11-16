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


def admin_only(func):
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

@app.route("/add_school", methods=['GET', 'POST'], endpoint='add_school')
@login_required
@admin_only
def add_school():
    form = AddSchoolForm()
    if request.method == 'POST':
        if form.validate_on_submit:
            location = form.location.data
            db.session.add(School(location=location))
            db.session.commit()
            flash("New School has been added")
            return redirect(url_for('add_school'))
    return render_template('add_school.html', form=form)


@app.route("/add_student", methods=['GET', 'POST'])
@login_required
def add_student():
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
            return redirect(url_for('add_student'))
    return render_template('add_student.html', form=form)


@app.route("/add_test", methods=['GET', 'POST'], endpoint='add_test')
@login_required
@admin_only
def add_test():
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
    return render_template('add_test.html', form=form)

@app.route('/add_to_makeup', methods=['POST'])
@login_required
def add_to_makeup():
    studentid = request.form['studentid']
    studentid = studentid.strip(')').strip('(')
    if studentid:
        studentid = int(studentid)
        student = Student.query.filter_by(id=studentid).first()
        if student:
            test = Test.query.order_by(Test.id.desc()).first()
            if test.testing_date - student.DOB >= timedelta(days=365*18):
                level = 'Adult'
            else:
                level = 'Junior'
            student_test = StudentTest(student_id=student.id,test_id=test.id,makeup_test=True,level=level)
            db.session.add(student_test)
            db.session.commit()

    return redirect(url_for('choose_testers'))

@app.route('/add_to_regular_limbo', methods=['POST'], endpoint="add_to_regular_limbo")
@login_required
@admin_only
def add_to_regular_limbo():
    studentid = request.form['studentid']
    studentid = studentid.strip(')').strip('(')
    if studentid:
        studentid = int(studentid)
        student = Student.query.filter_by(id=studentid).first()
        if student:
            test = Test.query.order_by(Test.id.desc()).first()
            student_test = StudentTest.query.filter_by(id=studentid).filter_by(test_id=test.id).first()
            student_test.regular_limbo = True
            db.session.commit()

    return redirect(url_for('first_pass'))

@app.route('/add_to_test', methods=['POST'])
@login_required
def add_to_test():
    studentid = request.form['studentid']
    studentid = studentid.strip(')').strip('(')
    if studentid:
        studentid = int(studentid)
        student = Student.query.filter_by(id=studentid).first()
        if student:
            test = Test.query.order_by(Test.id.desc()).first()
            if test.testing_date - student.DOB >= timedelta(days=365*18):
                level = 'Adult'
            else:
                level = 'Junior'
            student_test = StudentTest(student_id=student.id,test_id=test.id,regular_test=True,level=level)
            db.session.add(student_test)
            db.session.commit()

    return redirect(url_for('choose_testers'))


@app.route("/choose_high_ranks", methods=['GET','POST'])
@login_required
def choose_high_ranks():
    test = Test.query.order_by(Test.id.desc()).first()
    high_ranks = []
    for studenttest in test.students:
        student = Student.query.filter_by(id=studenttest.student_id).first()
        if student.rank >=4 and not studenttest.testing_up:
            high_ranks.append(student)
    
    return render_template('choose_high_ranks.html', high_ranks=high_ranks)

@app.route("/choose_testers", methods=['GET','POST'])
@login_required
def choose_testers():
    test = Test.query.order_by(Test.id.desc()).first()
    testing_set = {student.student_id for student in test.students}
    current_students = Student.query.filter_by(current=True).order_by(Student.last_name, Student.first_name).all()
    students = [student for student in current_students if student.id not in testing_set]
    return render_template('choose_testers.html', student_list=students)

@app.route("/confirm_first_update", methods=['GET','POST'], endpoint='confirm_first_update')
@login_required
@admin_only
def confirm_first_update():
    return render_template('confirm_first_update.html')


@app.route("/first_pass", methods=['GET','POST'], endpoint='first_pass')
@login_required
@admin_only
def first_pass():
    test = Test.query.order_by(Test.id.desc()).first()
    student_ids = [student.student_id for student in test.students if (student.regular_test and not student.regular_limbo)]
    students = [Student.query.filter_by(id=studentid).first() for studentid in student_ids]
    return render_template('first_pass.html', student_list=students)

@app.route("/first_update_rank", methods=['GET','POST'], endpoint='first_update_rank')
@login_required
@admin_only
def first_update_rank():
    test = Test.query.order_by(Test.id.desc()).first()
    students_test = [student for student in test.students if (student.regular_test and not student.regular_limbo and not student.passed_regular)]
    for student_test in students_test:
        student_test.passed_regular = True
        student = Student.query.filter_by(id=student_test.student_id).first()
        student.rank, student.recerts = update_rank(student_test, student)
        if student.recerts == 0:
            db.session.add(Certificate(test_id=test.id, studenttest_id=student_test.id, new_rank=student.rank))
    db.session.commit()
    flash("Ranks have been updated.")
    return redirect(url_for('options'))



@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route("/makeup_pass", methods=['GET','POST'], endpoint='makeup_pass')
@login_required
@admin_only
def makeup_pass():
    test = Test.query.order_by(Test.id.desc()).first()
    student_ids = [student.student_id for student in test.students if (student.makeup_test and not student.passed_makeup)]
    students = [Student.query.filter_by(id=studentid).first() for studentid in student_ids]
    students.sort(key= lambda x: [x.last_name, x.first_name])
    return render_template('makeup_pass.html', student_list=students)

@app.route('/move_to_makeup', methods=['POST'], endpoint="move_to_makeup")
@login_required
@admin_only
def move_to_makeup():
    studentid = request.form['studentid']
    studentid = studentid.strip(')').strip('(')
    if studentid:
        studentid = int(studentid)
        student = Student.query.filter_by(id=studentid).first()
        if student:
            test = Test.query.order_by(Test.id.desc()).first()
            student_test = StudentTest.query.filter_by(id=studentid).filter_by(test_id=test.id).first()
            student_test.regular_test = False
            student_test.makeup_test = True
            db.session.commit()

    return redirect(url_for('first_pass'))


# gets to all pages
@app.route('/options')
@login_required
def options():
    return render_template('options.html')


@app.route('/pass_makeups', methods=['POST'], endpoint="pass_makeups")
@login_required
@admin_only
def pass_makeups():
    studentids = request.form.getlist('studentid')
    passes = request.form.getlist('status')
    students = [studentids[idx] for idx in range(len(studentids)) if passes[idx]=="pass"]
    test = Test.query.order_by(Test.id.desc()).first()
    for studentid in students:
        student_test = StudentTest.query.filter_by(student_id=studentid).filter_by(test_id=test.id).first()
        student_test.passed_makeup = True
        student = Student.query.filter_by(id=studentid).first()
        student.rank, student.recerts = update_rank(student_test, student)
        if student.recerts == 0:
            db.session.add(Certificate(test_id=test.id, studenttest_id=student_test.id, new_rank=student.rank))
    db.session.commit()
    flash("Passing Makeup students have been updated.")
    return redirect(url_for('options'))


@app.route('/test_up', methods=['POST'])
@login_required
def test_up():
    studentid = request.form['studentid']
    studentid = studentid.strip(')').strip('(')
    if studentid:
        studentid = int(studentid)
        student = Student.query.filter_by(id=studentid).first()
        if student:
            test = Test.query.order_by(Test.id.desc()).first()
            student_testing = StudentTest.query.filter_by(student_id=studentid).filter_by(test_id=test.id).first()
            student_testing.testing_up = True           
            db.session.commit()
    return redirect(url_for('choose_high_ranks'))

def update_rank(student_test, student):
    if student.rank >= 4:
        if student_test.testing_up:
            return student.rank + 1, 0
        return student.rank, student.recerts + 1
    elif student.recerts == 2 * student.rank:
        return student.rank + 1, 0
    return student.rank, student.recerts + 1