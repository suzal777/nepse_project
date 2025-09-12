import boto3
import os
import html

ses = boto3.client("ses")

def lambda_handler(event, context):
    try:
        print("Received event:", event)

        email_from = os.environ["SES_EMAIL_FROM"]
        email_to = os.environ["SES_EMAIL_TO"]

        file_key = event['detail'].get('file_key', 'N/A')
        correlation_id = event['detail'].get('correlation_id', 'N/A')

        # ---- Extract values from event ----
        market_summary = event['detail'].get('market_summary', '')
        anomalies_str = event['detail'].get('anomalies', '')
        suggestions_str = event['detail'].get('suggestions', '')

        # ---- Extract row counts ----
        raw_count = event['detail'].get('raw_count', 'N/A')
        processed_count = event['detail'].get('processed_count', 'N/A')
        rejected_count = event['detail'].get('rejected_count', 'N/A')

        # ---- Market Summary ----
        market_summary_html = html.escape(market_summary).replace("\n", "<br>") if market_summary else "No market summary available."
        html_market_summary = f"<h2 style='color:#2E86C1;'>Market Summary</h2><p>{market_summary_html}</p>"

        # ---- Row Counts ----
        html_counts = f"""
        <h2 style='color:#34495E;'>Row Counts</h2>
        <ul>
            <li>Raw Rows: {raw_count}</li>
            <li>Processed Rows: {processed_count}</li>
            <li>Rejected Rows: {rejected_count}</li>
        </ul>
        """

        # ---- Anomalies ----
        if anomalies_str:
            anomaly_lines = [line.strip() for line in anomalies_str.splitlines() if line.strip()]
            anomalies_html = "<ul>"
            for line in anomaly_lines:
                anomalies_html += f"<li>{html.escape(line)}</li>"
            anomalies_html += "</ul>"
            html_anomalies = f"<h2 style='color:#C0392B;'>Anomalies</h2>{anomalies_html}"
        else:
            html_anomalies = "<h2 style='color:#C0392B;'>Anomalies</h2><p>No anomalies detected.</p>"

        # ---- Suggestions ----
        if suggestions_str:
            suggestion_lines = [line.strip() for line in suggestions_str.splitlines() if line.strip()]
            suggestions_html = "<ul>"
            for line in suggestion_lines:
                suggestions_html += f"<li>{html.escape(line)}</li>"
            suggestions_html += "</ul>"
            html_suggestions = f"<h2 style='color:#27AE60;'>Suggestions</h2>{suggestions_html}"
        else:
            html_suggestions = "<h2 style='color:#27AE60;'>Suggestions</h2><p>No suggestions available.</p>"

        # ---- Final HTML Body ----
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height:1.5; color:#333;">
            <h1 style="color:#34495E;">Daily Market Report</h1>
            <p><strong>File Key:</strong> {html.escape(file_key)}</p>
            <p><strong>Correlation ID:</strong> {html.escape(correlation_id)}</p>
            {html_counts}
            {html_market_summary}
            {html_anomalies}
            {html_suggestions}
        </body>
        </html>
        """

        subject = f"Daily Market Report - {file_key}"

        response = ses.send_email(
            Source=email_from,
            Destination={"ToAddresses": [email_to]},
            Message={
                "Subject": {"Data": subject},
                "Body": {"Html": {"Data": html_body}}
            }
        )

        print("SES Response:", response)
        return {"status": "success", "message_id": response["MessageId"]}

    except Exception as e:
        print("Error sending SES email:", str(e))
        return {"status": "error", "message": str(e)}
