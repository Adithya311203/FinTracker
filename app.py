from flask import Flask, render_template, redirect, url_for, request, session,flash,make_response
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

class UserDetails(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True)
    email = db.Column(db.String(100), nullable=False)
    annual_income = db.Column(db.Float, nullable=True)
    monthly_budget = db.Column(db.Float, nullable=True)
    occupation = db.Column(db.String(100), nullable=True)
    age = db.Column(db.Integer, nullable=True)
    location = db.Column(db.String(100), nullable=True)
    financial_goal = db.Column(db.String(200), nullable=True)

    user = db.relationship('User', backref=db.backref('details', uselist=False))

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

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already registered!', 'error')
            return render_template('register.html', error='Email already registered')

        newUser = User(name=name,email=email,password=password)
        db.session.add(newUser)
        db.session.commit()
        print('User has been registered')
        return redirect('/login')
    return render_template('register.html')



@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if not session.get('email'):
        return redirect('/login')

    user = User.query.filter_by(email=session['email']).first()
    details = UserDetails.query.filter_by(user_id=user.id).first()

    if not details:
        details = UserDetails(user_id=user.id, email=user.email)
        db.session.add(details)
        db.session.commit()
        session['ai_dirty'] = True

    if request.method == 'POST':
        field = request.form.get('save_field')
        value = request.form.get(field)

        # Cast types safely
        if field in ['annual_income', 'monthly_budget']:
            setattr(details, field, float(value) if value else None)
        elif field == 'age':
            setattr(details, field, int(value) if value else None)
        else:
            setattr(details, field, value)

        db.session.commit()
        session['ai_dirty'] = True
        flash(f"{field.replace('_', ' ').title()} updated!", "success")
        return redirect('/profile')

    return render_template('profile.html', user=user, details=details)


@app.route('/add_expenses', methods=['POST','GET'])
def add_expenses():
    if not session.get('name'):
        return redirect('/login')
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
            session['ai_dirty'] = True
            print('Expense has been added')
            return redirect('/add_expenses')
        user = User.query.filter_by(email=session['email']).first()
        return render_template('add_expenses.html',user=user)

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
    if 'email' not in session:
        return redirect('/login')

    user = User.query.filter_by(email=session['email']).first()
    details = UserDetails.query.filter_by(user_id=user.id).first()

    monthly_budget = details.monthly_budget if details and details.monthly_budget else 0

    expenses = Expenses.query.all()

    chart_div = generate_bar_chart(expenses)
    worm_chart_div = generate_worm_chart(expenses)
    pie_chart_div = generate_pie_chart(expenses)

    gauge_this_month, gauge_this_year, gauge_month_vs_last = generate_gauge_charts(
        expenses, monthly_budget_limit=monthly_budget
    )

    status_tiles = get_icon_status_data(expenses, monthly_budget=monthly_budget)
    latest_expenses = Expenses.query.order_by(Expenses.date.desc()).limit(4).all()

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
        status_tiles=status_tiles,
        monthly_budget=monthly_budget
    )

@app.route('/download_txt', methods=['POST'])
def download_txt():
    if 'email' not in session:
        return redirect('/login')

    user = User.query.filter_by(email=session['email']).first()
    details = UserDetails.query.filter_by(user_id=user.id).first()
    expenses = Expenses.query.all()

    total_spent = sum(e.amount for e in expenses)
    latest_expenses = sorted(expenses, key=lambda x: x.date, reverse=True)[:5]

    txt = f"--- FinTracker Report ---\n\n"
    txt += f"Name: {user.name}\nEmail: {user.email}\n\n"

    if details:
        txt += f"Age: {details.age or 'N/A'}\n"
        txt += f"Location: {details.location or 'N/A'}\n"
        txt += f"Occupation: {details.occupation or 'N/A'}\n"
        txt += f"Annual Income: ₹{details.annual_income or 'N/A'}\n"
        txt += f"Monthly Budget: ₹{details.monthly_budget or 'N/A'}\n"
        txt += f"Financial Goal: {details.financial_goal or 'N/A'}\n"

    # Budget comparison
    current_month = datetime.now().month
    current_year = datetime.now().year
    this_month_expenses = [e.amount for e in expenses if e.date.month == current_month and e.date.year == current_year]
    spent_this_month = sum(this_month_expenses)

    txt += f"\n--- Budget Comparison ---\n"
    txt += f"Spent This Month: ₹{spent_this_month}\n"
    if details and details.monthly_budget:
        budget = details.monthly_budget
        txt += f"Budget Remaining: ₹{budget - spent_this_month}\n"
        txt += "Status: "
        if spent_this_month > budget:
            txt += "❌ Over Budget\n"
        else:
            txt += "✅ Within Budget\n"
    else:
        txt += "Monthly budget not set.\n"

    txt += f"\n--- Expense Summary ---\n"
    txt += f"Total Expenses: ₹{total_spent}\n"
    txt += f"Total Entries: {len(expenses)}\n\n"

    txt += f"--- Latest 5 Expenses ---\n"
    for e in latest_expenses:
        txt += f"{e.date.strftime('%Y-%m-%d')}: ₹{e.amount} for {e.name} ({e.description})\n"

    response = make_response(txt)
    response.headers['Content-Type'] = 'text/plain'
    response.headers['Content-Disposition'] = 'attachment; filename=fintracker_report'+datetime.now().strftime('%Y%m%d%H%M%S')+'.txt'
    return response


import os
import json
import threading
from ai import analyze_txt_content, generate_data_hash


import markdown
from ai import analyze_txt_content, generate_data_hash

CACHE_FILE = "ai_cache.json"

@app.route('/ai')
def ai():
    if 'email' not in session:
        return redirect('/login')

    user = User.query.filter_by(email=session['email']).first()
    details = UserDetails.query.filter_by(user_id=user.id).first()
    expenses = Expenses.query.all()

    profile_data = {field: getattr(details, field) or "Not set" for field in
                    ['annual_income', 'monthly_budget', 'occupation', 'age', 'location', 'financial_goal']}
    expense_data = [{"name": e.name, "amount": e.amount, "date": str(e.date), "desc": e.description} for e in expenses[:10]]

    current_hash = generate_data_hash(profile_data, expense_data)
    cache = {}
    last_refreshed = None

    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r') as f:
            cache = json.load(f)

        # ✅ Get file modification time for "Last Refreshed"
        last_refreshed = datetime.fromtimestamp(os.path.getmtime(CACHE_FILE)).strftime("%Y-%m-%d %H:%M:%S")

        if cache.get('hash') == current_hash:
            rendered_output = markdown.markdown(
                cache.get('response', 'Generating new analysis...'),
                extensions=['fenced_code', 'tables']
            )
            return render_template('ai.html', user=user, analysis=rendered_output, last_refreshed=last_refreshed)

    cached_response = cache.get('response', "Generating new analysis...")
    # if "Would you like" in cached_response:
    #     cached_response = cached_response.rsplit("Would you like", 1)[0].strip()

    #  AI will generate in the background
    def background_ai_processing():
        profile_summary = f"Income: ₹{details.annual_income}, Budget: ₹{details.monthly_budget}, Goal: {details.financial_goal or 'N/A'}"
        expense_summary = f"Recent Expenses Total: ₹{sum(e['amount'] for e in expense_data)}"
        text = profile_summary + "\n" + expense_summary

        categories = list(set(e['desc'] for e in expense_data))
        if categories:
            text += f"\nExpense Categories: {', '.join(categories)}"

        result = analyze_txt_content(text)

        with open(CACHE_FILE, 'w') as f:
            json.dump({'hash': current_hash, 'response': result}, f)

    threading.Thread(target=background_ai_processing).start()
    rendered_output = markdown.markdown(cached_response, extensions=['fenced_code', 'tables'])

    #  even here, we pass last_refreshed if available
    return render_template('ai.html', user=user, analysis=rendered_output, last_refreshed=last_refreshed)


def main():
    app.run(host='0.0.0.0', port=5000, debug=True)

if __name__ == '__main__':
    main()
