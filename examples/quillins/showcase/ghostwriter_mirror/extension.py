from quill import api

# Mock transformation maps for demonstration.
# In a production version, these might use a more complex NLP engine or a set of a hundred mapping rules.
FORMAL_MAP = {
    "hello": "Greetings",
    "thanks": "We expression our gratitude",
    "bad": "suboptimal",
    "fix": "rectify",
    "idea": "proposition",
    "help": "assistance"
}

POETIC_MAP = {
    "hello": "Hail, traveler",
    "thanks": "My heart overflows with thanks",
    "bad": "woeful",
    "fix": "mend",
    "idea": "whisper of inspiration",
    "help": "succor"
}

def apply_mirror(text, mapping):
    words = text.split()
    transformed = [mapping.get(word.lower().strip(",.!?"), word) for word in words]
    return " ".join(transformed)

def mirror_formal(context):
    text = api.get_selection()
    if not text:
        api.announce("Please select some text to mirror.")
        return
    
    mirrored = apply_mirror(text, FORMAL_MAP)
    api.replace_selection(mirrored)
    api.announce("Text mirrored as Legal Formalist.")

def mirror_poetic(context):
    text = api.get_selection()
    if not text:
        api.announce("Please select some text to mirror.")
        return
    
    mirrored = apply_mirror(text, POETIC_MAP)
    api.replace_selection(mirrored)
    api.announce("Text mirrored as Victorian Poet.")

api.register_command("mirror_formal", mirror_formal)
api.register_command("mirror_poetic", mirror_poetic)
