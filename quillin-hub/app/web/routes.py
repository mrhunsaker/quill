from flask import Blueprint, render_template, request, jsonify
from app.models.database import Plugin, User, Interaction
from .. import db

web_bp = Blueprint('web', __name__, template_folder='templates')

@web_bp.route('/')
def index():
    """
    Accessible Storefront Home.
    Features: Search bar, Featured plugins, and Trending categories.
    """
    search_query = request.args.get('q', '').strip()
    plugins = Plugin.query.filter_by(status='Verified').all()
    
    if search_query:
        plugins = [p for p in plugins if search_query.lower() in p.name.lower() or search_query.lower() in p.description.lower()]
    
    # Sort by gold standard and then by reputation (simulated via a query for now)
    featured = [p for p in plugins if p.is_gold_standard]
    others = [p for p in plugins if not p.is_gold_standard]
    
    return render_template('index.html', plugins=featured + others, query=search_query)

@web_bp.route('/plugin/<int:plugin_id>')
def plugin_detail(plugin_id):
    """
    Deep-dive plugin page with a a a a "Snippet Simulator" and reviews.
    """
    plugin = Plugin.query.get_or_404(plugin_id)
    reviews = Interaction.query.filter_by(plugin_id=plugin_id, type='Comment').all()
    return render_template('plugin.html', plugin=plugin, reviews=reviews)

@web_bp.route('/search')
def search():
    """Dedicated search results page for accessibility navigation."""
    q = request.args.get('q', '')
    plugins = Plugin.query.filter(Plugin.name.contains(q) | Plugin.description.contains(q)).filter_by(status='Verified').all()
    return render_template('search.html', plugins=plugins, query=q)
