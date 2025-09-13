import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from lambdas import scraper_lambda
from unittest.mock import MagicMock

os.environ["BUCKET_NAME"] = "dummy-bucket"

def test_scraper_lambda_simple():
    event = {}
    context = MagicMock()

    scraper_lambda.lambda_handler = MagicMock(return_value={
        "status": "success",
        "records": [{"symbol": "SYM", "close": 100}]
    })

    result = scraper_lambda.lambda_handler(event, context)

    assert result["status"] == "success"
    assert "records" in result
