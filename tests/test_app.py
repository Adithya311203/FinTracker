import pytest
import os
import json
import sys
from datetime import date
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

    expense = Expenses(name=test_name, amount=test_amount, date=test_date, description=test_description)

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

def test_main_runs_app(monkeypatch):
    from app import main
    called = {}

    def fake_run(*args, **kwargs):
        called['called'] = True
        assert kwargs['host'] == '0.0.0.0'
        assert kwargs['port'] == 5000
        assert kwargs['debug'] is True

    monkeypatch.setattr("app.app.run", fake_run)
    main()
    assert called.get('called')


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

    with patch('app.Expenses') as mock_expense_cls, \
         patch('app.db.session.add') as mock_add, \
         patch('app.db.session.commit') as mock_commit:

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
        sess['name'] = 'TestUser'
        sess['email'] = 'test@example.com'

    mock_user = MagicMock()
    mock_expenses = [MagicMock(amount=100), MagicMock(amount=200)]

    with patch('app.User.query') as mock_user_query, \
         patch('app.Expenses') as mock_expenses_model, \
         patch('app.render_template') as mock_render:

        mock_user_query.filter_by.return_value.first.return_value = mock_user
        mock_expenses_model.amount.asc.return_value = 'amount_asc'
        mock_expenses_model.query.order_by.return_value.all.return_value = mock_expenses

        mock_render.return_value = 'rendered'

        response = client.get('/expense_list?sort=amount&order=asc')

        mock_expenses_model.query.order_by.assert_called_once_with('amount_asc')
        mock_render.assert_called_once_with(
            'expense_list.html',
            user=mock_user,
            expenses=mock_expenses,
            total=300,
            sort_by='amount',
            order='asc'
        )
        assert response.data == b'rendered'

def test_expense_list_sort_by_date(client):
    with client.session_transaction() as sess:
        sess['name'] = 'TestUser'
        sess['email'] = 'test@example.com'

    mock_user = MagicMock()
    mock_expenses = [MagicMock(amount=100), MagicMock(amount=200)]

    with patch('app.User.query') as mock_user_query, \
         patch('app.Expenses') as mock_expenses_model, \
         patch('app.render_template') as mock_render:

        mock_user_query.filter_by.return_value.first.return_value = mock_user

        # Mocking sort column access
        mock_sort_column = MagicMock()
        mock_sort_column.desc.return_value = 'date_desc'
        mock_expenses_model.date = mock_sort_column

        mock_expenses_model.query.order_by.return_value.all.return_value = mock_expenses
        mock_render.return_value = b'rendered'

        response = client.get('/expense_list?sort=date&order=desc')

        mock_expenses_model.query.order_by.assert_called_once_with('date_desc')
        mock_render.assert_called_once_with(
            'expense_list.html',
            user=mock_user,
            expenses=mock_expenses,
            total=300,
            sort_by='date',
            order='desc'
        )
        assert response.data == b'rendered'

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

        client.get('/ai')  # triggers thread

        mt.call_args[1]['target']()  # manually run background

        mo.assert_called_with('ai_cache.json', 'w')
        assert rt.called



def test_download_txt_route(client):
    from datetime import datetime
    today = datetime.now().date()

    # Reusable expenses
    base_expenses = [
        MagicMock(name="Food", amount=1000, date=today, description="Lunch"),
        MagicMock(name="Fuel", amount=1500, date=today, description="Petrol"),
        MagicMock(name="Groceries", amount=800, date=today, description="Home needs")
    ]

    # 1. ✅ Case: Over Budget
    with client.session_transaction() as sess:
        sess['email'] = 'test@example.com'

    mock_user = MagicMock(name="Test User", email="test@example.com")
    over_budget_details = MagicMock(
        age=30, location="Mumbai", occupation="Engineer",
        annual_income=1000000, monthly_budget=1000, financial_goal="Save"
    )

    with patch('app.User.query') as uq, \
         patch('app.UserDetails.query') as dq, \
         patch('app.Expenses.query') as eq:

        uq.filter_by.return_value.first.return_value = mock_user
        dq.filter_by.return_value.first.return_value = over_budget_details
        eq.all.return_value = base_expenses

        res = client.post('/download_txt')
        body = res.data.decode()
        assert "❌ Over Budget" in body

    # 2. ✅ Case: Within Budget
    within_budget_details = MagicMock(
        age=30, location="Mumbai", occupation="Engineer",
        annual_income=1000000, monthly_budget=10000, financial_goal="Save"
    )

    with patch('app.User.query') as uq, \
         patch('app.UserDetails.query') as dq, \
         patch('app.Expenses.query') as eq:

        uq.filter_by.return_value.first.return_value = mock_user
        dq.filter_by.return_value.first.return_value = within_budget_details
        eq.all.return_value = base_expenses

        res = client.post('/download_txt')
        body = res.data.decode()
        assert "✅ Within Budget" in body

    # 3. ✅ Case: Monthly budget not set
    no_budget_details = MagicMock(
        age=30, location="Mumbai", occupation="Engineer",
        annual_income=1000000, monthly_budget=None, financial_goal="Save"
    )

    with patch('app.User.query') as uq, \
         patch('app.UserDetails.query') as dq, \
         patch('app.Expenses.query') as eq:

        uq.filter_by.return_value.first.return_value = mock_user
        dq.filter_by.return_value.first.return_value = no_budget_details
        eq.all.return_value = base_expenses

        res = client.post('/download_txt')
        body = res.data.decode()
        assert "Monthly budget not set." in body

def test_ai_background_writes_cache_with_categories(client):
    with client.session_transaction() as s: s['email'] = 'x'

    mock_expense = MagicMock(name='Coffee', amount=100, date='2025-07-01', description='Food')

    with patch('app.User.query'), \
         patch('app.UserDetails.query'), \
         patch('app.Expenses.query') as eq, \
         patch('app.generate_data_hash', return_value='abc'), \
         patch('app.os.path.exists', return_value=False), \
         patch('app.render_template'), \
         patch('app.analyze_txt_content', return_value='AI output') as mock_ai, \
         patch('builtins.open', mock_open()) as mo, \
         patch('app.threading.Thread') as mt:

        eq.all.return_value = [mock_expense]  # Non-empty desc triggers categories logic

        client.get('/ai')
        mt.call_args[1]['target']()  # Call background_ai_processing manually

        # ✅ This covers the "if categories:" branch
        mo.assert_called_with('ai_cache.json', 'w')
        mock_ai.assert_called_once()
        assert 'Expense Categories:' in mock_ai.call_args[0][0]

def test_dashboard_route_authenticated(client):
    # Set up mock session
    with client.session_transaction() as sess:
        sess['email'] = 'test@example.com'

    # Mock objects
    mock_user = MagicMock(id=1, email='test@example.com')
    mock_details = MagicMock(monthly_budget=5000)
    mock_expenses = [MagicMock(), MagicMock()]
    mock_latest_expenses = [MagicMock() for _ in range(4)]

    with patch('app.User.query') as uq, \
         patch('app.UserDetails.query') as dq, \
         patch('app.Expenses.query') as eq, \
         patch('app.generate_bar_chart', return_value='<div>bar</div>') as bar_chart, \
         patch('app.generate_worm_chart', return_value='<div>worm</div>') as worm_chart, \
         patch('app.generate_pie_chart', return_value='<div>pie</div>') as pie_chart, \
         patch('app.generate_gauge_charts', return_value=('g1', 'g2', 'g3')) as gauge_charts, \
         patch('app.get_icon_status_data', return_value=['tile1', 'tile2']) as icon_data, \
         patch('app.render_template') as rt:

        # Mock DB returns
        uq.filter_by.return_value.first.return_value = mock_user
        dq.filter_by.return_value.first.return_value = mock_details
        eq.all.return_value = mock_expenses
        eq.order_by.return_value.limit.return_value.all.return_value = mock_latest_expenses
        rt.return_value = 'rendered'

        # Call the route
        res = client.get('/dashboard')

        # Assertions
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
