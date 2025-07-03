import pytest
from unittest.mock import patch, MagicMock
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ai import analyze_txt_content, generate_data_hash

# Mock data for hash test
mock_profile = {
    "annual_income": "1200000",
    "monthly_budget": "12000",
    "occupation": "Engineer",
    "age": 25,
    "location": "Chennai",
    "financial_goal": "Save 1 Cr"
}
mock_expenses = [
    {"name": "Groceries", "amount": 3000, "date": "2025-06-01", "desc": "Food"},
    {"name": "Rent", "amount": 8000, "date": "2025-06-02", "desc": "Housing"}
]

def test_generate_data_hash_consistency():
    hash1 = generate_data_hash(mock_profile, mock_expenses)
    hash2 = generate_data_hash(mock_profile, mock_expenses)
    assert hash1 == hash2
    assert isinstance(hash1, str)
    assert len(hash1) == 64  # SHA256 hash length

@patch("ai.client.chat.completions.create")
def test_analyze_txt_content_success(mock_create):
    # Set up mock response
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content="✅ Mocked analysis result"))]
    mock_create.return_value = mock_response

    text = "Income: ₹1200000, Budget: ₹12000, Goal: Save 1 Cr"
    result = analyze_txt_content(text)
    
    assert "✅" in result
    mock_create.assert_called_once()

@patch("ai.client.chat.completions.create")
def test_analyze_txt_content_no_valid_response(mock_create):
    # Simulate no valid content in AI response
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=None)]  # No message
    mock_create.return_value = mock_response

    result = analyze_txt_content("test input without valid message")
    
    assert result == "❌ AI Error: No valid response received from model."
    mock_create.assert_called_once()

@patch("ai.client.chat.completions.create")
def test_analyze_txt_content_error(mock_create):
    mock_create.side_effect = Exception("Simulated failure")
    result = analyze_txt_content("test")
    
    assert result.startswith("❌ AI Error")
