from flask import render_template, url_for, flash, redirect, request
from shop import app, db, bcrypt
from shop.forms import RegistrationForm, LoginForm, UpdateAccountForm
from shop.models import User
from flask_login import login_user, current_user, logout_user, login_required
import sqlite3

DATABASE = "database.db"

products = [
    {"id": 1, "name": "Keyboard", "qty": 1, "desc": "This description for the product details.", "price": 50,
     "image": "/static/pictures/keyboard.png"},
    {"id": 2, "name": "Mouse", "qty": 1, "desc": "This description for the product details.", "price": 10,
     "image": "/static/pictures/mouse.png"},
    {"id": 3, "name": "Headphone", "qty": 1, "desc": "This description for the product details.", "price": 80,
     "image": "/static/pictures/headphone.png"},
    {"id": 4, "name": "Gamepad", "qty": 1, "desc": "This description for the product details.", "price": 60,
     "image": "/static/pictures/gamepad.png"},
]

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS cart (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER
        )
    ''')
    conn.commit()
    conn.close()

init_db()

@app.route("/")
@app.route("/home")
def home():
    return render_template('home.html', title='Home', products=products)

@app.route("/product/<int:pid>")
def product_detail(pid):
    product = next((p for p in products if p["id"] == pid), None)
    return render_template("product.html", product=product, title="Product")

@app.route("/add_to_cart/<int:pid>")
def add_to_cart(pid):
    conn = get_db_connection()
    conn.execute('INSERT INTO cart (product_id) VALUES (?)', (pid,))
    conn.commit()
    conn.close()
    return redirect(url_for("cart_view"))

@app.route("/cart")
def cart_view():
    conn = get_db_connection()
    cart_items_raw = conn.execute('SELECT * FROM cart').fetchall()
    conn.close()


    cart_items = []
    for item in cart_items_raw:
        prod = next((p for p in products if p["id"] == item["product_id"]), None)
        if prod:
            cart_items.append({"cart_id": item["id"], **prod})

    total = sum(item["price"] for item in cart_items)
    return render_template("cart.html", cart_items=cart_items, total=total, title="Cart")

@app.route("/remove_from_cart/<int:cart_id>")
def remove_from_cart(cart_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM cart WHERE id = ?', (cart_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("cart_view"))

@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You are now able to login', 'success')
        return redirect(url_for('login'))
    return render_template("register.html", title="Register", form=form)

@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template("login.html", title="LogIn", form=form)

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route("/account", methods=['GET', 'POST'])
@login_required
def account():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Your account has been updated!', 'success')
        return redirect(url_for('account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    return render_template("account.html", title="Account", form=form)
