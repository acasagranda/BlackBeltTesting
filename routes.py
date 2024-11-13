# import csv
# import os
# import smtplib
# import string

from app import app, db, Certificate, School, Student, StudentTest, Test, User, login_manager  # Archive
# from collections import defaultdict
# from datetime import datetime, timezone
from flask import request, render_template, flash, redirect, url_for
from flask_login import current_user, login_user, logout_user, login_required
from forms import LoginForm  #, EmailForm2, PasswordForm2, AddstudentForm2, RegistrationForm2
# from secrets import choice


@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))


# sign in page
@app.route('/', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if request.method == "POST":
        if form.validate_on_submit():
            user = User.query.filter_by(username=form.username.data).first()
            if user and user.check_password(form.password.data):
                login_user(user, remember=form.remember.data)
                next_page = request.args.get('next')
                return redirect(next_page or url_for('options'))
        flash("Username or password is incorrect. Please try again.")
        return redirect(url_for('login'))

    return render_template('login.html', form=form)

# gets to all pages
@app.route('/options')
@login_required
def options():
    if current_user.role != 'admin':
        flash("You do not have access to this page")
        return redirect(url_for('/login'))
    return render_template('options.html')
