from flask import Blueprint , Flask, render_template



views = Blueprint('views', __name__)

@views.route('/')
def home():
    return render_template("home.html")