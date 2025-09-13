import pytest
import json
from unittest.mock import patch, MagicMock
from lambdas import processor_lambda

@patch("lambdas.processor_lambda.boto3.client")
def test_processor_lambda_success(mock_boto):
    # Sample raw data
    raw_data = [[None, "SYM", None, 100, 101, 102, 103, 104, None, None, None, 105, None, 106, None, None, 107, None]]
    
    # Mock S3 client
    mock_s3 = MagicMock()
    mock_s3.get_object.return_value = {"Body": MagicMock(read=MagicMock(return_value=json.dumps(raw_data)))}
    mock_boto.return_value = mock_s3

    processor_lambda.BUCKET_NAME = "dummy-bucket"

    event = {"Records":[{"s3":{"object":{"key":"raw/2025-09-13/data.json"}}}]}
    context = {}

    result = processor_lambda.lambda_handler(event, context)

    assert result["processed_count"] > 0
    mock_s3.put_object.assert_called()
