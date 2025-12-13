from flask import Flask, Blueprint, render_template, request, flash

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    return render_template("login.html")

@auth.route('/logout')
def logout():
    return render_template("logout.html")

@auth.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
    if request.method == 'POST':
        email = request.form.get('email')
        first_name = request.form.get('firstName')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')
        
        if len(email) < 4:
             flash('Email must be longer than 3 characters.', category='error')
        elif len(first_name) < 2:
            flash('First Name must be longer than 1 character.', category='error')  # Add your handling code here
        elif password1 != password2:
             flash('Passwords don\'t match.', category='error')
        else:
            flash('Account created!', category='success')
            
    return render_template("signup.html")
