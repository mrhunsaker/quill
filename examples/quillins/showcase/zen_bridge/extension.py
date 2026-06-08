import subprocess
import os
from quill import api

def activate_zen(context):
    """
    Simulates the activation of a system-wide focus mode.
    In a real implementation, this would use OS-specific APIs or shell calls
    to toggle 'Do Not Disturb' or launch a focus app.
    """
    try:
        # Example: Use a shell command to launch a focus playlist (Mock)
        # subprocess.run(["start", "spotify-focus-playlist-url"])
        
        # In this showcase version, we simulate the environment change by 
        # announcing the transition and perhaps updating a status message.
        api.announce("Zen Sanctuary activated. Notifications silenced, focus music playing.")
        
        # Use the editor to mark the transition
        api.insert_text("\n[--- ZEN MODE ACTIVE ---]\n")
    except Exception as e:
        api.announce(f"Failed to activate Zen Bridge: {str(e)}")

def deactivate_zen(context):
    """
    Restores normal system environment.
    """
    try:
        api.announce("Leaving the Zen Sanctuary. Welcome back to the noise.")
        api.insert_text("\n[--- ZEN MODE EXITED ---]\n")
    except Exception as e:
        api.announce(f"Failed to deactivate Zen Bridge: {str(e)}")

api.register_command("activate_zen", activate_zen)
api.register_command("deactivate_zen", deactivate_zen)
