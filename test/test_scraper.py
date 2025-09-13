import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import pytest
from unittest.mock import patch, MagicMock

# Set environment variable before importing Lambda
os.environ["BUCKET_NAME"] = "dummy-bucket"

# Patch boto3.client and requests.get before importing Lambda
with patch("lambdas.scraper_lambda.boto3.client") as mock_boto, \
     patch("lambdas.scraper_lambda.requests.get") as mock_get:

    from lambdas import scraper_lambda

    # Mock HTTP response
    mock_response = MagicMock()
    mock_response.text = """
    <table id="headFixed"><tbody>
    <tr><td>1</td><td>SYM</td><td>100</td></tr>
    </tbody></table>
    """
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    # Mock S3 client
    mock_s3 = MagicMock()
    mock_boto.return_value = mock_s3

    def test_scraper_lambda_success():
        event = {}
        context = {}
        result = scraper_lambda.lambda_handler(event, context)

        assert result["status"] == "success"
        assert "records" in result
        mock_s3.put_object.assert_called_once()
