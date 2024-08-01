import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import json
import logging

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///billing.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db = SQLAlchemy(app)

# Initialize LoginManager
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Set up logging
logging.basicConfig(filename='app.log', level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')

# User model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)

# Product model
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    hsn_code = db.Column(db.String(20), nullable=False)
    description = db.Column(db.String(200))
    unit = db.Column(db.String(20), nullable=False)
    rate = db.Column(db.Float, nullable=False)

# Bill model
class Bill(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bill_number = db.Column(db.String(50), unique=True, nullable=False)
    date = db.Column(db.Date, nullable=False)
    subtotal = db.Column(db.Float, nullable=False)
    cgst_total = db.Column(db.Float, nullable=False)
    sgst_total = db.Column(db.Float, nullable=False)
    grand_total = db.Column(db.Float, nullable=False)
    items = db.relationship('BillItem', backref='bill', lazy=True)

# BillItem model
class BillItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bill_id = db.Column(db.Integer, db.ForeignKey('bill.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    rate = db.Column(db.Float, nullable=False)
    amount = db.Column(db.Float, nullable=False)
    cgst_percent = db.Column(db.Float, nullable=False)
    cgst_amount = db.Column(db.Float, nullable=False)
    sgst_percent = db.Column(db.Float, nullable=False)
    sgst_amount = db.Column(db.Float, nullable=False)
    product = db.relationship('Product', backref='bill_items')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('admin'))
        flash('Invalid username or password')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/admin')
@login_required
def admin():
    products = Product.query.all()
    return render_template('admin.html', products=products)

@app.route('/add_product', methods=['GET', 'POST'])
@login_required
def add_product():
    if request.method == 'POST':
        new_product = Product(
            name=request.form['name'],
            hsn_code=request.form['hsn_code'],
            description=request.form['description'],
            unit=request.form['unit'],
            rate=float(request.form['rate'])
        )
        db.session.add(new_product)
        db.session.commit()
        flash('Product added successfully')
        return redirect(url_for('admin'))
    return render_template('add_product.html')

@app.route('/edit_product/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_product(id):
    product = Product.query.get_or_404(id)
    if request.method == 'POST':
        product.name = request.form['name']
        product.hsn_code = request.form['hsn_code']
        product.description = request.form['description']
        product.unit = request.form['unit']
        product.rate = float(request.form['rate'])
        db.session.commit()
        flash('Product updated successfully')
        return redirect(url_for('admin'))
    return render_template('edit_product.html', product=product)

@app.route('/delete_product/<int:id>')
@login_required
def delete_product(id):
    product = Product.query.get_or_404(id)
    db.session.delete(product)
    db.session.commit()
    flash('Product deleted successfully')
    return redirect(url_for('admin'))

@app.route('/get_product/<int:id>')
def get_product(id):
    product = Product.query.get_or_404(id)
    return jsonify({
        'name': product.name,
        'hsn_code': product.hsn_code,
        'unit': product.unit,
        'rate': product.rate
    })

@app.route('/create_bill', methods=['GET', 'POST'])
@login_required
def create_bill():
    products = Product.query.all()
    if request.method == 'POST':
        try:
            bill_data = json.loads(request.form['bill_data'])
            logging.info(f"Received bill data: {bill_data}")

            if not bill_data['items']:
                raise ValueError("No items in the bill")

            new_bill = Bill(
                bill_number=generate_bill_number(),
                date=datetime.now().date(),
                subtotal=bill_data['subtotal'],
                cgst_total=bill_data['cgst_total'],
                sgst_total=bill_data['sgst_total'],
                grand_total=bill_data['grand_total']
            )
            db.session.add(new_bill)
            
            for item in bill_data['items']:
                product = Product.query.get(item['product_id'])
                if not product:
                    raise ValueError(f"Product with id {item['product_id']} not found")
                
                new_item = BillItem(
                    bill=new_bill,
                    product=product,
                    quantity=item['quantity'],
                    rate=item['rate'],
                    amount=item['amount'],
                    cgst_percent=item['cgst_percent'],
                    cgst_amount=item['cgst_amount'],
                    sgst_percent=item['sgst_percent'],
                    sgst_amount=item['sgst_amount']
                )
                db.session.add(new_item)
            
            db.session.commit()
            return jsonify({"redirect": url_for('view_bill', id=new_bill.id)})
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error creating bill: {str(e)}")
            return jsonify({"error": str(e)}), 400
    
    return render_template('create_bill.html', products=products)

@app.route('/view_bill/<int:id>')
@login_required
def view_bill(id):
    bill = Bill.query.get_or_404(id)
    return render_template('bill.html', bill=bill)

def generate_bill_number():
    last_bill = Bill.query.order_by(Bill.id.desc()).first()
    if last_bill:
        last_number = int(last_bill.bill_number.split('-')[1])
        new_number = last_number + 1
    else:
        new_number = 1
    return f"BILL-{new_number:04d}"

def init_db():
    with app.app_context():
        db.create_all()
        # Check if admin user exists, if not create one
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(username='admin', password_hash=generate_password_hash('admin123'))
            db.session.add(admin)
            db.session.commit()
            print("Admin user created.")

def recreate_db():
    with app.app_context():
        db.drop_all()
        db.create_all()
        # Create admin user
        admin = User(username='admin', password_hash=generate_password_hash('admin123'))
        db.session.add(admin)
        db.session.commit()
        print("Database recreated and admin user added.")

if __name__ == '__main__':
    recreate_db()  # This will recreate the database
    app.run(debug=True)