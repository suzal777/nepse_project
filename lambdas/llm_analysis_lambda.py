import json
import boto3
import os
import re
from decimal import Decimal
import uuid

s3 = boto3.client("s3")
dynamodb = boto3.resource("dynamodb")
bedrock = boto3.client("bedrock-runtime")
events = boto3.client("events")

BUCKET_NAME = os.environ["BUCKET_NAME"]
DYNAMO_TABLE = os.environ["DYNAMO_TABLE"]
LLM_MODEL = os.environ.get("LLM_MODEL", "amazon.nova-lite-v1:0")
ALERT_EVENT_BUS = os.environ.get("ALERT_EVENT_BUS")

def _convert_numeric_to_decimal(obj):
    if isinstance(obj, list):
        return [_convert_numeric_to_decimal(x) for x in obj]
    elif isinstance(obj, dict):
        return {k: _convert_numeric_to_decimal(v) for k, v in obj.items()}
    elif isinstance(obj, float) or isinstance(obj, int):
        return Decimal(str(obj))
    return obj

def _send_event_to_bus(event_bus_name, detail):
    if not event_bus_name:
        return
    entry = {
        "Source": "llm_analysis",
        "DetailType": "AnomalyDetected",
        "Detail": json.dumps(detail),
        "EventBusName": event_bus_name
    }
    resp = events.put_events(Entries=[entry])
    print("EventBridge response:", resp)
    return resp

def lambda_handler(event, context):
    correlation_id = str(uuid.uuid4())
    try:
        key = event["Records"][0]["s3"]["object"]["key"]
        print(json.dumps({"level": "INFO", "message": "Fetching processed file", "file": key, "correlation_id": correlation_id}))

        obj = s3.get_object(Bucket=BUCKET_NAME, Key=key)
        processed_data = json.loads(obj["Body"].read())
        if not isinstance(processed_data, list):
            raise ValueError("Processed data must be a list.")

        # --- Derive metadata key ---
        if key.startswith("processed/") and key.endswith(".json"):
            date_prefix = key.split("/")[1]       
            filename = key.split("/")[-1]         
            base = filename.replace(".json", "")  
            metadata_key = f"metadata/{date_prefix}/{base}_meta.json"
        else:
            raise ValueError(f"Unexpected processed key format: {key}")

        # --- Load metadata ---
        metadata_obj = s3.get_object(Bucket=BUCKET_NAME, Key=metadata_key)
        metadata = json.loads(metadata_obj["Body"].read())
        raw_count = metadata.get("raw_count", len(processed_data))
        processed_count = metadata.get("processed_count", len(processed_data))
        rejected_count = metadata.get("rejected_count", 0)    

        # LLM Prompt
        prompt = f"""
You are a financial market analyst. You are given daily stock market data in JSON format.

Perform structured analysis with these sections only:

1. MARKET SUMMARY - concise narrative of today's market (sentiment, key movers, trend)
2. ANOMALIES - unusual trading patterns, bullet points: Symbol, Turnover, Price Change, Reason
3. SUGGESTIONS - 2-3 actionable suggestions (Opportunities & Risks)

Return as plain text, starting each section with its heading in uppercase.

Example output format (Return output in exact same structure as below):

MARKET SUMMARY
Today's market showed a mixture of strength and weakness. 
The overall sentiment was cautious as many stocks experienced losses despite brief periods of growth. 
Key movers included "ANLB," which saw a substantial increase despite the general downturn. 
"BHPC," "ALBSL," and "HIDCL" also showed positive growth, while several others like "BHCL," "BHPL," and "BKBL" faced significant drops.

ANOMALIES
Symbol: ANLB, Turnover: 7069763.5, Price Change: 2.47%, Reason: ANLB experienced an unusual price increase, significantly outperforming the market. 
Symbol: GWFD83, Turnover: 294775.0, Price Change: -1.42%, Reason: Stable price movement with low turnover and low trading volume.
Symbol: HIDCLP, Turnover: 46114891.5, Price Change: -1.94%, Reason: High trading volume and turnover, indicating unusual demand but closing below the opening.
Symbol: NLCD86, Turnover: 1477160.0, Price Change: 4.35%, Reason: Sudden and unexplainable significant price increase, with limited trading volume.

SUGGESTIONS
Opportunity: Stocks like ANLB and GWFD83 displayed unusual price movements. Investors might want to closely watch these for potential growth or upcoming news.
Opportunity: Stocks such as ADBSL and NCCD86 showed gains despite market volatility. Keeping a close watch on these for sustained performance.
Risk: Highly volatile stocks like GHL and PPCL reported decreased end value. These might be riskier investments in current conditions.
Risk: Stocks with significant drops, including BHPC and ALBSL, may stabilize, but caution is advised as they are likely to remain unstable.

Here is the market data:
{json.dumps(processed_data, indent=2)}
"""

        body = {
            "messages": [{"role": "user", "content": [{"text": prompt}]}],
            "inferenceConfig": {"maxTokens": 800, "temperature": 0.0, "topP": 1}
        }

        response = bedrock.invoke_model(
            modelId=LLM_MODEL,
            contentType="application/json",
            accept="application/json",
            body=json.dumps(body)
        )

        raw = response["body"].read()
        parsed = json.loads(raw)
        analysis_text = (
            parsed.get("output", {}).get("message", {}).get("content", [{}])[0].get("text", "")
        )
        if not analysis_text:
            analysis_text = "No analysis generated."

        # Extract sections
        def extract_section(name, text):
            pattern = rf"(?i){name}\s*(.*?)(?=\n[A-Z ]+\n|$)"
            match = re.search(pattern, text, re.DOTALL)
            return match.group(1).strip() if match else ""

        market_summary = extract_section("MARKET SUMMARY", analysis_text)
        anomalies = extract_section("ANOMALIES", analysis_text)
        suggestions = extract_section("SUGGESTIONS", analysis_text)

        # Save structured output to DynamoDB
        table = dynamodb.Table(DYNAMO_TABLE)
        table.put_item(Item=_convert_numeric_to_decimal({
            "file_key": key,
            "market_summary": market_summary,
            "anomalies": anomalies,
            "suggestions": suggestions,
            "timestamp": context.aws_request_id,
            "correlation_id": correlation_id
        }))

        print(json.dumps({"level": "INFO", "message": "Analysis saved to DynamoDB", "correlation_id": correlation_id}))

        # Trigger EventBridge if anomalies exist
        if anomalies:
            _send_event_to_bus(ALERT_EVENT_BUS, {
                "file_key": key,
                "market_summary": market_summary,
                "anomalies": anomalies,
                "suggestions": suggestions,
                "raw_count": raw_count,
                "processed_count": processed_count,
                "rejected_count": rejected_count,
                "correlation_id": correlation_id
            })

        return {
            "status": "success",
            "market_summary": market_summary,
            "anomalies": anomalies,
            "suggestions": suggestions,
            "raw_count": raw_count,
            "processed_count": processed_count,
            "rejected_count": rejected_count,
            "correlation_id": correlation_id
        }

    except Exception as e:
        print(json.dumps({"level": "ERROR", "message": str(e), "correlation_id": correlation_id}))
        return {"status": "error", "message": str(e), "correlation_id": correlation_id}
