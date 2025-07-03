import pytest
from unittest.mock import MagicMock
from types import SimpleNamespace
from graphs import (
    generate_bar_chart, generate_pie_chart, generate_worm_chart,
    generate_gauge_charts, generate_sparkline, get_icon_status_data
)
from datetime import date

@pytest.fixture
def sample_expenses():
    # Use real data instead of MagicMock
    return [
        SimpleNamespace(name="Food", amount=200, date=date(2025, 7, 1)),
        SimpleNamespace(name="Transport", amount=100, date=date(2025, 7, 2)),
        SimpleNamespace(name="Food", amount=300, date=date(2025, 7, 3)),
        SimpleNamespace(name="Entertainment", amount=150, date=date(2025, 6, 30)),
    ]
def test_generate_bar_chart_returns_div(sample_expenses):
    output = generate_bar_chart(sample_expenses)
    assert isinstance(output, str)
    assert output.startswith("<div")

def test_generate_pie_chart_returns_div(sample_expenses):
    output = generate_pie_chart(sample_expenses)
    assert isinstance(output, str)
    assert output.startswith("<div")

def test_generate_worm_chart_with_valid_dates(sample_expenses):
    output = generate_worm_chart(sample_expenses)
    assert isinstance(output, str)
    assert output.startswith("<div")

def test_generate_worm_chart_with_invalid_dates():
    mock_expenses = [MagicMock(name="X", amount=100, date="invalid")]
    output = generate_worm_chart(mock_expenses)
    assert "No valid data" in output

def test_generate_gauge_charts_returns_all(sample_expenses):
    gm, gy, gvsl = generate_gauge_charts(sample_expenses, monthly_budget_limit=500)
    assert all(isinstance(x, str) and x.startswith("<div") for x in [gm, gy, gvsl])

def test_generate_gauge_charts_empty_input():
    gm, gy, gvsl = generate_gauge_charts([], monthly_budget_limit=1000)
    assert "No gauge data" in gm

def test_generate_sparkline_returns_div(sample_expenses):
    output = generate_sparkline(sample_expenses)
    assert isinstance(output, str)
    assert output.startswith("<div")

def test_generate_sparkline_empty_returns_message():
    output = generate_sparkline([])
    assert "No data for sparkline" in output

def test_get_icon_status_data_structure(sample_expenses):
    tiles = get_icon_status_data(sample_expenses, monthly_budget=1000)
    assert isinstance(tiles, list)
    assert len(tiles) == 6
    assert all("icon" in t and "label" in t and "value" in t for t in tiles)

def test_create_gauge_under_branch():
    from graphs import create_gauge
    out = create_gauge("Gauge", 10000, 50000, show_budget=True)
    assert "📉" in out 
