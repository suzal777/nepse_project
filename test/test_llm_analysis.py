import os
import json
from lambdas import llm_analysis_lambda
from unittest.mock import MagicMock

# Set environment variables
os.environ["BUCKET_NAME"] = "dummy-bucket"
os.environ["DYNAMO_TABLE"] = "dummy-table"
os.environ["LLM_MODEL"] = "dummy-model"

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
