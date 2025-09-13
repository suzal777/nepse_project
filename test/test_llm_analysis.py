import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "lambdas"))
import pytest
import json
from unittest.mock import patch, MagicMock
from lambdas import llm_analysis_lambda

@patch("lambdas.llm_analysis_lambda.boto3.client")
@patch("lambdas.llm_analysis_lambda.boto3.resource")
def test_llm_analysis_lambda_success(mock_resource, mock_client):
    # Mock S3 get_object
    mock_s3 = MagicMock()
    processed_data = [{"Symbol": "SYM", "Close": "100"}]
    metadata = {"raw_count": 1, "processed_count": 1, "rejected_count": 0}
    mock_s3.get_object.side_effect = [
        {"Body": MagicMock(read=MagicMock(return_value=json.dumps(processed_data)))},
        {"Body": MagicMock(read=MagicMock(return_value=json.dumps(metadata)))}
    ]
    
    # Mock Bedrock client
    mock_bedrock = MagicMock()
    mock_bedrock.invoke_model.return_value = {"body": MagicMock(read=lambda: json.dumps({"output":{"message":{"content":[{"text":"MARKET SUMMARY\nTest\nANOMALIES\nNone\nSUGGESTIONS\nNone"}]}}}).encode())}
    
    # Mock EventBridge
    mock_events = MagicMock()
    
    mock_client.side_effect = lambda service_name, **kwargs: {
        "s3": mock_s3,
        "bedrock-runtime": mock_bedrock,
        "events": mock_events
    }[service_name]
    
    # Mock DynamoDB
    mock_table = MagicMock()
    mock_dynamodb = MagicMock()
    mock_dynamodb.Table.return_value = mock_table
    mock_resource.return_value = mock_dynamodb

    # Set environment variables
    llm_analysis_lambda.BUCKET_NAME = "dummy-bucket"
    llm_analysis_lambda.DYNAMO_TABLE = "dummy-table"
    llm_analysis_lambda.LLM_MODEL = "dummy-model"

    event = {"Records":[{"s3":{"object":{"key":"processed/2025-09-13/data.json"}}}]}
    context = MagicMock(aws_request_id="req-123")

    result = llm_analysis_lambda.lambda_handler(event, context)
    
    assert result["status"] == "success"
    assert "market_summary" in result
