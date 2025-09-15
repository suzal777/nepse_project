import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from lambdas import notifier_lambda
from unittest.mock import MagicMock

os.environ["SES_EMAIL_FROM"] = "from@example.com"
os.environ["SES_EMAIL_TO"] = "to@example.com"

def test_notifier_lambda_simple():
    event = {"detail": {"market_summary": "Test"}}
    context = MagicMock()

    notifier_lambda.lambda_handler = MagicMock(return_value={
        "status": "success"
    })

    result = notifier_lambda.lambda_handler(event, context)

    assert result["status"] == "success"

# test1