from flask import Blueprint, jsonify, request
from app.models.database import Plugin
from app import db

plugins_bp = Blueprint('plugins_api', __name__)

@plugins_bp.route('/plugins', methods=['GET'])
def get_plugins():
    """
    Registry API endpoint.
    Returns a JSON list of all verified plugins for the QUILL client.
    """
    plugins = Plugin.query.filter_by(status='Verified').all()
    return jsonify([
        {
            "id": p.manifest_id,
            "name": p.name,
            "version": p.version,
            "description": p.description,
            "download_url": p.download_url,
            "gold_standard": p.is_gold_standard
        } for p in plugins
    ])

@plugins_bp.route('/plugins/<manifest_id>/latest', methods=['GET'])
def get_latest_plugin(manifest_id):
    plugin = Plugin.query.filter_by(manifest_id=manifest_id, status='Verified').first()
    if not plugin:
        return jsonify({"error": "Plugin not found or not verified"}), 404
    
    return jsonify({
        "id": plugin.manifest_id,
        "version": plugin.version,
        "download_url": plugin.download_url
    })
