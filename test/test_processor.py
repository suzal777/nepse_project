import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from lambdas import processor_lambda
from unittest.mock import MagicMock

os.environ["BUCKET_NAME"] = "dummy-bucket"

def test_processor_lambda_simple():
    event = {"Records":[{"s3":{"object":{"key":"raw/fake_data.json"}}}]}
    context = MagicMock()

    processor_lambda.lambda_handler = MagicMock(return_value={
        "processed_count": 1,
        "rejected_count": 0
    })

    result = processor_lambda.lambda_handler(event, context)

    assert result["processed_count"] > 0
