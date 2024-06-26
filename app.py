import os
import requests
from dotenv import load_dotenv
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, session, render_template_string, Response
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_user import login_required, UserManager, UserMixin
from flask_login import login_required, current_user, LoginManager, login_user, logout_user
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, TextAreaField
from wtforms.validators import InputRequired, DataRequired, Email, Length, EqualTo, Optional
from werkzeug.security import generate_password_hash, check_password_hash

# Charger les variables d'environnement
load_dotenv()

# Initialisation de Flask
app = Flask(__name__)
# Configuration de la base de données
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI')
app.config['USER_ENABLE_EMAIL'] = False
app.config['USER_EMAIL_SENDER_EMAIL'] = "photovernhet@gmail.com"

# Configuration de l'accès Synology
SYNOLOGY_URL = os.getenv('SYNOLOGY_URL')
SYNOLOGY_ACCOUNT = os.getenv('SYNOLOGY_ACCOUNT')
SYNOLOGY_PASSWORD = os.getenv('SYNOLOGY_PASSWORD')
SYNOLOGY_FOLDER = os.getenv('SYNOLOGY_FOLDER')
SYNOLOGY_SCHOOL_FOLDER = os.getenv('SYNOLOGY_SCHOOL_FOLDER')

# Initialisation de la base de données
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Initialisation de Flask-Login
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

# Modèle utilisateur pour Flask-User
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False, server_default='')
    email = db.Column(db.String(120), nullable=False, unique=True)
    role = db.Column(db.String(80))

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

# Initialisation de Flask-User
user_manager = UserManager(app, db, User)

# Formulaire Flask-WTF pour la connexion
class LoginForm(FlaskForm):
    username = StringField('Nom d\'utilisateur :', validators=[InputRequired()])
    password = PasswordField('Mot de passe :', validators=[InputRequired()])

# Formulaire Flask-WTF pour la mise à jour du profil
class ProfilForm(FlaskForm):
    username = StringField('Nom d\'utilisateur', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Mot de passe', validators=[Optional(), Length(min=6)])
    confirm_password = PasswordField('Confirmer le mot de passe', validators=[EqualTo('password')])
    submit = SubmitField('Mettre à jour')

class ContactMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    message = db.Column(db.Text, nullable=False)
    submitted_on = db.Column(db.DateTime, default=db.func.current_timestamp(), nullable=False)

    def __repr__(self):
        return f'<ContactMessage {self.name}>'

class ContactForm(FlaskForm):
    name = StringField('Nom', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    message = TextAreaField('Message', validators=[DataRequired()])
    submit = SubmitField('Envoyer')

class UserAlbum(db.Model):
    __tablename__ = 'user_albums'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    album_name = db.Column(db.String(255), nullable=False)

    user = db.relationship('User', backref=db.backref('albums', lazy=True))

def user_has_access_to_album(user_id, album_name):
    access = UserAlbum.query.filter_by(user_id=user_id, album_name=album_name).first()
    return access is not None

@login_manager.user_loader
def load_user(user_id):
    user = User.query.get(int(user_id))
    if user:
        return user
    return None

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    form = ContactForm()
    if form.validate_on_submit():
        message = ContactMessage(name=form.name.data, email=form.email.data, message=form.message.data)
        db.session.add(message)
        db.session.commit()
        flash('Votre message a été envoyé avec succès. Nous vous contacterons bientôt.', 'success')
        return redirect(url_for('contact'))
    return render_template('Contact_page.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            session['user_role'] = user.role
            if user.role == 'admin':
                return redirect(url_for('admin'))
            else:
                return redirect(url_for('home'))
        else:
            flash('Nom d\'utilisateur ou mot de passe incorrect.', 'error')
    return render_template('Login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Récupérer les données du formulaire
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        # Vérifier si un utilisateur avec le même nom d'utilisateur ou email existe déjà
        existing_user = User.query.filter_by(username=username).first()
        existing_user_by_email = User.query.filter_by(email=email).first()
        # Initialiser une variable pour contrôler la redirection
        redirect_needed = False

        if existing_user:
            flash('Le nom d\'utilisateur existe déjà.', 'error')
            redirect_needed = True

        if existing_user_by_email:
            flash('L\'adresse email existe déjà.', 'error')
            redirect_needed = True

        if redirect_needed:
            return redirect(url_for('register'))

        # Hacher le mot de passe avant de le stocker dans la base de données
        hashed_password = generate_password_hash(password)

        # Créer une nouvelle instance de l'utilisateur avec le rôle user par défaut
        new_user = User(username=username, email=email, password=hashed_password, role='user')

        # Ajouter l'utilisateur à la base de données
        db.session.add(new_user)
        db.session.commit()

        flash('Votre compte a été créé avec succès ! Merci de vous connecter.', 'success')
        return redirect(url_for('login'))  # Rediriger vers la page de connexion après l'inscription
    return render_template('Register.html')

@app.route('/albums')
@login_required
def albums():
    # Récupérer la liste des albums auxquels l'utilisateur actuel a accès
    user_albums = UserAlbum.query.filter_by(user_id=current_user.id).all()
    return render_template('albumSelection.html', albums=user_albums)

def get_synology_session():
    try:
        # Send a GET request to the Synology API for authentication
        response = requests.get(f"{SYNOLOGY_URL}webapi/auth.cgi", params={
            'api': 'SYNO.API.Auth',  # Specify the API to use
            'version': '3',  # Specify the version of the API
            'method': 'login',  # Specify the method to use (login)
            'account': SYNOLOGY_ACCOUNT,  # Provide the account name
            'passwd': SYNOLOGY_PASSWORD,  # Provide the password
            'session': 'FileStation',  # Specify the session to use
            'format': 'sid'  # Specify the format of the response (session ID)
        })
        # Raise an exception if the HTTP status code is 4xx or 5xx
        response.raise_for_status()
        # Parse the JSON response
        data = response.json()
        # If the authentication was successful, return the session ID
        if data['success']:
            return data['data']['sid']
    except Exception as e:
        # Print any errors that occur during the authentication process
        print(f"Erreur lors de l'authentification : {e}")
    # If the authentication was not successful, return None
    return None

# Route pour afficher les albums de l'utilisateur
@app.route('/albums/<album_name>')
@login_required
def view_album(album_name):
    if not user_has_access_to_album(current_user.id, album_name):
        flash("Vous n'êtes pas autorisé à voir cet album.", 'error')
        return redirect(url_for('home'))
    
    thumbnails_urls = []
    sid = get_synology_session()
    if sid is None:
        flash("Impossible d'accéder à l'album : Problème d'authentification", 'error')
        return redirect(url_for('home'))

    synology_folder = SYNOLOGY_FOLDER + '/' + album_name
    try:
        response = requests.get(f"{SYNOLOGY_URL}webapi/entry.cgi", params={
            'api': 'SYNO.FileStation.List',
            'version': '2',
            'method': 'list',
            'folder_path': synology_folder,
            '_sid': sid
        })
        response.raise_for_status()
        data = response.json()
        if data['success']:
            for file in data['data']['files']:
                file_name = file['name']
                # Générez des URLs qui pointent vers la nouvelle route Flask `/serve_thumb`
                thumbnails_urls.append(url_for('serve_thumb', album_name=album_name, file_name=file_name))
        else:
            flash("Impossible de lister les fichiers dans l'album", 'error')
            return redirect(url_for('home'))
    except Exception as e:
        flash(f"Impossible d'accéder à l'album : {e}", 'error')
        return redirect(url_for('home'))
    
    return render_template('albumView.html', thumbnails=thumbnails_urls, album_name=album_name)

@app.route('/serve_thumb/<album_name>/<file_name>')
def serve_thumb(album_name, file_name):
    if not user_has_access_to_album(current_user.id, album_name):
        return "Accès refusé", 403
    
    sid = get_synology_session()
    if sid is None:
        return "Erreur d'authentification", 500

    # Construire le chemin complet du fichier sur le NAS
    synology_folder = SYNOLOGY_FOLDER + '/' + album_name
    file_path = f"{synology_folder}/{file_name}"

    try:
        thumb_url = f"{SYNOLOGY_URL}webapi/entry.cgi"
        params = {
            'api': 'SYNO.FileStation.Thumb',
            'version': '1',
            'method': 'get',
            'path': file_path,
            'size': 'small',
            '_sid': sid
        }
        thumb_response = requests.get(thumb_url, params=params, stream=True)
        thumb_response.raise_for_status()
        return Response(thumb_response.content, mimetype='image/jpeg')
    except Exception as e:
        return f"Erreur lors du chargement de la vignette : {e}", 500

# Route pour afficher les écoles
@app.route('/school_albums/<school_name>/<album_name>')
@login_required
def school_album(school_name, album_name):
    username = current_user.username
    # Vérifier que le nom de l'album correspond au nom d'utilisateur pour autoriser l'accès
    if album_name != username:
        flash("Vous n'êtes pas autorisé à voir cet album.", 'error')
        return redirect(url_for('home'))

    thumbnails_urls = []
    sid = get_synology_session()
    if sid is None:
        flash("Impossible d'accéder à l'album : Problème d'authentification", 'error')
        return redirect(url_for('home'))

    folder_path = f'{SYNOLOGY_SCHOOL_FOLDER}/{school_name}/{album_name}'
    try:
        response = requests.get(f"{SYNOLOGY_URL}webapi/entry.cgi", params={
            'api': 'SYNO.FileStation.List',
            'version': '2',
            'method': 'list',
            'folder_path': folder_path,
            '_sid': sid
        })
        response.raise_for_status()
        data = response.json()
        if data['success']:
            for file in data['data']['files']:
                file_name = file['name']
                thumbnails_urls.append(url_for('school_thumb', album_name=album_name, file_name=file_name, school_name=school_name))
        else:
            flash("Impossible de lister les fichiers dans l'album", 'error')
            return redirect(url_for('home'))
    except Exception as e:
        flash(f"Impossible d'accéder à l'album : {e}", 'error')
        return redirect(url_for('home'))
    
    return render_template('schoolView.html', thumbnails=thumbnails_urls, album_name=album_name)

@app.route('/school_thumb/<school_name>/<album_name>/<file_name>')
@login_required
def school_thumb(school_name, album_name, file_name):
    # Vérifier que le nom de l'album correspond au nom de l'utilisateur connecté
    if album_name != current_user.username:
        return "Accès refusé", 403

    sid = get_synology_session()
    if sid is None:
        return "Erreur d'authentification", 500

    # Construire le chemin complet du fichier sur le NAS, en incluant le nom de l'école et de l'album
    file_path = f"{SYNOLOGY_SCHOOL_FOLDER}/{school_name}/{album_name}/{file_name}"

    try:
        thumb_url = f"{SYNOLOGY_URL}webapi/entry.cgi"
        params = {
            'api': 'SYNO.FileStation.Thumb',
            'version': '1',
            'method': 'get',
            'path': file_path,
            'size': 'small',
            '_sid': sid
        }
        thumb_response = requests.get(thumb_url, params=params, stream=True)
        thumb_response.raise_for_status()
        return Response(thumb_response.content, mimetype='image/jpeg')
    except Exception as e:
        return f"Erreur lors du chargement de la vignette : {e}", 500

@app.route('/school')
def school():
    sid = get_synology_session()
    if sid is None:
        flash("Erreur d'authentification avec le serveur Synology.", 'error')
        return redirect(url_for('home'))

    try:
        response = requests.get(f"{SYNOLOGY_URL}webapi/entry.cgi", params={
            'api': 'SYNO.FileStation.List',
            'version': '2',
            'method': 'list',
            'folder_path': SYNOLOGY_SCHOOL_FOLDER,
            '_sid': sid
        })
        response.raise_for_status()
        data = response.json()

        if data['success']:
            # Crée une liste des noms des dossiers (écoles)
            schools = [folder['name'] for folder in data['data']['files']]
        else:
            flash("Impossible de lister les dossiers des écoles.", 'error')
            return redirect(url_for('home'))
    except Exception as e:
        flash(f"Erreur lors de l'accès aux dossiers des écoles : {e}", 'error')
        return redirect(url_for('home'))

    return render_template('School_page.html', schools=schools)

@app.route('/choose_school', methods=['POST'])
@login_required
def choose_school():
    school_name = request.form.get('school_name')
    username = current_user.username
    sid = get_synology_session()

    # Construire le chemin vers le dossier potentiel de l'utilisateur dans l'école sélectionnée
    user_folder_path = f'{SYNOLOGY_SCHOOL_FOLDER}/{school_name}/{username}'

    try:
        # Vérifier si le dossier de l'utilisateur existe dans le dossier de l'école sélectionnée
        response = requests.get(f"{SYNOLOGY_URL}webapi/entry.cgi", params={
            'api': 'SYNO.FileStation.List',
            'version': '2',
            'method': 'list',
            'folder_path': user_folder_path,
            '_sid': sid
        })
        response.raise_for_status()
        data = response.json()

        if data['success'] and data['data']['files']:
            # Si le dossier existe, rediriger vers la vue de cet album
            return redirect(url_for('school_album', album_name=username, school_name=school_name))
        else:
            flash(f"Aucun album trouvé pour {username} dans l'établissement {school_name}.", 'error')
    except Exception as e:
        flash(f"Erreur lors de l'accès à l'album de l'utilisateur : {e}", 'error')

    return redirect(url_for('school'))

@app.route('/profil', methods=['GET', 'POST'])
@login_required
def profil():
    form = ProfilForm(obj=current_user)  # Initialisez le formulaire avec les données actuelles
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.email = form.email.data
        if form.password.data:
            current_user.set_password(form.password.data)

        db.session.commit()
        login_user(current_user)
        flash('Votre profil a été mis à jour.', 'success')
        return redirect(url_for('profil'))
    return render_template('profil.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    session.clear()
    flash('Vous avez été déconnecté avec succès.', 'success')
    return redirect(url_for('home'))

@app.route('/delete_user', methods=['POST'])
@login_required
def delete_user():
    user_id = current_user.id
    user_to_delete = db.session.get(User, user_id)
    if user_to_delete:
        UserAlbum.query.filter_by(user_id=user_id).delete()
        db.session.delete(user_to_delete)
        db.session.commit()

    logout_user()
    flash('Votre compte a été supprimé avec succès.', 'success')
    return redirect('/')

@app.route('/delete_user_admin', methods=['POST'])
def delete_user_admin():
    user_id = request.form.get('user_id')
    if user_id is not None:
        user_to_delete = db.session.get(User, user_id)
        if user_to_delete:
            UserAlbum.query.filter_by(user_id=user_id).delete()
            db.session.delete(user_to_delete)
            db.session.commit()
            flash('Le compte a été supprimé.', 'success')
        else:
            flash('Utilisateur introuvable.', 'error')
    else:
        flash("Aucun ID d'utilisateur fourni.", 'error')

    return redirect('/admin')

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_role' not in session or session['user_role'] != 'admin':
            flash("Vous devez être administrateur pour accéder à cette page.", "warning")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/admin', methods=['GET', 'POST'])
@admin_required
def admin():
    if request.method == 'POST':
        user_id = request.form['user_id']
        new_role = request.form['role']

        # Récupérer l'utilisateur à partir de l'ID
        user = User.query.get(user_id)
        if user:
            user.role = new_role # Mettre à jour le rôle de l'utilisateur
            db.session.commit() # Mettre à jour la base de données
            flash('Rôle mis à jour avec succès.', 'success')

    users = User.query.all() # Récupérer tous les utilisateurs de la base de données
    return render_template('userList.html', users=users)

@app.route('/add_album_access', methods=['POST'])
@login_required
@admin_required
def add_album_access():
    user_id = request.form.get('user_id')
    album_name = request.form.get('album_name').strip()
    
    if UserAlbum.query.filter_by(user_id=user_id, album_name=album_name).first():
        flash('L\'accès à cet album existe déjà pour cet utilisateur.', 'warning')
    else:
        new_access = UserAlbum(user_id=user_id, album_name=album_name)
        db.session.add(new_access)
        db.session.commit()
        flash('Accès à l\'album accordé avec succès.', 'success')
    return redirect(url_for('admin'))

@app.route('/remove_album_access', methods=['POST'])
@login_required
@admin_required
def remove_album_access():
    user_id = request.form.get('user_id')
    album_name = request.form.get('album_name').strip()
    
    access = UserAlbum.query.filter_by(user_id=user_id, album_name=album_name).first()
    if access:
        db.session.delete(access)
        db.session.commit()
        flash('Accès à l\'album retiré avec succès.', 'success')
    else:
        flash('Accès spécifié introuvable.', 'error')
    return redirect(url_for('admin'))

@app.route('/password-check', methods=['GET', 'POST'])
def password_check():
    if request.method == 'POST':
        password = request.form.get('password')
        correct_password = os.getenv('ACCESS_PASSWORD')
        if password == correct_password:
            return redirect(url_for('school'))
        else:
            return render_template_string('''
                <p>Mot de passe incorrect.</p>
                <a href="/">Retour à l'accueil</a>
            ''')
    return render_template_string('''
        <form method="post">
            Veuillez entrer le mot de passe pour accéder à cette page :
            <input type="password" name="password">
            <input type="submit" value="Vérifier">
        </form>
    ''')

if __name__ == '__main__':
    app.run(debug=True, port=5001)