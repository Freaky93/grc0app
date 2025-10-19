# app.py
from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer
from flask_mail import Mail, Message
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'replace-this-with-a-secure-random-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///grc.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


from flask_mail import Mail, Message
import os

s = URLSafeTimedSerializer(app.config['SECRET_KEY'])

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = 'bfreaky834@gmail.com'            # ✅ your Gmail
app.config['MAIL_PASSWORD'] = 'qezlripgnlcszgsb'             # ✅ your Gmail App Password (no spaces)
app.config['MAIL_DEFAULT_SENDER'] = ('GRC App Support', 'bfreaky@gmail.com')

mail = Mail(app)


db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"

# ---------- Models ----------
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(250), unique=True, nullable=False)
    password = db.Column(db.String(250), nullable=False)  # hashed password
    password_plain = db.Column(db.String(250))  # store plain version for display (not secure)
    statements = db.relationship('Statement', backref='owner', lazy=True)
    components = db.relationship('Component', backref='owner', lazy=True)

class Statement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    timestamp = db.Column(db.DateTime, server_default=db.func.now())

class Component(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(300), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ---------- Routes ----------
@app.route('/')
def index():
    return redirect(url_for('login'))

# ---------- SIGNUP ----------
@app.route('/signup', methods=['GET','POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username','').strip()
        email = request.form.get('email','').strip()
        password = request.form.get('password','')
        confirm = request.form.get('confirm','')

        if not username or not email or not password:
            return render_template('signup.html', error="Please fill all fields")
        if password != confirm:
            return render_template('signup.html', error="Passwords do not match")

        if User.query.filter((User.username==username)|(User.email==email)).first():
            return render_template('signup.html', error="Username or email already exists")

        hashed = generate_password_hash(password)
        user = User(username=username, email=email, password=hashed, password_plain=password)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        return redirect(url_for('dashboard'))
    return render_template('signup.html')

# ---------- LOGIN ----------
@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username','').strip()
        password = request.form.get('password','')
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        return render_template('index.html', error="Invalid credentials")
    return render_template('index.html')

# ---------- LOGOUT ----------
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# --# -------- DASHBOARD ----------
@app.route('/dashboard')
@login_required
def dashboard():
    statements = Statement.query.filter_by(user_id=current_user.id).order_by(Statement.timestamp.desc()).all()
    default_components = [
        "define", "document", "protection and handling", "data and information",
        "applicable laws, regulations, and policies", "National Data Management Office (NDMO)",
        "Incident Response Team", "Security Operations Center", "Must Be Reported",
        "Data Loss Prevention", "Must Be Approved By The", "Organization", "Workstation",
        "Servers", "Identity and Access Management (IAM)"
    ]
    user_components = Component.query.filter_by(user_id=current_user.id).all()
    
    # ✅ Add this line to include templates created by the user
    user_templates = Template.query.filter_by(user_id=current_user.id).all()

    # ✅ Pass user_templates to the HTML page
    return render_template(
        'dashboard.html',
        user=current_user,
        statements=statements,
        default_components=default_components,
        components=user_components,
        user_templates=user_templates
    )

# ---------- PROFILE ----------
@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html', user=current_user, plain_password=current_user.password_plain or "")

# ---------- UPDATE PASSWORD ----------
@app.route('/update_password', methods=['POST'])
@login_required
def update_password():
    new_password = request.form.get('new_password')
    if not new_password:
        return render_template('profile.html', user=current_user, error="Please enter a new password.")
    current_user.password = generate_password_hash(new_password)
    current_user.password_plain = new_password
    db.session.commit()
    return render_template('profile.html', user=current_user, plain_password=new_password, message="Password updated successfully!")

# ---------- SAVE STATEMENT ----------
@app.route('/save_statement', methods=['POST'])
@login_required
def save_statement():
    data = request.get_json() or {}
    content = data.get('content','').strip()
    if not content:
        return jsonify({'success': False, 'error': 'Empty content'})
    st = Statement(content=content, user_id=current_user.id)
    db.session.add(st)
    db.session.commit()
    return jsonify({'success': True, 'id': st.id, 'content': st.content})

# ---------- DELETE STATEMENT ----------
@app.route('/delete_statement', methods=['POST'])
@login_required
def delete_statement():
    data = request.get_json() or {}
    sid = data.get('id')
    if not sid:
        return jsonify({'success': False, 'error': 'No id'})
    st = Statement.query.filter_by(id=sid, user_id=current_user.id).first()
    if not st:
        return jsonify({'success': False, 'error': 'Not found'})
    db.session.delete(st)
    db.session.commit()
    return jsonify({'success': True})

# ---------- SAVE COMPONENT ----------
@app.route('/save_component', methods=['POST'])
@login_required
def save_component():
    data = request.get_json() or {}
    name = (data.get('name') or '').strip()
    if not name:
        return jsonify({'success': False, 'error': 'Empty name'})
    comp = Component(name=name, user_id=current_user.id)
    db.session.add(comp)
    db.session.commit()
    return jsonify({'success': True, 'id': comp.id, 'name': comp.name})
 # ---------- FORGOT PASSWORD ----------
@app.route('/forgot', methods=['GET','POST'])
def forgot():
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        if not user:
            return render_template('forgot.html', error="No user with that email.")
        token = s.dumps(user.email, salt='password-reset')
        link = url_for('reset_password', token=token, _external=True)
        # Build message
        msg = Message(subject="Password Reset - GRC Statements",
                      recipients=[user.email])
        msg.body = f"Hello {user.username},\n\nClick the link below to reset your password (valid 30 minutes):\n\n{link}\n\nIf you didn't request this, ignore this email."
        try:
            mail.send(msg)
            return render_template('forgot.html', message="Reset link sent — check your email.")
        except Exception as e:
            # fallback to console + useful debug message
            print("Mail send failed:", e)
            print("Reset link (dev):", link)
            return render_template('forgot.html', message="Reset link printed to console (mail send failed).")
    return render_template('forgot.html')


@app.route('/reset/<token>', methods=['GET', 'POST'])
def reset_password(token):
    try:
        email = s.loads(token, salt='password-reset', max_age=1800)
    except Exception:
        return render_template('reset.html', error="Invalid or expired token.")

    if request.method == 'POST':
        password = request.form.get('password')
        confirm = request.form.get('confirm')
        if password != confirm:
            return render_template('reset.html', error="Passwords do not match.")
        user = User.query.filter_by(email=email).first()
        if user:
            user.password = generate_password_hash(password)
            user.password_plain = password
            db.session.commit()
            return redirect(url_for('login'))
    return render_template('reset.html', email=email)

@app.route('/your_saved')
@login_required
def your_saved():
    statements = Statement.query.filter_by(user_id=current_user.id).order_by(Statement.timestamp.desc()).all()
    return render_template('your_saved.html', user=current_user, statements=statements)

# Delete a user component (AJAX)
@app.route('/delete_component', methods=['POST'])
@login_required
def delete_component():
    data = request.get_json() or {}
    cid = data.get('id')

    if not cid:
        return jsonify({'success': False, 'error': 'No ID provided'}), 400

    comp = Component.query.filter_by(id=cid, user_id=current_user.id).first()
    if not comp:
        return jsonify({'success': False, 'error': 'Component not found or not allowed'}), 404

    try:
        db.session.delete(comp)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting component: {e}")  # optional debug log
        return jsonify({'success': False, 'error': 'Database error'}), 500

@app.route('/templates')
@login_required
def templates_page():
    templates = Template.query.filter_by(user_id=current_user.id).all()
    return render_template('templates.html', templates=templates)

class Template(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150))
    content = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))


# --- Replace /update or add this new add_template handler (put where routes are) ---
from flask import jsonify  # ensure imported near top

@app.route('/add_template', methods=['POST'])
@login_required
def add_template():
    # accept either form POST (legacy) or JSON (AJAX from templates.html)
    if request.is_json:
        data = request.get_json()
        name = (data.get('name') or '').strip()
        content = (data.get('content') or '').strip()
    else:
        name = request.form.get('name')
        content = request.form.get('content')

    if not name or not content:
        if request.is_json:
            return jsonify({'success': False, 'error': 'Both name and content are required'}), 400
        flash('Both name and content are required', 'error')
        return redirect(url_for('templates_page'))

    new_template = Template(name=name, content=content, user_id=current_user.id)
    db.session.add(new_template)
    db.session.commit()

    if request.is_json:
        return jsonify({'success': True, 'id': new_template.id, 'name': new_template.name, 'content': new_template.content})
    flash('Template added successfully!', 'success')
    return redirect(url_for('templates_page'))


# --- Delete template endpoint (AJAX) ---
@app.route('/delete_template', methods=['POST'])
@login_required
def delete_template():
    data = request.get_json() or {}
    tid = data.get('id')
    if not tid:
        return jsonify({'success': False, 'error': 'No ID provided'}), 400
    t = Template.query.filter_by(id=tid, user_id=current_user.id).first()
    if not t:
        return jsonify({'success': False, 'error': 'Template not found or not allowed'}), 404
    try:
        db.session.delete(t)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': 'DB error'}), 500


# --- Optional: endpoint to get all current user templates as JSON ---
@app.route('/get_templates', methods=['GET'])
@login_required
def get_templates():
    templates = Template.query.filter_by(user_id=current_user.id).all()
    out = [{'id': t.id, 'name': t.name, 'content': t.content} for t in templates]
    return jsonify({'success': True, 'templates': out})

# near top of file, after app = Flask(__name__)



# ---------- Run ----------
if __name__ == '__main__':
    if not os.path.exists('grc.db'):
        with app.app_context():
            db.create_all()
    app.run(debug=True)
