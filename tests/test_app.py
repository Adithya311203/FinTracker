import pytest
import os
import json
import sys
from datetime import date,datetime
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    
from flask import session
from app import app as flask_app,User, Expenses
# import app as app_module
# flask_app = app_module.app
# User = app_module.User

@pytest.fixture
def client():
    flask_app.config['TESTING'] = True
    flask_app.config['WTF_CSRF_ENABLED'] = False
    with flask_app.test_client() as client:
        with flask_app.app_context():
            yield client

def test_index_redirects_to_login(client):
    response = client.get('/')
    assert response.status_code == 302
    assert '/login' in response.location

def test_get_login_page(client):
    response = client.get('/login')
    assert response.status_code == 200
    assert b'login' in response.data.lower()

def test_get_register_page(client):
    response = client.get('/register')
    assert response.status_code == 200
    assert b'register' in response.data.lower()

def test_redirect_profile_if_not_logged_in(client):
    response = client.get('/profile', follow_redirects=False)
    assert response.status_code == 302
    assert '/login' in response.location

def test_redirect_add_expenses_if_not_logged_in(client):
    response = client.get('/add_expenses', follow_redirects=False)
    assert response.status_code == 302
    assert '/login' in response.location

def test_redirect_dashboard_if_not_logged_in(client):
    response = client.get('/dashboard', follow_redirects=False)
    assert response.status_code == 302
    assert '/login' in response.location

def test_redirect_ai_if_not_logged_in(client):
    response = client.get('/ai', follow_redirects=False)
    assert response.status_code == 302
    assert '/login' in response.location

def test_redirect_download_txt_if_not_logged_in(client):
    response = client.post('/download_txt', follow_redirects=False)
    assert response.status_code == 302
    assert '/login' in response.location

def test_expense_list_redirect_if_not_logged_in(client):
    response = client.get('/expense_list', follow_redirects=False)
    assert response.status_code == 302
    assert '/login' in response.location

def test_user_model_password_hashing():
    user = User(name='Test User', email='test@example.com', password='secret123')
    assert user.name == 'Test User'
    assert user.email == 'test@example.com'
    assert user.password != 'secret123'  # ensure it's hashed
    assert user.check_password('secret123')
    assert not user.check_password('wrongpass')

def test_expenses_model_initialization():
    test_name = 'Lunch'
    test_amount = 250
    test_date = date(2025, 7, 1)
    test_description = 'Office lunch'

    expense = Expenses(name=test_name, amount=test_amount, date=test_date, description=test_description, user_id=1)

    assert expense.name == test_name
    assert expense.amount == test_amount
    assert expense.date == test_date
    assert expense.description == test_description

from unittest.mock import patch, MagicMock, mock_open
from flask import template_rendered

def test_login_post_success_mock(client):
    mock_user = MagicMock()
    mock_user.name = 'Test User'
    mock_user.email = 'test@example.com'
    mock_user.password = 'hashed_pw'
    mock_user.check_password.return_value = True

    with patch('app.User.query') as mock_query:
        mock_query.filter_by.return_value.first.return_value = mock_user
        response = client.post('/login', data={
            'email': 'test@example.com',
            'password': 'secret123'
        }, follow_redirects=False)

        assert response.status_code == 302
        assert '/dashboard' in response.location


def test_login_post_invalid_user_mock(client):
    with patch('app.User.query') as mock_query:
        mock_query.filter_by.return_value.first.return_value = None
        response = client.post('/login', data={
            'email': 'nonexistent@example.com',
            'password': 'wrongpass'
        }, follow_redirects=True)

        assert response.status_code == 200
        assert b'invalid user' in response.data.lower()


def test_register_post_existing_user(client):
    # Mock an existing user being returned
    mock_user = MagicMock()
    with patch('app.User.query') as mock_query, \
         patch('app.render_template') as mock_render:
        mock_query.filter_by.return_value.first.return_value = mock_user
        mock_render.return_value = "mocked register page"

        response = client.post('/register', data={
            'name': 'Test',
            'email': 'test@example.com',
            'password': 'password123'
        })

        assert response.status_code == 200
        mock_render.assert_called_with('register.html', error='Email already registered')

def test_register_post_new_user(client):
    with patch('app.User.query') as mock_query, \
         patch('app.db.session.add') as mock_add, \
         patch('app.db.session.commit') as mock_commit, \
         patch('app.redirect') as mock_redirect:

        mock_query.filter_by.return_value.first.return_value = None
        mock_redirect.return_value = MagicMock()  # Return a dummy response

        client.post('/register', data={
            'name': 'NewUser',
            'email': 'new@example.com',
            'password': 'securepass'
        })

        mock_add.assert_called()
        mock_commit.assert_called()
        mock_redirect.assert_called_once_with('/login')

def test_profile_get_flow(client):
    with client.session_transaction() as sess:
        sess['email'] = 'mock@example.com'

    with patch('app.User.query') as mock_user_query, \
         patch('app.UserDetails.query') as mock_details_query, \
         patch('app.db.session.add') as mock_add, \
         patch('app.db.session.commit') as mock_commit, \
         patch('app.render_template') as mock_render:

        mock_user = MagicMock(id=1, email='mock@example.com')
        mock_user_query.filter_by.return_value.first.return_value = mock_user
        mock_details_query.filter_by.return_value.first.return_value = None

        mock_render.return_value = "rendered"

        response = client.get('/profile')

        mock_add.assert_called()
        mock_commit.assert_called()
        mock_render.assert_called_once()
        assert response.data == b"rendered"


def test_profile_post_flow(client):
    with client.session_transaction() as sess:
        sess['email'] = 'mock@example.com'

    with patch('app.User.query') as mock_user_query, \
         patch('app.UserDetails.query') as mock_details_query, \
         patch('app.db.session.commit') as mock_commit, \
         patch('app.redirect') as mock_redirect, \
         patch('app.flash') as mock_flash:

        mock_user = MagicMock(id=1, email='mock@example.com')
        mock_details = MagicMock()

        mock_user_query.filter_by.return_value.first.return_value = mock_user
        mock_details_query.filter_by.return_value.first.return_value = mock_details
        mock_redirect.return_value = "redirected"

        response = client.post('/profile', data={
            'save_field': 'age',
            'age': '25'
        })

        assert mock_commit.called
        mock_flash.assert_called_with('Age updated!', 'success')
        mock_redirect.assert_called_once_with('/profile')

def test_profile_post_annual_income_field(client):
    with client.session_transaction() as sess:
        sess['email'] = 'mock@example.com'

    with patch('app.User.query') as mock_user_query, \
         patch('app.UserDetails.query') as mock_details_query, \
         patch('app.db.session.commit'), \
         patch('app.redirect') as mock_redirect, \
         patch('app.flash'):

        mock_user = MagicMock(id=1, email='mock@example.com')
        mock_details = MagicMock()

        mock_user_query.filter_by.return_value.first.return_value = mock_user
        mock_details_query.filter_by.return_value.first.return_value = mock_details
        mock_redirect.return_value = "redirected"

        client.post('/profile', data={
            'save_field': 'annual_income',
            'annual_income': '500000'
        })

        assert mock_details.annual_income == 500000.0
        mock_redirect.assert_called_once_with('/profile')

def test_profile_post_other_field(client):
    with client.session_transaction() as sess:
        sess['email'] = 'mock@example.com'

    with patch('app.User.query') as mock_user_query, \
         patch('app.UserDetails.query') as mock_details_query, \
         patch('app.db.session.commit'), \
         patch('app.redirect') as mock_redirect, \
         patch('app.flash'):

        mock_user = MagicMock(id=1, email='mock@example.com')
        mock_details = MagicMock()

        mock_user_query.filter_by.return_value.first.return_value = mock_user
        mock_details_query.filter_by.return_value.first.return_value = mock_details
        mock_redirect.return_value = "redirected"

        client.post('/profile', data={
            'save_field': 'occupation',
            'occupation': 'Engineer'
        })

        assert mock_details.occupation == 'Engineer'
        mock_redirect.assert_called_once_with('/profile')

def test_add_expense_post_valid_data(client):
    with client.session_transaction() as sess:
        sess['name'] = 'TestUser'
        sess['email'] = 'test@example.com'

    with patch('app.User.query') as mock_user_query, \
        patch('app.Expenses') as mock_expense_cls, \
        patch('app.db.session.add') as mock_add, \
        patch('app.db.session.commit') as mock_commit:

        mock_user = MagicMock(id=1)
        mock_user_query.filter_by.return_value.first.return_value = mock_user
        response = client.post('/add_expenses', data={
            'name': 'Groceries',
            'amount': '250',
            'date': '2025-07-01',
            'desc': 'Food & supplies'
        })

        mock_expense_cls.assert_called_once()
        mock_add.assert_called_once()
        mock_commit.assert_called_once()
        assert response.status_code == 302
        assert '/add_expenses' in response.location

def test_add_expense_get_form_render(client):
    with client.session_transaction() as sess:
        sess['name'] = 'TestUser'
        sess['email'] = 'test@example.com'

    with patch('app.User.query') as mock_user_query:
        mock_user = MagicMock()
        mock_user_query.filter_by.return_value.first.return_value = mock_user

        response = client.get('/add_expenses')
        assert response.status_code == 200
        assert b'add' in response.data.lower()  # Or something more specific from the template

def test_expense_list_sort_by_amount_asc(client):
    with client.session_transaction() as sess:
        sess['email'] = 'test@example.com'
        sess['name'] = 'Test User'

    mock_user = MagicMock(id=1, email='test@example.com')

    # Create mock expense objects
    mock_expense1 = MagicMock(amount=100)
    mock_expense2 = MagicMock(amount=200)
    mock_expenses = [mock_expense1, mock_expense2]

    with patch('app.User.query') as mock_user_query, \
         patch('app.Expenses.query') as mock_exp_query, \
         patch('app.render_template') as mock_render:

        # Mock user lookup
        mock_user_query.filter_by.return_value.first.return_value = mock_user

        # Chain: Expenses.query.filter_by().order_by().all()
        mock_filter = MagicMock()
        mock_order_by = MagicMock()
        mock_order_by.all.return_value = mock_expenses
        mock_filter.order_by.return_value = mock_order_by
        mock_exp_query.filter_by.return_value = mock_filter

        # Final HTML output stub
        mock_render.return_value = 'rendered'

        response = client.get('/expense_list?sort=amount&order=asc')

        # 🔍 Assertions
        mock_exp_query.filter_by.assert_called_once_with(user_id=mock_user.id)
        mock_filter.order_by.assert_called_once()  # Confirm sort
        mock_render.assert_called_once()           # Confirm page rendered


def test_expense_list_sort_by_date(client):
    with client.session_transaction() as sess:
        sess['email'] = 'test@example.com'
        sess['name'] = 'Test User'

    mock_user = MagicMock(id=1, email='test@example.com')

    mock_expense1 = MagicMock(date=datetime(2025, 7, 1))
    mock_expense2 = MagicMock(date=datetime(2025, 7, 2))
    mock_expenses = [mock_expense2, mock_expense1]

    with patch('app.User.query') as mock_user_query, \
         patch('app.Expenses.query') as mock_exp_query, \
         patch('app.render_template') as mock_render:

        mock_user_query.filter_by.return_value.first.return_value = mock_user

        # Chain mocking
        mock_filtered = MagicMock()
        mock_exp_query.filter_by.return_value = mock_filtered

        mock_ordered = MagicMock()
        mock_filtered.order_by.return_value = mock_ordered
        mock_ordered.all.return_value = mock_expenses

        mock_render.return_value = 'rendered'

        response = client.get('/expense_list?sort=date&order=desc')

        # Assert that sort was used correctly
        mock_filtered.order_by.assert_called_once()
        mock_filtered.order_by.return_value.all.assert_called_once()
        mock_render.assert_called_once()

def test_expense_list_invalid_sort_key(client):
    with client.session_transaction() as sess:
        sess['name'], sess['email'] = 'TestUser', 'test@example.com'

    with patch('app.User.query') as uq, patch('app.Expenses.query') as eq, patch('app.render_template') as rt:
        uq.filter_by.return_value.first.return_value = MagicMock()
        eq.all.return_value = [MagicMock(amount=100), MagicMock(amount=200)]
        rt.return_value = b'rendered'
        assert client.get('/expense_list?sort=xyz').data == b'rendered'




def test_ai_falls_back_to_background_processing(client):
    from io import StringIO

    with client.session_transaction() as sess:
        sess['email'] = 'test@example.com'

    mock_user = MagicMock(id=1, email="test@example.com")
    mock_details = MagicMock()

    with patch('app.User.query') as uq, \
         patch('app.UserDetails.query') as dq, \
         patch('app.Expenses.query') as eq, \
         patch('app.generate_data_hash', return_value="xyz456"), \
         patch('app.os.path.exists', return_value=False), \
         patch('app.analyze_txt_content', return_value='Mocked Summary'), \
         patch('app.render_template') as rt, \
         patch('app.markdown.markdown', return_value="mocked html"), \
         patch('app.threading.Thread') as mt, \
         patch('builtins.open', return_value=StringIO()) as mo:

        uq.filter_by.return_value.first.return_value = mock_user
        dq.filter_by.return_value.first.return_value = mock_details
        eq.all.return_value = []
        rt.return_value = b'rendered fallback'
        mock_user.id = 1
        client.get('/ai')  # triggers thread

        mt.call_args[1]['target']()  # manually run background
        mo.assert_any_call(f'ai_cache_{mock_user.id}.json', 'w')
        # mo.assert_called_with('ai_cache.json', 'w')
        assert rt.called


def test_download_txt_route(client):
    with client.session_transaction() as sess:
        sess['email'] = 'test@example.com'
        sess['name'] = 'Test User'

    mock_user = MagicMock(name="Test User", id=1, email="test@example.com")

    # 1️⃣ Over-Budget Scenario
    mock_details_over = MagicMock()
    mock_details_over.annual_income = 100000
    mock_details_over.monthly_budget = 1000
    mock_details_over.financial_goal = "Save more"
    mock_details_over.age = 25
    mock_details_over.location = "Chennai"
    mock_details_over.occupation = "Engineer"

    mock_expense1 = MagicMock(name="Coffee", amount=600, date=datetime(2025, 7, 1), description="Food")
    mock_expense2 = MagicMock(name="Books", amount=700, date=datetime(2025, 7, 2), description="Education")

    # 2️⃣ No Budget Scenario
    mock_details_none = MagicMock()
    mock_details_none.annual_income = 200000
    mock_details_none.monthly_budget = None
    mock_details_none.financial_goal = "Retire Early"
    mock_details_none.age = 30
    mock_details_none.location = "Mumbai"
    mock_details_none.occupation = "Teacher"

    mock_expense3 = MagicMock(name="Snacks", amount=100, date=datetime(2025, 7, 3), description="Food")

    # 3️⃣ Within Budget Scenario
    mock_details_within = MagicMock()
    mock_details_within.annual_income = 300000
    mock_details_within.monthly_budget = 5000
    mock_details_within.financial_goal = "Travel"
    mock_details_within.age = 28
    mock_details_within.location = "Delhi"
    mock_details_within.occupation = "Artist"

    mock_expense4 = MagicMock(name="Lunch", amount=400, date=datetime(2025, 7, 4), description="Food")
    mock_expense5 = MagicMock(name="Metro", amount=300, date=datetime(2025, 7, 5), description="Transport")

    with patch('app.User.query') as uq, \
         patch('app.UserDetails.query') as dq, \
         patch('app.Expenses.query') as eq:

        uq.filter_by.return_value.first.return_value = mock_user

        # --- First: Over Budget ---
        dq.filter_by.return_value.first.return_value = mock_details_over
        eq.filter_by.return_value.all.return_value = [mock_expense1, mock_expense2]

        res1 = client.get('/download_txt')
        txt1 = res1.data.decode()
        assert "❌ Over Budget" in txt1
        assert "Coffee" in txt1 and "Books" in txt1

        # --- Second: No Budget ---
        dq.filter_by.return_value.first.return_value = mock_details_none
        eq.filter_by.return_value.all.return_value = [mock_expense3]

        res2 = client.get('/download_txt')
        txt2 = res2.data.decode()
        assert "Monthly budget not set." in txt2
        assert "Snacks" in txt2

        # --- Third: Within Budget ---
        dq.filter_by.return_value.first.return_value = mock_details_within
        eq.filter_by.return_value.all.return_value = [mock_expense4, mock_expense5]

        res3 = client.get('/download_txt')
        txt3 = res3.data.decode()
        assert "✅ Within Budget" in txt3
        assert "Lunch" in txt3 and "Metro" in txt3



def test_ai_background_writes_cache_with_categories(client):
    with client.session_transaction() as s:
        s['email'] = 'x@example.com'

    dummy_expense = {
        "name": "Coffee",
        "amount": 100.0,
        "date": "2025-07-01",
        "description": "Food"
    }

    mock_user = MagicMock(id=42, email="x@example.com")
    mock_details = MagicMock()
    mock_details.annual_income = 1000000
    mock_details.monthly_budget = 5000
    mock_details.financial_goal = "Save"

    with patch('app.User.query') as uq, \
         patch('app.UserDetails.query') as dq, \
         patch('app.Expenses.query') as eq, \
         patch('app.generate_data_hash', return_value='abc'), \
         patch('app.os.path.exists', return_value=False), \
         patch('app.render_template'), \
         patch('app.analyze_txt_content', side_effect=lambda p: p) as mock_ai, \
         patch('builtins.open', mock_open()) as mo, \
         patch('app.threading.Thread') as mt:

        uq.filter_by.return_value.first.return_value = mock_user
        dq.filter_by.return_value.first.return_value = mock_details

        # ✅ Patch .filter_by().all()
        eq.filter_by.return_value.all.return_value = [MagicMock(**dummy_expense)]

        client.get('/ai')
        mt.call_args[1]['target']()  # run the background thread manually

        mo.assert_any_call(f'ai_cache_{mock_user.id}.json', 'w')

        prompt = mock_ai.call_args[0][0]
        print("Prompt used:\n", prompt)

        assert "Expense Categories:" in prompt
        assert "Food" in prompt
        assert "Recent Expenses Total: ₹100.0" in prompt

def test_dashboard_route_authenticated(client):
    with client.session_transaction() as sess:
        sess['email'] = 'test@example.com'

    mock_user = MagicMock(id=1, email='test@example.com')
    mock_details = MagicMock(monthly_budget=5000)
    mock_expenses = [MagicMock(), MagicMock()]
    mock_latest_expenses = [MagicMock() for _ in range(4)]

    with patch('app.User.query') as uq, \
         patch('app.UserDetails.query') as dq, \
         patch('app.Expenses.query') as eq, \
         patch('app.generate_bar_chart', return_value='<div>bar</div>'), \
         patch('app.generate_worm_chart', return_value='<div>worm</div>'), \
         patch('app.generate_pie_chart', return_value='<div>pie</div>'), \
         patch('app.generate_gauge_charts', return_value=('g1', 'g2', 'g3')), \
         patch('app.get_icon_status_data', return_value=['tile1', 'tile2']), \
         patch('app.render_template') as rt:

        uq.filter_by.return_value.first.return_value = mock_user
        dq.filter_by.return_value.first.return_value = mock_details

        # Mock for Expenses.query.filter_by().all()
        eq.filter_by.return_value.all.return_value = mock_expenses

        # Mock for Expenses.query.filter_by().order_by().limit().all()
        mock_filter = MagicMock()
        mock_order = MagicMock()
        mock_limit = MagicMock()
        eq.filter_by.return_value = mock_filter
        mock_filter.order_by.return_value = mock_order
        mock_order.limit.return_value = mock_limit
        mock_limit.all.return_value = mock_latest_expenses


        rt.return_value = 'rendered'

        res = client.get('/dashboard')

        assert res.data == b'rendered'
        rt.assert_called_once_with(
            'dashboard.html',
            user=mock_user,
            chart_div='<div>bar</div>',
            worm_chart_div='<div>worm</div>',
            pie_chart_div='<div>pie</div>',
            latest_expenses=mock_latest_expenses,
            gauge_this_month='g1',
            gauge_this_year='g2',
            gauge_month_vs_last='g3',
            status_tiles=['tile1', 'tile2'],
            monthly_budget=5000
        )


def test_ai_strips_would_you_like_prompt(client):
    with client.session_transaction() as sess:
        sess['email'] = 'test@example.com'

    fake_cached_data = {
        "hash": "abc123",
        "response": "Here are your insights. Would you like to export them?"
    }

    with patch('app.User.query') as uq, \
         patch('app.UserDetails.query') as dq, \
         patch('app.Expenses.query.all', return_value=[]), \
         patch('app.generate_data_hash', return_value="abc123"), \
         patch('app.os.path.exists', return_value=True), \
         patch('app.os.path.getmtime', return_value=1720000000), \
         patch('builtins.open', mock_open(read_data=json.dumps(fake_cached_data))), \
         patch('app.markdown.markdown') as md, \
         patch('app.render_template') as rt:

        mock_user = MagicMock(id=1, email='test@example.com')
        uq.filter_by.return_value.first.return_value = mock_user
        dq.filter_by.return_value.first.return_value = MagicMock()
        rt.return_value = b'done'
        res = client.get('/ai')
        assert res.data == b'done'
