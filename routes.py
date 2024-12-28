import csv
import os
# import smtplib
# import string

from app import app, db, Certificate, School, Student, StudentTest, Test, User, login_manager  # Archive
# from collections import defaultdict
from datetime import datetime, timezone, timedelta
from flask import request, render_template, flash, redirect, url_for, session
from flask_login import current_user, login_user, logout_user, login_required
from forms import AddSchoolForm, AddStudentForm, AddTestForm, AddUserForm, LoginForm  #, EmailForm2, PasswordForm2, AddstudentForm2, RegistrationForm2
# from secrets import choice



@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))


def admin_only(func):
    def wrapper(*args, **kwargs):
        if current_user.role != 'admin':
            flash("You do not have access to that page")
            return redirect(url_for('options'))
        return func(*args, **kwargs)
    return wrapper


# sign in page
@app.route('/', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if request.method == "POST":
        if form.validate_on_submit():
            user = User.query.filter_by(email=form.email.data).first()
            if user and user.check_password(form.password.data):
                login_user(user, remember=form.remember.data)
                test = Test.query.order_by(Test.id.desc()).first()
                # filename = r"/home/TerryM/dealer.picassolures.com/PassLists/passlist"+str(test.testing_number)+".csv"
                session["pass_filename"] = 'PassLists/passlist' + str(test.testing_number) + ".csv"
                session["certif_filename"] = 'CertificateLists/certificatelist' + str(test.testing_number) + ".csv"
                session["makeup_filename"] = 'MakeupPassLists/makeuppasslist' + str(test.testing_number) + ".csv"
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
    form.school_id.data = current_user.school_id
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
            new_student = Student(first_name=first_name.upper(),last_name=last_name.upper(),DOB=DOB,rank=rank,recerts=recerts,school_id=school_id)
            db.session.add(new_student)
            db.session.commit()
            if which_test != "not testing":
                test = Test.query.order_by(Test.id.desc()).first()
                if test.testing_date.date() - DOB >= timedelta(days=365*18):
                    level = 'Adult'
                else:
                    level = 'Junior'
                if rank == 3 and recerts == 6:
                    testing_up = True
                else:
                    testing_up = False
                if which_test == "regular test":
                    student_test = StudentTest(student_id=new_student.id,test_id=test.id,makeup_test=False,level=level,testing_up=testing_up)
                else:
                    student_test = StudentTest(student_id=new_student.id,test_id=test.id,makeup_test=True,level=level,testing_up=testing_up)
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
            # testing_date = testing_date.date()
            testing_number = form.testing_number.data
            db.session.add(Test(testing_date=testing_date,testing_number=testing_number))
            db.session.commit()
            test = Test.query.order_by(Test.id.desc()).first()
            # filename = r"/home/TerryM/dealer.picassolures.com/PassLists/passlist"+str(test.testing_number)+".csv"
            session["pass_filename"] = 'PassLists/passlist' + str(testing_number) + ".csv"
            session["certif_filename"] = 'CertificateLists/certificatelist' + str(testing_number) + ".csv"
            session["makeup_filename"] = 'MakeupPassLists/makeuppasslist' + str(testing_number) + ".csv"
            flash("New test has been added.")
            return redirect(url_for('options'))
    test = Test.query.order_by(Test.id.desc()).first()
    form.testing_number.data = test.testing_number + 1
    return render_template('add_test.html', form=form)




#  A student that went to regular testing but has not passed yet is put in limbo
@app.route('/add_to_limbo', methods=['POST'], endpoint="add_to_limbo")
@login_required
@admin_only
def add_to_limbo():
    studentid = request.form['studentid']
    studentid = studentid.strip(')').strip('(')
    if studentid:
        studentid = int(studentid)
        student = Student.query.filter_by(id=studentid).first()
        if student:
            test = Test.query.order_by(Test.id.desc()).first()
            student_test = StudentTest.query.filter_by(student_id=studentid).filter_by(test_id=test.id).first()
            student_test.limbo = True
            db.session.commit()

    return redirect(url_for('first_pass'))

@app.route('/add_to_test/<testid>', methods=['POST'])
@login_required
def add_to_test(testid):
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
            if testid == "first":
                makeup_test = False
            else:
                makeup_test = True
            if student.rank == 3 and student.recerts == 6:
                testing_up = True
            else:
                testing_up = False
            student_test = StudentTest(student_id=student.id,test_id=test.id,makeup_test=makeup_test,level=level,testing_up=testing_up)
            db.session.add(student_test)
            db.session.commit()

    return redirect(url_for('choose_testers'))


@app.route("/add_user", methods=['GET', 'POST'], endpoint='add_user')
@login_required
@admin_only
def add_user():
    form = AddUserForm()
    form.school_id.choices = [(school.id, school.location) for school in School.query.order_by(School.location).all()]
    if request.method == 'POST':
        if form.validate_on_submit:
            first_name = form.first_name.data
            last_name = form.last_name.data
            email = form.email.data
            school_id = form.school_id.data
            role = form.role.data
            duplicate = User.query.filter_by(email=email).first()
            if duplicate:
                flash("Email (Username) is already taken")
                form.data.first_name=first_name
                form.data.last_name=last_name
                form.data.school_id=school_id
                form.role=role
                return redirect(url_for('add_user', form=form))
            new_user = User(first_name=first_name,last_name=last_name,email=email,role=role,school_id=school_id)
            db.session.add(new_user)
            new_user.set_password(form.temp_password.data)
            db.session.commit()
            flash("New User has been added")
            return redirect(url_for('options'))
    return render_template('add_user.html', form=form)

@app.route("/choose_high_ranks", methods=['GET','POST'])
@login_required
def choose_high_ranks():
    test = Test.query.order_by(Test.id.desc()).first()
    high_ranks = []
    for studenttest in test.students:
        student = Student.query.filter_by(id=studenttest.student_id).first()
        if student.rank >=4 and not studenttest.testing_up:
            high_ranks.append(student)
    high_ranks.sort(key = lambda x: (x.last_name, x.first_name))
    return render_template('choose_high_ranks.html', high_ranks=high_ranks)


@app.route("/choose_instructor", methods=['GET','POST'], endpoint='choose_instructor')
@login_required
@admin_only
def choose_instructor():
    instructors = User.query.filter(User.id != 1).order_by(User.last_name, User.first_name).all()
    if request.method == "POST":
        userid = request.form['userid']
        userid=userid.strip(')').strip('(')
        return redirect(url_for('edit_instructor', userid=userid))
    
    return render_template('choose_instructor.html', instructor_list=instructors)


@app.route("/choose_school", methods=['GET','POST'], endpoint='choose_school')
@login_required
@admin_only
def choose_school():
    schools = School.query.order_by(School.location).all()
    if request.method == "POST":
        schoolid = request.form['schoolid']
        schoolid=schoolid.strip(')').strip('(')
        return redirect(url_for('edit_school', schoolid=schoolid))
    
    return render_template('choose_school.html', school_list=schools)

@app.route("/choose_student", methods=['GET','POST'])
@login_required
def choose_student():
    if current_user.role == 'admin':
        students = Student.query.order_by(Student.last_name, Student.first_name).all()   #  filter_by(current=True)
    else:
        students = Student.query.filter_by(school_id=current_user.school_id).filter_by(current=True).order_by(Student.last_name, Student.first_name).all()
    if request.method == "POST":
        studentid = request.form['studentid']
        studentid=studentid.strip(')').strip('(')
        return redirect(url_for('edit_student', studentid=studentid))
    
    return render_template('choose_student.html', student_list=students)



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


@app.route("/edit_instructor/<userid>", methods=['GET', 'POST'], endpoint='edit_instructor')
@login_required
@admin_only
def edit_instructor(userid):   
    instructor = User.query.filter_by(id=userid).first()
    form = AddUserForm()
    form.school_id.choices = [(school.id, school.location) for school in School.query.order_by(School.location).all()]
    if request.method == 'POST':
        if form.validate_on_submit:
            first_name = form.first_name.data
            last_name = form.last_name.data
            temp_password = form.temp_password.data
            email = form.email.data
            school_id = form.school_id.data
            role = form.role.data
            if email != instructor.email:
                duplicate = User.query.filter_by(email=email).first()
                if duplicate:
                    flash("Email (Username) is already taken")
                    form.first_name.data = first_name
                    form.last_name.data = last_name
                    form.school_id.data = school_id
                    form.role.data = role
                    return render_template('edit_instructor.html', form=form, userid=userid)
            instructor.first_name = first_name
            instructor.last_name = last_name
            instructor.email = email
            instructor.school_id = school_id
            instructor.role = role
            if temp_password != '':
                instructor.set_password(temp_password)
            
            db.session.commit()
            
            flash("Instructor has been edited.")
            return redirect(url_for('options'))
    
    form.first_name.data = instructor.first_name
    form.last_name.data = instructor.last_name
    form.email.data = instructor.email
    form.role.data = instructor.role
    form.school_id.data = instructor.school_id
    
    return render_template('edit_instructor.html', form=form)

@app.route("/edit_school/<schoolid>", methods=['GET', 'POST'], endpoint='edit_school')
@login_required
@admin_only
def edit_school(schoolid):   
    school = School.query.filter_by(id=schoolid).first()
    form = AddSchoolForm()
    if request.method == 'POST':
        if form.validate_on_submit:
            location = form.location.data
            if location != school.location:
                duplicate = School.query.filter_by(location=location).first()
                if duplicate:
                    flash("School name is already taken")
                    form.location.data = location
                    return render_template('edit_school.html', form=form, schoolid=schoolid)
            school.location = location            
            db.session.commit()
            
            flash("School has been edited.")
            return redirect(url_for('options'))
    
    form.location.data = school.location
    
    return render_template('edit_school.html', form=form)


@app.route("/edit_student/<studentid>", methods=['GET', 'POST'])
@login_required
def edit_student(studentid):   
    student = Student.query.filter_by(id=studentid).first()
    form = AddStudentForm()
    form.school_id.choices = [(school.id, school.location) for school in School.query.order_by(School.location).all()]
    if request.method == 'POST':
        if form.validate_on_submit:
            student.first_name = form.first_name.data
            student.last_name = form.last_name.data
            student.DOB = form.DOB.data
            rank = form.rank.data
            if rank == 'triple stripe':
                student.rank = 0
            else:
                student.rank = int(rank)
            student.recerts = int(form.recerts.data)
            student.school_id = form.school_id.data
            student.current = form.current.data
            
            db.session.commit()
            
            flash("Student has been edited.")
            return redirect(url_for('options'))
    
    form.first_name.data = student.first_name
    form.last_name.data = student.last_name
    form.DOB.data = student.DOB
    if student.rank == 0:
        form.rank.data = "triple stripe"
    else:
        form.rank.data = str(student.rank)
    form.recerts.data = student.recerts
    form.school_id.data = student.school_id
    form.current.data = student.current
    return render_template('edit_student.html', form=form)
    


@app.route("/edit_test", methods=['GET', 'POST'], endpoint='edit_test')
@login_required
@admin_only
def edit_test():
    test = Test.query.order_by(Test.id.desc()).first()
    form = AddTestForm()
    if request.method == "POST":
        if form.validate_on_submit():
            testing_date = form.testing_date.data
            testing_number = form.testing_number.data
            if testing_date != test.testing_date.date() and testing_number != test.testing_number:
                flash("Instead of editing this test ADD A NEW TEST")
                return redirect(url_for('options'))
            if testing_date == test.testing_date.date() and testing_number == test.testing_number:
                flash("Test has NOT been edited.")
                return redirect(url_for('options'))
            if testing_date != test.testing_date.date():
                test.testing_date = testing_date
                db.session.commit()
            if testing_number != test.testing_number:
                previous_test_number = Test.query.filter_by(testing_number=testing_number).first()
                if previous_test_number:
                    flash("This test number has already been used")
                    return redirect(url_for('options'))
                
                if os.path.isfile('PassLists/passlist' + str(test.testing_number) + ".csv"):
                    os.rename('PassLists/passlist' + str(test.testing_number) + ".csv", 'PassLists/passlist' + str(testing_number) + ".csv")
                session["pass_filename"] = 'PassLists/passlist' + str(testing_number) + ".csv"
                if os.path.isfile('CertificateLists/certificatelist' + str(test.testing_number) + ".csv"):
                    os.rename('CertificateLists/certificatelist' + str(test.testing_number) + ".csv",'CertificateLists/certificatelist' + str(testing_number) + ".csv")
                session["certif_filename"] = 'CertificateLists/certificatelist' + str(testing_number) + ".csv"
                if os.path.isfile('MakeupPassLists/makeuppasslist' + str(test.testing_number) + ".csv"):
                    os.rename('MakeupPassLists/makeuppasslist' + str(test.testing_number) + ".csv",'MakeupPassLists/makeuppasslist' + str(testing_number) + ".csv")
                session["makeup_filename"] = 'MakeupPassLists/makeuppasslist' + str(testing_number) + ".csv"
                test.testing_number = testing_number
                db.session.commit()         
            flash("Changes to test have been made.")
            return redirect(url_for('options'))
    form.testing_number.data = test.testing_number
    form.testing_date.data = test.testing_date
    return render_template('edit_test.html', form=form)



@app.route("/first_pass", methods=['GET','POST'], endpoint='first_pass')
@login_required
@admin_only
def first_pass():
    test = Test.query.order_by(Test.id.desc()).first()
    student_ids = [student.student_id for student in test.students if (not student.makeup_test and not student.limbo and not student.passed_regular)]
    students = [Student.query.filter_by(id=studentid).first() for studentid in student_ids]
    students.sort(key = lambda x: (x.last_name, x.first_name))
    return render_template('first_pass.html', student_list=students)

@app.route("/first_update_rank", methods=['GET','POST'], endpoint='first_update_rank')
@login_required
@admin_only
def first_update_rank():
    test = Test.query.order_by(Test.id.desc()).first()
    students_test = [student for student in test.students if (not student.makeup_test and not student.limbo and not student.passed_regular)]
    for student_test in students_test:
        student_test.passed_regular = True
        student = Student.query.filter_by(id=student_test.student_id).first()
        student.rank, student.recerts = update_rank(student_test, student)
        full_name = student.first_name + " " + student.last_name
        write_to_file(session["pass_filename"],[full_name,student.rank, student.recerts, student_test.level, student.first_name, student.last_name])
        if student.recerts == 0:
            db.session.add(Certificate(test_id=test.id, studenttest_id=student_test.id, new_rank=student.rank))
            school = School.query.filter_by(id=student.school_id).first()
            write_to_file(session["certif_filename"],[full_name,student.rank, student_test.level, school.location, student.first_name, student.last_name])
    db.session.commit()
    flash("Ranks have been updated.")
    return redirect(url_for('options'))

@app.route("/indiv_first_update", methods=['GET','POST'], endpoint='indiv_first_update')
@login_required
@admin_only
def indiv_first_update():
    test = Test.query.order_by(Test.id.desc()).first()
    student_ids = [student.student_id for student in test.students if student.limbo]
    students = [Student.query.filter_by(id=studentid).first() for studentid in student_ids]
    students.sort(key= lambda x: (x.last_name, x.first_name))
    return render_template('indiv_first_update.html', student_list=students)

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
    students.sort(key= lambda x: (x.last_name, x.first_name))
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
            student_test = StudentTest.query.filter_by(student_id=studentid).filter_by(test_id=test.id).first()
            student_test.makeup_test = True
            db.session.commit()

    return redirect(url_for('first_pass'))


# gets to all pages
@app.route('/options')
@login_required
def options():
    return render_template('options.html')

@app.route('/pass_indiv', methods=['POST'], endpoint="pass_indiv")
@login_required
@admin_only
def pass_indiv():
    studentids = request.form.getlist('studentid')
    passes = request.form.getlist('status')
    students = [studentids[idx] for idx in range(len(studentids)) if passes[idx]=="pass"]
    test = Test.query.order_by(Test.id.desc()).first()
    for studentid in students:
        student_test = StudentTest.query.filter_by(student_id=studentid).filter_by(test_id=test.id).first()
        student_test.passed_regular = True
        student_test.limbo = False
        student = Student.query.filter_by(id=studentid).first()
        student.rank, student.recerts = update_rank(student_test, student)
        full_name = student.first_name + " " + student.last_name
        write_to_file(session["pass_filename"],[full_name,student.rank, student.recerts, student_test.level, student.first_name, student.last_name])
        if student.recerts == 0:
            db.session.add(Certificate(test_id=test.id, studenttest_id=student_test.id, new_rank=student.rank))
            school = School.query.filter_by(id=student.school_id).first()
            write_to_file(session["certif_filename"],[full_name,student.rank, student_test.level, school.location, student.first_name, student.last_name])
    db.session.commit()
    flash("Passing Individual students have been updated.")
    return redirect(url_for('options'))


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
        full_name = student.first_name + " " + student.last_name
        write_to_file(session["makeup_filename"],[full_name,student.rank, student.recerts, student_test.level, student.first_name, student.last_name])
        if student.recerts == 0:
            db.session.add(Certificate(test_id=test.id, studenttest_id=student_test.id, new_rank=student.rank))
            school = School.query.filter_by(id=student.school_id).first()
            write_to_file(session["certif_filename"],[full_name,student.rank, student_test.level, school.location, student.first_name, student.last_name])
    db.session.commit()
    flash("Passing Makeup students have been updated.")
    return redirect(url_for('options'))


@app.route('/pattern_count')
@login_required
def pattern_count():
    test = Test.query.order_by(Test.id.desc()).first()
    juniors = [Student.query.filter_by(id=student.student_id).first() for student in test.students if student.level=="Junior"]
    adults = [Student.query.filter_by(id=student.student_id).first() for student in test.students if student.level=="Adult"]
    junior_patterns = [0,[],[],[]]
    adult_patterns = [0,[],[],[]]
    ranks = [0,"1ST","2ND","3RD"]
    for rank in range(1,4):
        for recert in range(0,3):
            junior = [student for student in juniors if student.rank == rank and recert <= student.recerts <= (3*recert**2 - recert)//2]
            if junior:
                patterns = len(junior)
            else:
                patterns = 0
            junior_patterns[rank].append(patterns)
            adult_patterns[rank].append(len([student for student in adults if student.rank == rank and recert <= student.recerts <= (3*recert**2 - recert)//2]))
    return render_template('pattern_count.html', adult_patterns=adult_patterns, junior_patterns=junior_patterns, ranks=ranks)
    

@app.route('/test_count/<testid>')
@login_required
def test_count(testid):
    test = Test.query.order_by(Test.id.desc()).first()
    if testid == "first":
        juniors = [Student.query.filter_by(id=student_test.student_id).first() for student_test in test.students if not student_test.makeup_test and not student_test.passed_regular and student_test.level == "Junior" and not student_test.testing_up ]
        juniors_test = [Student.query.filter_by(id=student_test.student_id).first() for student_test in test.students if not student_test.makeup_test and not student_test.passed_regular and student_test.level == "Junior" and student_test.testing_up ]
        adults = [Student.query.filter_by(id=student_test.student_id).first() for student_test in test.students if not student_test.makeup_test and not student_test.passed_regular and student_test.level == "Adult" and not student_test.testing_up ]
        adults_test = [Student.query.filter_by(id=student_test.student_id).first() for student_test in test.students if not student_test.makeup_test and not student_test.passed_regular and student_test.level == "Adult" and student_test.testing_up ]
        filename = 'TestCount/testcount' + str(test.testing_number) + ".csv"    
    elif testid == "makeup":
        juniors = [Student.query.filter_by(id=student_test.student_id).first() for student_test in test.students if student_test.makeup_test and not student_test.passed_regular and student_test.level == "Junior" and not student_test.testing_up ]
        juniors_test = [Student.query.filter_by(id=student_test.student_id).first() for student_test in test.students if student_test.makeup_test and not student_test.passed_regular and student_test.level == "Junior" and student_test.testing_up ]
        adults = [Student.query.filter_by(id=student_test.student_id).first() for student_test in test.students if student_test.makeup_test and not student_test.passed_regular and student_test.level == "Adult" and not student_test.testing_up ]
        adults_test = [Student.query.filter_by(id=student_test.student_id).first() for student_test in test.students if student_test.makeup_test and not student_test.passed_regular and student_test.level == "Adult" and student_test.testing_up ]
        filename = 'TestCount/makeupcount' + str(test.testing_number) + ".csv"
    with open(filename, 'w', newline='') as csvfile:
        spamwriter = csv.writer(csvfile, delimiter=',')
        spamwriter.writerow(["Count of Testing on " + str(test.testing_date.date())])
    test_totals = [0, 0, 0, 0]
    for rank in range(4):
        if 0 <= rank <= 1:
            test = 1
        else:
            test = 2
        adult = count(adults, rank)
        junior = count(juniors, rank)
        write_rank(filename, rank, junior, adult, False)
        test_totals[test] += junior + adult
    rank = 3
    test = 3
    adult = count(adults_test, rank)
    junior = count(juniors_test, rank)
    write_rank(filename, rank, junior, adult, True)
    test_totals[test] += junior + adult
    rank = 4
    adult = count(adults, rank)
    junior = count(juniors, rank)
    write_rank(filename, rank, junior, adult, False)
    test_totals[test] += junior + adult
    adult = count(adults_test, rank)
    write_rank(filename, rank, 0, adult, True)
    test_totals[test] += adult
    for rank in range(5,9):
        adult = count(adults, rank)
        write_rank(filename, rank, 0, adult, False)
        test_totals[test] += adult
        adult = count(adults_test, rank)
        write_rank(filename, rank, 0, adult, True)
        test_totals[test] += adult
    for test in range(1,4):  
        write_to_file(filename, ["Total at Test " + str(test) + ":   " + str(test_totals[test])])
    flash("Count of Testing has been made.")
    return redirect(url_for('options'))
    

def count(students, rank):
    return len([student for student in students if student.rank == rank])

def write_rank(filename, rank, junior, adult, test):
    titles = ['TRIPLE STRIPES', '1ST DANS', '2ND DANS', '3RD DANS', '4TH DANS', '5TH DANS', '6TH DANS','7TH DANS','8TH DANS','9TH DANS']
    if test and junior + adult > 0:
        write_to_file(filename, ['RANK: ' + str(titles[rank]) + " TESTING FOR " + titles[rank + 1][:4]])
    elif junior + adult > 0:
        write_to_file(filename, ['RANK: ' + str(titles[rank]) + '     TOTAL: ' + str(junior + adult)])
    if junior > 0:
        write_to_file(filename, ["Juniors: " + str(junior)])
    if adult > 0:
        write_to_file(filename, ["Adults: " + str(adult)])

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

def write_to_file(filename, row):
    with open(filename, 'a', newline='') as csvfile:
        spamwriter = csv.writer(csvfile, delimiter=',')
        spamwriter.writerow(row)
    return