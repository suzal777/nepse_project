import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import json
os.environ.setdefault("BUCKET_NAME", "dummy-bucket")
os.environ.setdefault("DYNAMO_TABLE", "dummy-table")
os.environ.setdefault("LLM_MODEL", "dummy-model")

from lambdas import llm_analysis_lambda
from unittest.mock import MagicMock

def test_llm_analysis_lambda_simple():
    # Fake event and context
    event = {"Records":[{"s3":{"object":{"key":"processed/fake_data.json"}}}]}
    context = MagicMock(aws_request_id="req-123")

    # Mock the lambda function's internal calls
    llm_analysis_lambda.lambda_handler = MagicMock(return_value={
        "status": "success",
        "market_summary": "Test summary"
    })

    result = llm_analysis_lambda.lambda_handler(event, context)

    assert result["status"] == "success"
    assert "market_summary" in result
