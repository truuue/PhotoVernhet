import os
import requests
import json
from dotenv import load_dotenv
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, session, render_template_string
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_user import login_required, UserManager, UserMixin
from flask_login import login_required, current_user, LoginManager, login_user, logout_user
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField
from wtforms.validators import InputRequired, DataRequired, Email, Length, EqualTo, Optional
from werkzeug.security import generate_password_hash, check_password_hash
from synology_api.filestation import FileStation

# Charger les variables d'environnement
load_dotenv()

# Initialisation de Flask
app = Flask(__name__)
# Configuration de la base de données
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI')
app.config['USER_ENABLE_EMAIL'] = False
app.config['USER_EMAIL_SENDER_EMAIL'] = "photovernhet@gmail.com"

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

@app.route('/contact')
def contact():
    return render_template('Contact_page.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        # Récupérer les informations de connexion
        username = form.username.data
        password = form.password.data

        # Vérifier les informations de connexion (exemple simplifié)
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

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Le nom d\'utilisateur existe déjà.', 'error')
            return redirect(url_for('register'))

        # Hacher le mot de passe
        hashed_password = generate_password_hash(password)

        # Créer une nouvelle instance de l'utilisateur avec le rôle user par défaut
        new_user = User(username=username, email=email, password=hashed_password, role='user')

        # Ajouter l'utilisateur à la base de données
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('login'))  # Rediriger vers la page de connexion après l'inscription
    return render_template('Register.html')

@app.route('/albums')
@login_required
def albums():
    # Récupérer la liste des albums auxquels l'utilisateur actuel a accès
    user_albums = UserAlbum.query.filter_by(user_id=current_user.id).all()

    # Optionnellement, si vous voulez récupérer des informations supplémentaires sur les albums,
    # par exemple, à partir d'un stockage externe ou d'une autre table, vous pouvez le faire ici

    return render_template('albumSelection.html', albums=user_albums)

@app.route('/albums/<album_name>')
@login_required
def view_album(album_name):
    if not user_has_access_to_album(current_user.id, album_name):
        flash("Vous n'êtes pas autorisé à voir cet album.", 'error')
        return redirect(url_for('home'))
    
    thumbnails_urls = []
    try:
        synology_folder = os.getenv('SYNOLOGY_FOLDER') + '/' + album_name
        files = []
        
        for file in files:
            file_name = file['name']
            thumb_params = {
                'api': 'SYNO.FileStation.Thumb',
                'version': '1',
                'method': 'get',
                'path': os.path.join(synology_folder, file_name),
                'size': 'small',  # Choisissez la taille de la vignette selon les options de l'API
                '_sid': sid
            }
            thumb_response = requests.get(f"{SYNOLOGY_URL}entry.cgi", params=thumb_params, verify=False)  # `verify=False` si vous avez des problèmes de certificat SSL
            
            if thumb_response.status_code == 200:
                # Supposant que l'API renvoie directement l'image de la vignette en réponse
                # Sauvegarder ou transmettre la vignette comme nécessaire
                # Cette partie dépend de comment vous voulez gérer les vignettes
                thumb_url = "/path/to/saved/thumbnail"  # Mettez à jour selon votre logique de sauvegarde
                thumbnails_urls.append(thumb_url)
    except Exception as e:
        flash("Impossible d'accéder à l'album: " + str(e), 'error')
        return redirect(url_for('home'))
    
    return render_template('albumView.html', thumbnails=thumbnails_urls)

@app.route('/serve_thumb/<album_name>/<file_name>')
def serve_thumb(album_name, file_name):
    if not user_has_access_to_album(current_user.id, album_name):
        return "Accès refusé", 403
    
    try:
        fs = FileStation(SYNOLOGY_URL, ACCOUNT, PASSWORD)
        synology_folder = DIRECTORY_PATH + '/' + album_name
        thumb_response = fs.get_thumb(synology_folder, file_name, size='small')  # Ajustez selon votre implémentation
        
        return Response(thumb_response, mimetype='image/jpeg')  # Assurez-vous que le type MIME est correct
    except Exception as e:
        return "Erreur lors du chargement de la vignette: " + str(e), 500

@app.route('/school')
def school():
    return render_template('School_page.html')

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
        db.session.delete(user_to_delete)
        db.session.commit()

    logout_user()
    flash('Votre compte a été supprimé avec succès.', 'success')
    return redirect('/')

@app.route('/delete_user_admin', methods=['POST'])
def delete_user_admin():
    user_id = request.form.get('user_id')
    user_to_delete = User.query.get(user_id)
    if user_to_delete:
        db.session.delete(user_to_delete)
        db.session.commit()
        flash('Le compte a été supprimé.', 'success')
    else:
        flash('Utilisateur introuvable.', 'error')

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
# Mettre en place une redirection automatique vers l'école du mot de passe désigné
# du style : /password-check?redirect=school
# motdepasse redigige vers saint joseph
# motdepasse2 redirige vers la sup

if __name__ == '__main__':
    app.run(debug=True, port=5001)