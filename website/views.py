from flask import Blueprint, Flask, render_template, request, flash, jsonify
from .models import Note
from . import db
from flask_login import login_required, current_user
import json
from .ai_helpers import analyze_error_message, call_ai_feedback_api



views = Blueprint('views', __name__)

@views.route('/', methods=['GET', 'POST'])
@login_required
def home():
    if request.method == 'POST':
        note = request.form.get('note')

        if len(note) < 1:
            flash('Note is too short!', category='error')
        else:
            new_note = Note(data=note, user_id=current_user.id)
            db.session.add(new_note)
            db.session.commit()
            flash('Note added!', category='success')
    return render_template("home.html", user=current_user)


@views.route('/ai-helper', methods=['GET', 'POST'])
@login_required
def ai_helper():
    analysis = None
    ai_feedback = None
    message = ""

    if request.method == 'POST':
        message = (request.form.get('message') or "").strip()

        if not message:
            flash('Please enter an error message to analyze.', category='error')
        else:
            analysis = analyze_error_message(message)
            ai_feedback = call_ai_feedback_api(message, analysis)

    return render_template(
        "ai_helper.html",
        user=current_user,
        analysis=analysis,
        ai_feedback=ai_feedback,
        message=message,
    )

@views.route('/delete-note', methods=['POST'])
@login_required
def delete_note():
    note = json.loads(request.data)
    noteId = note['noteId']
    note = Note.query.get(noteId)
    if note:
        if note.user_id == current_user.id:
            db.session.delete(note)
            db.session.commit()
    
    return jsonify({})

@views.route('/ai-message-checker', methods=['POST', 'GET'])
@login_required
def ai_message_checker():
    if request.method == 'POST':
        #get the message from the form and send it to the AI tool via the API. 
        message = request.form.get('message')