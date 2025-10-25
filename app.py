# app.py
import os
from flask import Flask, render_template, request, session, redirect, url_for, flash
from flask_session import Session
from database import init_db, verify_user, create_user, get_user_by_username
from diktat import get_diktate_list, parse_diktat, compare_texts, get_diktate_metadata
from auth import login_required, login_user, logout_user, validate_registration

# --- Konfiguration ---
app = Flask(__name__)

# Wichtig für die Session-Verwaltung.
app.config['SECRET_KEY'] = 'ein_sehr_geheimer_schlüssel_für_diktate'
# Konfiguration für serverseitige Sessions
app.config['SESSION_TYPE'] = 'filesystem'
# Das Verzeichnis, in dem die Session-Dateien gespeichert werden
os.makedirs('flask_session', exist_ok=True)
app.config['SESSION_FILE_DIR'] = 'flask_session'

Session(app)

# --- Datenbank beim Start der App initialisieren ---
init_db()

# --- Context Processor ---
# Macht die Variable 'theme' in allen Templates verfügbar
@app.context_processor
def inject_theme():
    theme = session.get('theme', 'light') # Standard ist 'light'
    return dict(theme=theme)

# --- Helper Functions ---
def render_stars(rating):
    """Renders star rating HTML based on numeric rating."""
    stars_html = '<div class="rating rating-sm">'
    for i in range(1, 6):
        if i <= rating:
            stars_html += '<input type="radio" name="rating-' + str(rating) + '" class="mask mask-star-2 bg-orange-400" checked disabled />'
        else:
            stars_html += '<input type="radio" name="rating-' + str(rating) + '" class="mask mask-star-2 bg-orange-400" disabled />'
    stars_html += '</div>'
    return stars_html

# --- Routen ---
@app.route('/')
def index():
    """Startseite: Zeigt alle verfügbaren Diktate an."""
    # Get filter parameters
    search_query = request.args.get('search', '').strip()
    thema_filter = request.args.get('thema', '')
    uebung_filter = request.args.get('uebung', '')
    schwierigkeit_filter = request.args.get('schwierigkeit', '')
    
    # Get all dictations with metadata
    all_diktate = get_diktate_metadata()
    
    # Apply filters
    filtered_diktate = []
    
    for diktat in all_diktate:
        # Apply search filter
        if search_query and search_query.lower() not in diktat.get('titel', '').lower() and \
           search_query.lower() not in diktat.get('beschreibung', '').lower():
            continue
            
        # Apply theme filter
        if thema_filter and thema_filter != diktat.get('thema', ''):
            continue
            
        # Apply exercise filter
        if uebung_filter and uebung_filter != diktat.get('übung', ''):
            continue
            
        # Apply difficulty filter
        if schwierigkeit_filter and schwierigkeit_filter != diktat.get('schwierigkeit', ''):
            continue
            
        # Add star rating HTML
        try:
            rating = int(diktat.get('schwierigkeit', 1))
        except (ValueError, TypeError):
            rating = 1
        diktat['stars_html'] = render_stars(rating)
        
        filtered_diktate.append(diktat)
    
    # Get unique values for filter dropdowns
    themen = sorted(set(d.get('thema', '') for d in all_diktate if d.get('thema')))
    uebungen = sorted(set(d.get('übung', '') for d in all_diktate if d.get('übung')))
    schwierigkeiten = sorted(set(d.get('schwierigkeit', '') for d in all_diktate if d.get('schwierigkeit')))
    
    return render_template('index.html', 
                          diktate=filtered_diktate,
                          themen=themen,
                          uebungen=uebungen,
                          schwierigkeiten=schwierigkeiten,
                          search_query=search_query,
                          thema_filter=thema_filter,
                          uebung_filter=uebung_filter,
                          schwierigkeit_filter=schwierigkeit_filter)

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login-Seite."""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = verify_user(username, password)
        
        if user:
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        else:
            flash('Ungültiger Benutzername oder Passwort.', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Registrierungsseite."""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Validierung der Eingaben
        errors = validate_registration(username, password, confirm_password)
        
        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('register.html')
        
        # Prüfen, ob der Benutzername bereits existiert
        existing_user = get_user_by_username(username)
        
        if existing_user:
            flash('Dieser Benutzername ist bereits vergeben.', 'error')
            return render_template('register.html')
        
        # Neuen Benutzer erstellen
        if create_user(username, password):
            flash('Registrierung erfolgreich. Sie können sich jetzt anmelden.', 'success')
            return redirect(url_for('login'))
        else:
            flash('Bei der Registrierung ist ein Fehler aufgetreten.', 'error')
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    """Logout-Funktion."""
    logout_user()
    return redirect(url_for('login'))

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if request.method == 'POST':
        selected_theme = request.form.get('theme')
        if selected_theme:
            session['theme'] = selected_theme
        
        back_url = session.pop('settings_back_url', url_for('index'))
        return redirect(back_url)

    back_url = url_for('index')
    
    if request.referrer and request.referrer.endswith(url_for('train')) and session.get('sentences'):
        back_url = url_for('train')
        
    session['settings_back_url'] = back_url
        
    return render_template('settings.html', back_url=back_url)

@app.route('/start', methods=['POST'])
@login_required
def start_diktat():
    """Startet ein ausgewähltes Diktat und initialisiert die Session."""
    diktat_name = request.form.get('diktat')
    if not diktat_name or diktat_name not in get_diktate_list():
        return redirect(url_for('index'))
        
    sentences, metadata = parse_diktat(diktat_name)
    session['diktat_name'] = metadata.get('titel', diktat_name.replace('.txt', ''))
    session['sentences'] = sentences
    session['current_index'] = 0
    session['feedback'] = None
    session['attempts'] = []  # Initialize attempts list
    
    return redirect(url_for('train'))

@app.route('/train')
@login_required
def train():
    """Hauptseite zum Trainieren eines Satzes."""
    if 'sentences' not in session or 'current_index' not in session:
        return redirect(url_for('index'))

    current_index = session['current_index']
    sentences = session['sentences']
    
    if current_index >= len(sentences):
        # Diktat beendet - redirect to results page
        return redirect(url_for('results'))

    current_sentence = sentences[current_index]
    total_sentences = len(sentences)
    sentence_number = current_index + 1
    
    feedback_html = session.get('feedback')
    
    return render_template(
        'train.html',
        sentence=current_sentence,
        sentence_number=sentence_number,
        total_sentences=total_sentences,
        feedback=feedback_html,
        finished=False
    )

@app.route('/check', methods=['POST'])
@login_required
def check_answer():
    """Prüft die Antwort des Benutzers und speichert das Feedback in der Session."""
    user_input = request.form.get('user_input', '')
    original_sentence = session['sentences'][session['current_index']]
    
    feedback_html, is_correct = compare_texts(original_sentence, user_input)
    session['feedback'] = feedback_html
    session['is_correct'] = is_correct
    
    # Store the attempt in the session
    if 'attempts' not in session:
        session['attempts'] = []
    
    session['attempts'].append({
        'original': original_sentence,
        'user_input': user_input,
        'feedback': feedback_html,
        'is_correct': is_correct
    })
    
    return redirect(url_for('train'))

@app.route('/next')
@login_required
def next_sentence():
    """Wechselt zum nächsten Satz."""
    session['current_index'] += 1
    session['feedback'] = None  # Feedback für den nächsten Satz zurücksetzen
    session['is_correct'] = None  # Reset correctness for the next sentence
    return redirect(url_for('train'))

if __name__ == '__main__':
    # Stellt sicher, dass der Diktate-Ordner existiert
    from diktat import DIKTATE_FOLDER
    if not os.path.exists(DIKTATE_FOLDER):
        os.makedirs(DIKTATE_FOLDER)
    
    app.run(debug=True)

@app.route('/results')
@login_required
def results():
    """Zeigt die Ergebnisse des abgeschlossenen Diktats an."""
    if 'attempts' not in session:
        return redirect(url_for('index'))
    
    diktat_name = session.get('diktat_name', 'Unbekannt')
    attempts = session['attempts']
    
    # Calculate statistics
    total_sentences = len(attempts)
    correct_sentences = sum(1 for attempt in attempts if attempt['is_correct'])
    
    # Calculate word-level accuracy
    total_words = 0
    correct_words = 0
    
    for attempt in attempts:
        original_words = attempt['original'].split()
        user_words = attempt['user_input'].split()
        
        total_words += len(original_words)
        
        # Compare words one by one
        for i in range(min(len(original_words), len(user_words))):
            if original_words[i] == user_words[i]:
                correct_words += 1
    
    word_accuracy = (correct_words / total_words) * 100 if total_words > 0 else 0
    
    # Separate correct and incorrect attempts
    correct_attempts = [attempt for attempt in attempts if attempt['is_correct']]
    incorrect_attempts = [attempt for attempt in attempts if not attempt['is_correct']]
    
    # Clear the session data for the next dictation
    session.pop('diktat_name', None)
    session.pop('sentences', None)
    session.pop('current_index', None)
    session.pop('feedback', None)
    session.pop('is_correct', None)
    attempts_copy = attempts.copy()
    incorrect_attempts_copy = incorrect_attempts.copy()
    session.pop('attempts', None)
    
    return render_template('results.html', 
                          diktat_name=diktat_name, 
                          attempts=attempts_copy,
                          incorrect_attempts=incorrect_attempts_copy,
                          total_sentences=total_sentences,
                          correct_sentences=correct_sentences,
                          word_accuracy=word_accuracy,
                          total_words=total_words,
                          correct_words=correct_words)