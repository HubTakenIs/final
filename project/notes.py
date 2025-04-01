from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, session
)
from werkzeug.exceptions import abort

from project.auth import login_required
from project.db import get_db

bp = Blueprint('notes', __name__)

@bp.route('/')
def index():
    db = get_db()
    if 'user_id' in session:

        notes = db.execute(
            'SELECT n.id, title, body, created, author_id'
            ' FROM notes n WHERE author_id = ?'
            ' ORDER BY created DESC',(session['user_id'],)
        ).fetchmany(5)
        return render_template('notes/index.html', notes=notes)
    flash("Go make some new notes")
    return render_template('notes/index.html')

@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        error = None

        if not title:
            error = 'Title is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'INSERT INTO notes (title, body, author_id)'
                ' VALUES (?, ?, ?)',
                (title, body, g.user['id'])
            )
            db.commit()
            return redirect(url_for('notes.index'))

    return render_template('notes/create.html')

def get_note(id, check_author=True):
    note = get_db().execute(
        'SELECT n.id, title, body, created, author_id, username'
        ' FROM notes n JOIN user u ON n.author_id = u.id'
        ' WHERE n.id = ?',
        (id,)
    ).fetchone()

    if note is None:
        abort(404, f"Note id {id} doesn't exist.")

    if check_author and note['author_id'] != g.user['id']:
        abort(403)

    return note

@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    note = get_note(id)

    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        error = None

        if not title:
            error = 'Title is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'UPDATE notes SET title = ?, body = ?'
                ' WHERE id = ?',
                (title, body, id)
            )
            db.commit()
            return redirect(url_for('notes.index'))

    return render_template('notes/update.html', note=note)

@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    get_note(id)
    db = get_db()
    db.execute('DELETE FROM notes WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('notes.index'))

@bp.route('/<int:id>/view', methods=('GET',))
@login_required
def view(id):
    note = get_note(id)
    return render_template('notes/view.html', note=note)
    