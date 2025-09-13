import pytest
import json
from unittest.mock import patch, MagicMock
from lambdas import scraper_lambda

@patch("lambdas.scraper_lambda.boto3.client")
@patch("lambdas.scraper_lambda.requests.get")
def test_scraper_lambda_success(mock_get, mock_boto):
    # Mock HTTP response
    mock_response = MagicMock()
    mock_response.text = """
    <table id="headFixed"><tbody>
    <tr><td>1</td><td>Symbol</td><td>100</td></tr>
    </tbody></table>
    """
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    # Mock S3 client
    mock_s3 = MagicMock()
    mock_boto.return_value = mock_s3

    # Set environment variable
    scraper_lambda.BUCKET_NAME = "dummy-bucket"

    event = {}
    context = {}
    result = scraper_lambda.lambda_handler(event, context)

    assert result["status"] == "success"
    assert "records" in result
    mock_s3.put_object.assert_called_once()
