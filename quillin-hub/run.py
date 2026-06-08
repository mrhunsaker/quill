import os
import json
import subprocess
from flask import Flask
from app import db, create_app
from app.models.database import Plugin, User, Interaction
from app.web.routes import web_bp
from app.api.plugins import plugins_bp
from app.forge.forms import forge_bp # Even if we move to GH, we can keep a read-only forge portal

app = create_app()

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=True)
