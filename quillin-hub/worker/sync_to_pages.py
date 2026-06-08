from github import Github
import json
import os
from app.models.database import Plugin, User
from app import db

def sync_from_github(token, repo_name="Community-Access/quill"):
    """
    Scans the GitHub repository for plugins and syncs them to the local DB.
    This is the heart of the GitHub-Native model.
    """
    g = Github(token)
    repo = g.get_repo(repo_name)
    
    # Path to where plugins live in the repo
    plugins_root = "examples/quillins"
    contents = repo.get_contents(plugins_root)
    
    for content_file in contents:
        if content_file.type == "dir":
            # We found a plugin directory
            manifest_path = f"{content_file.path}/manifest.json"
            try:
                manifest_content = repo.get_contents(manifest_path)
                manifest = json.loads(manifest_content.decoded_content)
                
                # Sync to DB
                plugin = Plugin.query.filter_by(manifest_id=manifest['id']).first()
                if not plugin:
                    plugin = Plugin(manifest_id=manifest['id'])
                
                plugin.name = manifest['name']
                plugin.version = manifest['version']
                plugin.description = manifest.get('description', '')
                plugin.status = 'Verified' # Assuming if it's in main, it's verified
                
                # Construct the raw GitHub download URL
                plugin.download_url = f"https://github.com/{repo_name}/archive/refs/heads/main.zip"
                
                db.session.add(plugin)
                db.session.commit()
            except Exception as e:
                print(f"Error syncing plugin {content_file.path}: {e}")

if __name__ == "__main__":
    # This would typically be run as a cron job or worker
    # For local testing, we can manually trigger it
    from app import create_app
    app = create_app()
    with app.app_context():
        sync_from_github(os.environ.get('GITHUB_TOKEN'))
