# diktat/__init__.py
import os
import difflib
import re

DIKTATE_FOLDER = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'diktate')

def get_diktate_list():
    """Reads all .txt files from the diktate folder."""
    try:
        files = [f for f in os.listdir(DIKTATE_FOLDER) if f.endswith('.txt')]
        return sorted(files)
    except FileNotFoundError:
        return []

def parse_diktat(filename):
    """Reads a diktat file and returns a list of sentences."""
    filepath = os.path.join(DIKTATE_FOLDER, filename)
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Extract metadata from headers
    metadata = {}
    sentences = []
    
    for line in lines:
        line = line.strip()
        if line.startswith('# '):
            # Parse header line
            header_match = re.match(r'#\s*(\w+):\s*(.+)', line)
            if header_match:
                key = header_match.group(1).lower()
                value = header_match.group(2)
                metadata[key] = value
        elif line:
            # Add non-empty lines as sentences
            sentences.append(line)
    
    return sentences, metadata

def get_diktate_metadata():
    """Returns metadata for all dictations."""
    diktate_metadata = []
    
    for filename in get_diktate_list():
        _, metadata = parse_diktat(filename)
        metadata['filename'] = filename
        diktate_metadata.append(metadata)
    
    return diktate_metadata

def compare_texts(original, user_input):
    """
    Compares two texts and returns HTML with highlighting for errors.
    Uses DaisyUI classes for color highlighting.
    Also returns whether the text is correct.
    """
    original_words = original.split()
    user_words = user_input.split()

    diff = list(difflib.ndiff(original_words, user_words))
    
    highlighted_html = ""
    is_correct = True  # Assume it's correct initially
    
    for word_code in diff:
        code = word_code[0]
        word = word_code[2:]
        if code == ' ':
            highlighted_html += f'<span class="badge badge-success">{word}</span> '
        elif code == '-':
            highlighted_html += f'<span class="badge badge-warning text-decoration-line-through">{word}</span> '
            is_correct = False  # Found a missing word, so it's incorrect
        elif code == '+':
            highlighted_html += f'<span class="badge badge-error">{word}</span> '
            is_correct = False  # Found an extra word, so it's incorrect
            
    return highlighted_html.strip(), is_correct