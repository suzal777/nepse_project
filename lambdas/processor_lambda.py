import json
import boto3
import os
import uuid
from datetime import datetime

s3 = boto3.client("s3")
BUCKET_NAME = os.environ["BUCKET_NAME"]

# Columns we want in processed file
REQUIRED_COLUMNS = ["Symbol", "Open", "High", "Low", "Close", "LTP", "Vol", "Turnover", "Diff %"]
# Fixed indices from raw rows (matches ShareSansar table)
COLUMN_INDICES = [1, 3, 4, 5, 6, 7, 11, 13, 17]

MIN_STOCK_PRICE = 20  # filter threshold for mutual funds

def lambda_handler(event, context):
    correlation_id = str(uuid.uuid4())
    log = {"correlation_id": correlation_id, "event": event}
    print(json.dumps({"level": "INFO", "message": "Processor Lambda started", **log}))

    try:
        # Get S3 object key
        key = event["Records"][0]["s3"]["object"]["key"]
        obj = s3.get_object(Bucket=BUCKET_NAME, Key=key)
        raw_data = json.loads(obj["Body"].read())

        if not isinstance(raw_data, list):
            raise ValueError(f"Raw data must be a list of rows. Got type {type(raw_data)}")

        processed_records = []
        rejected_records = []

        for row in raw_data:
            try:
                # Map fixed indices to required columns
                filtered_row = {col: row[idx] for col, idx in zip(REQUIRED_COLUMNS, COLUMN_INDICES)}

                # Filter out stocks with price < MIN_STOCK_PRICE (mutual funds)
                close_price = float(filtered_row.get("Close", "0") or 0)
                if close_price < MIN_STOCK_PRICE:
                    rejected_records.append({
                        "row": filtered_row,
                        "reason": f"Close price {close_price} < {MIN_STOCK_PRICE} (likely mutual fund)"
                    })
                    continue

                # Convert all numeric values to strings
                for k, v in filtered_row.items():
                    if isinstance(v, (int, float)):
                        filtered_row[k] = str(v)

                processed_records.append(filtered_row)

            except Exception as e:
                rejected_records.append({"row": row, "reason": str(e)})

        # Save processed file in S3
        date_prefix = key.split("/")[1]  # raw/YYYY-MM-DD/
        timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%S")
        processed_key = f"processed/{date_prefix}/data_{timestamp}.json"
        s3.put_object(
            Bucket=BUCKET_NAME,
            Key=processed_key,
            Body=json.dumps(processed_records, indent=2),
            ContentType="application/json"
        )

        # Save rejected rows (including mutual funds) if any
        reject_key = None
        if rejected_records:
            reject_key = f"rejects/{date_prefix}/data_{timestamp}.json"
            s3.put_object(
                Bucket=BUCKET_NAME,
                Key=reject_key,
                Body=json.dumps(rejected_records, indent=2),
                ContentType="application/json"
            )

        # Save metadata for counts
        metadata = {
            "raw_count": len(raw_data),
            "processed_count": len(processed_records),
            "rejected_count": len(rejected_records),
            "processed_file": processed_key,
            "rejected_file": reject_key,
            "correlation_id": correlation_id
        }
        metadata_key = f"metadata/{date_prefix}/data_{timestamp}_meta.json"
        s3.put_object(
            Bucket=BUCKET_NAME,
            Key=metadata_key,
            Body=json.dumps(metadata, indent=2),
            ContentType="application/json"
        )

        print(json.dumps({"level": "INFO", "message": "Processor Lambda completed", **metadata}))
        return metadata

    except Exception as e:
        error_log = {"status": "error", "message": str(e), "correlation_id": correlation_id}
        print(json.dumps({"level": "ERROR", "message": "Processor Lambda failed", **error_log}))
        return error_log
