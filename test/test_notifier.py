import sys
import os

# Add repo root to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# --- Set environment variables before importing the Lambda ---
os.environ["SES_EMAIL_FROM"] = "from@example.com"
os.environ["SES_EMAIL_TO"] = "to@example.com"

import pytest
from unittest.mock import patch, MagicMock
from lambdas import notifier_lambda

@patch("lambdas.notifier_lambda.boto3.client")
def test_notifier_lambda_success(mock_boto):
    # Mock SES client
    mock_ses = MagicMock()
    mock_ses.send_email.return_value = {"MessageId": "12345"}
    mock_boto.return_value = mock_ses

    event = {
        "detail": {
            "file_key": "processed/2025-09-13/data.json",
            "correlation_id": "abc-123",
            "market_summary": "Test summary",
            "anomalies": "None",
            "suggestions": "None",
            "raw_count": 1,
            "processed_count": 1,
            "rejected_count": 0
        }
    }
    context = {}

    result = notifier_lambda.lambda_handler(event, context)
    
    assert result["status"] == "success"
    mock_ses.send_email.assert_called_once()
