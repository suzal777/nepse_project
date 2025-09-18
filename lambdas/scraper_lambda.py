import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime
import boto3
import uuid
import time

s3 = boto3.client("s3")

BUCKET_NAME = os.environ["BUCKET_NAME"]
TARGET_URL = os.environ.get("TARGET_URL", "https://www.sharesansar.com/today-share-price")

MAX_RETRIES = 3
RETRY_DELAY = 2 

def lambda_handler(event, context):
    correlation_id = str(uuid.uuid4())
    print(f"[{correlation_id}] Starting scraper Lambda")

    attempt = 0
    while attempt < MAX_RETRIES:
        try:
            response = requests.get(TARGET_URL, timeout=10)
            response.raise_for_status()
            break
        except requests.RequestException as e:
            attempt += 1
            print(f"[{correlation_id}] Attempt {attempt} failed: {str(e)}")
            if attempt >= MAX_RETRIES:
                return {"status": "error", "message": f"Failed to fetch data after {MAX_RETRIES} attempts"}
            time.sleep(RETRY_DELAY)

    try:
        soup = BeautifulSoup(response.text, "html.parser")
        table = soup.find("table", id="headFixed")
        tbody = table.find("tbody")

        all_rows = []
        for tr in tbody.find_all("tr"):
            row_data = []
            for td in tr.find_all("td"):
                cell_text = td.get_text(strip=True).replace(",", "")
                # Try to convert to float if numeric, else keep as string.
                try:
                    cell_text = float(cell_text)
                except ValueError:
                    pass
                row_data.append(cell_text)
            if row_data:
                all_rows.append(row_data)

        if not all_rows:
            return {"status": "error", "message": "No rows scraped from the table"}

        # Create S3 key with date and timestamp for idempotency
        timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%S")
        key = f"raw/{datetime.utcnow().date()}/data_{timestamp}.json"

        s3.put_object(
            Bucket=BUCKET_NAME,
            Key=key,
            Body=json.dumps(all_rows, indent=2),
            ContentType="application/json"
        )

        print(f"[{correlation_id}] Scraped {len(all_rows)} rows, saved to s3://{BUCKET_NAME}/{key}")
        return {
            "status": "success",
            "file": key,
            "records": len(all_rows),
            "correlation_id": correlation_id
        }

    except Exception as e:
        print(f"[{correlation_id}] Error parsing/saving data: {str(e)}")
        return {"status": "error", "message": str(e), "correlation_id": correlation_id}
