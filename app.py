from flask import Flask, render_template, redirect, url_for, request, session,flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Date
import bcrypt
from datetime import datetime
from graphs import generate_bar_chart,generate_worm_chart, generate_pie_chart, generate_gauge_charts,get_icon_status_data

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)
app.secret_key = 'secret_key'

class User(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(100),nullable=False)
    email = db.Column(db.String(100),unique=True)
    password = db.Column(db.String(100),nullable=False)

    def __init__(self,name,email,password):
        self.name = name
        self.email = email
        self.password = bcrypt.hashpw(password.encode('utf-8'),bcrypt.gensalt()).decode('utf-8')
    
    def check_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'),self.password.encode('utf-8'))

class Expenses(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(100),nullable=False)
    amount = db.Column(db.Integer,nullable=False)
    date = db.Column(db.Date, nullable=False)
    description = db.Column(db.String(100),nullable=False)

    def __init__(self,name,amount,date,description):
        self.name = name
        self.amount = amount
        self.date = date
        self.description = description

with app.app_context():
    db.create_all()

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['POST','GET'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            session['name'] = user.name
            session['email'] = user.email
            session['password'] = user.password
            print('Logged in Sucessfully!')
            return redirect('/dashboard')
        else:
            print('Invalid User')
            return render_template('login.html',error='Invalid User')

    return render_template('login.html')

@app.route('/register', methods=['POST','GET'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        newUser = User(name=name,email=email,password=password)
        db.session.add(newUser)
        db.session.commit()
        print('User has been registered')
        return redirect('/login')
    print("Cannot Register User")
    return render_template('register.html')

# @app.route('/dashboard', methods=['POST','GET'])
# def dashboard():
#     if session['name']:
#         user = User.query.filter_by(email=session['email']).first()
#         return render_template('dashboard.html',user=user)

#     return redirect('/login')

@app.route('/profile', methods = ['GET','PUT'])
def profile():
    print("HEY")
    if session['name']:
        user = User.query.filter_by(email=session['email']).first()
        return render_template('profile.html',user=user)

@app.route('/add_expenses', methods=['POST','GET'])
def add_expenses():
    if session['name']:
        if request.method == 'POST':
            name = request.form['name']
            amount = int(request.form['amount'])
            date_string = request.form['date']
            desc = request.form.get('desc')
            date_obj = datetime.strptime(date_string, "%Y-%m-%d").date()

            print("###",name,amount,date_string,desc)
            newExpense = Expenses(name=name,amount=amount,date=date_obj,description=desc)
            db.session.add(newExpense)
            db.session.commit()
            print('Expense has been added')
            return redirect('/add_expenses')
        user = User.query.filter_by(email=session['email']).first()
        return render_template('add_expenses.html',user=user)
    return redirect('/login')

@app.route('/expense_list', methods=['GET'])
def expense_list():
    if session.get('name'):
        user = User.query.filter_by(email=session['email']).first()
        sort_by = request.args.get('sort')
        order = request.args.get('order', 'asc')  # Defaults to ascending
        
        # Choose the column
        if sort_by == 'amount':
            sort_column = Expenses.amount
        elif sort_by == 'date':
            sort_column = Expenses.date
        else:
            sort_column = None
        
        # Build the query
        if sort_column is not None:
            if order == 'desc':
                expenses = Expenses.query.order_by(sort_column.desc()).all()
            else:
                expenses = Expenses.query.order_by(sort_column.asc()).all()
        else:
            expenses = Expenses.query.all()
                
        total = sum(exp.amount for exp in expenses)

        return render_template('expense_list.html',user=user, expenses=expenses, total=total, sort_by=sort_by, order=order)
    return redirect('/login')

@app.route('/dashboard', methods=['GET'])
def dashboard():
    if session.get('name'):
        user = User.query.filter_by(email=session['email']).first()
        expenses = Expenses.query.all()

        chart_div = generate_bar_chart(expenses)
        worm_chart_div = generate_worm_chart(expenses)
        pie_chart_div = generate_pie_chart(expenses)
        latest_expenses = Expenses.query.order_by(Expenses.date.desc()).limit(4).all()
        gauge_this_month, gauge_this_year, gauge_month_vs_last = generate_gauge_charts(expenses)
        status_tiles = get_icon_status_data(expenses)

        return render_template(
        'dashboard.html',
        user=user,
        chart_div=chart_div,
        worm_chart_div=worm_chart_div,
        pie_chart_div=pie_chart_div,
        latest_expenses=latest_expenses,
        gauge_this_month=gauge_this_month, 
        gauge_this_year=gauge_this_year, 
        gauge_month_vs_last=gauge_month_vs_last,
        status_tiles=status_tiles
    )



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)