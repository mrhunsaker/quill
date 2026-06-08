from flask import Blueprint, render_template, request, flash, redirect, url_for
from app.models.database import Plugin, User, Interaction
from app import db

forge_bp = Blueprint('forge', __name__, template_folder='templates')

@forge_bp.route('/')
def index():
    """Entrance to the Submission Forge."""
    return render_template('forge_index.html')

@forge_bp.route('/submit', methods=['GET', 'POST'])
def submit():
    if request.method == 'POST':
        # In the GitHub-Native model, this form now acts as a 
        # "Submission Guide" that helps the user prepare a PR.
        return redirect(url_for('web.index'))
    return render_template('submit_form.html')
