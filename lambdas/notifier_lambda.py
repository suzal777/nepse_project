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

        # ---- Row Counts Card ----
        html_counts = f"""
        <div style='border:1px solid #34495E; border-radius:8px; background:#F4F6F7; padding:15px; width:300px; display:inline-block; vertical-align:top; box-shadow:2px 2px 8px rgba(0,0,0,0.1); margin-right:10px;'>
            <h3 style='color:#34495E; margin-top:0;'>Row Counts</h3>
            <table style='border-collapse: collapse; width:100%; text-align:left;'>
                <tr style='background:#D5DBDB;'>
                    <th style='border:1px solid #ddd; padding:5px;'>Raw</th>
                    <th style='border:1px solid #ddd; padding:5px;'>Processed</th>
                    <th style='border:1px solid #ddd; padding:5px;'>Rejected</th>
                </tr>
                <tr>
                    <td style='border:1px solid #ddd; padding:5px;'>{raw_count}</td>
                    <td style='border:1px solid #ddd; padding:5px;'>{processed_count}</td>
                    <td style='border:1px solid #ddd; padding:5px;'>{rejected_count}</td>
                </tr>
            </table>
        </div>
        """

        # ---- Market Summary Card ----
        market_summary_html = html.escape(market_summary).replace("\n", "<br>") if market_summary else "No market summary available."
        html_market_summary = f"""
        <div style='border:1px solid #2E86C1; border-radius:8px; background:#EAF2F8; padding:15px; width:600px; display:inline-block; vertical-align:top; box-shadow:2px 2px 8px rgba(0,0,0,0.1);'>
            <h3 style='color:#2E86C1; margin-top:0;'>Market Summary</h3>
            <p>{market_summary_html}</p>
        </div>
        """

        # ---- Anomalies Card ----
        if anomalies_str:
            anomaly_lines = [line.strip() for line in anomalies_str.splitlines() if line.strip()]
            anomalies_html = "<table style='border-collapse: collapse; width:100%; margin-bottom:10px;'>"
            anomalies_html += """
            <tr style='background:#FDEBD0;'>
                <th style='border:1px solid #ddd; padding:5px; text-align:left;'>Symbol</th>
                <th style='border:1px solid #ddd; padding:5px; text-align:left;'>Turnover</th>
                <th style='border:1px solid #ddd; padding:5px; text-align:left;'>Price Change</th>
                <th style='border:1px solid #ddd; padding:5px; text-align:left;'>Reason</th>
            </tr>
            """
            for idx, line in enumerate(anomaly_lines):
                parts = dict(part.strip().split(":", 1) for part in line.split(",") if ":" in part)
                price_change = parts.get('Price Change', '').strip()
                price_color = 'green' if price_change.startswith('+') else 'red' if price_change.startswith('-') else 'black'
                row_bg = '#FFF8E1' if idx % 2 == 0 else '#FEF9E7'
                anomalies_html += f"""
                <tr style='background:{row_bg};'>
                    <td style='border:1px solid #ddd; padding:5px;'>{html.escape(parts.get('Symbol',''))}</td>
                    <td style='border:1px solid #ddd; padding:5px;'>{html.escape(parts.get('Turnover',''))}</td>
                    <td style='border:1px solid #ddd; padding:5px; color:{price_color}; font-weight:bold;'>{html.escape(price_change)}</td>
                    <td style='border:1px solid #ddd; padding:5px;'>{html.escape(parts.get('Reason',''))}</td>
                </tr>
                """
            anomalies_html += "</table>"
            html_anomalies = f"""
            <div style='border:1px solid #F1C40F; border-radius:8px; background:#FEF9E7; padding:15px; margin-bottom:15px; box-shadow:2px 2px 8px rgba(0,0,0,0.1);'>
                <h3 style='color:#B9770E; margin-top:0;'>Anomalies</h3>
                {anomalies_html}
            </div>
            """
        else:
            html_anomalies = """
            <div style='border:1px solid #F1C40F; border-radius:8px; background:#FEF9E7; padding:15px; margin-bottom:15px; box-shadow:2px 2px 8px rgba(0,0,0,0.1);'>
                <h3 style='color:#B9770E; margin-top:0;'>Anomalies</h3>
                <p>No anomalies detected.</p>
            </div>
            """

        # ---- Suggestions Cards ----
        opportunity_html = ""
        risk_html = ""
        if suggestions_str:
            for line in [l.strip() for l in suggestions_str.splitlines() if l.strip()]:
                if line.lower().startswith("opportunity"):
                    opportunity_html += f"<li>{html.escape(line)}</li>"
                elif line.lower().startswith("risk"):
                    risk_html += f"<li>{html.escape(line)}</li>"

        if opportunity_html:
            opportunity_html = f"""
            <div style='border:1px solid #27AE60; border-radius:8px; background:#E9F7EF; padding:15px; margin-bottom:10px; box-shadow:2px 2px 8px rgba(0,0,0,0.1);'>
                <h3 style='color:#27AE60; margin-top:0;'>Opportunities</h3>
                <ul style='padding-left:15px;'>{opportunity_html}</ul>
            </div>
            """
        if risk_html:
            risk_html = f"""
            <div style='border:1px solid #C0392B; border-radius:8px; background:#FDEDEC; padding:15px; margin-bottom:10px; box-shadow:2px 2px 8px rgba(0,0,0,0.1);'>
                <h3 style='color:#C0392B; margin-top:0;'>Risks</h3>
                <ul style='padding-left:15px;'>{risk_html}</ul>
            </div>
            """

        if not opportunity_html and not risk_html:
            suggestions_html = """
            <div style='border:1px solid #27AE60; border-radius:8px; background:#F9F9F9; padding:15px; margin-bottom:15px; box-shadow:2px 2px 8px rgba(0,0,0,0.1);'>
                <h3 style='color:#27AE60; margin-top:0;'>Suggestions</h3>
                <p>No suggestions available.</p>
            </div>
            """
        else:
            suggestions_html = opportunity_html + risk_html

        # ---- Final HTML Body ----
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height:1.5; color:#333; padding:20px; background:#F5F5F5;">
            <h1 style="color:#34495E; text-align:center;">Daily Market Report</h1>
            <div style='margin-bottom:15px;'>
                <p><strong>File Key:</strong> {html.escape(file_key)}</p>
                <p><strong>Correlation ID:</strong> {html.escape(correlation_id)}</p>
            </div>
            <div style="display:flex; gap:15px; flex-wrap:wrap;">
                {html_counts}
                {html_market_summary}
            </div>
            {html_anomalies}
            {suggestions_html}
        </body>
        </html>
        """

        subject = f"Daily Market Report - {file_key}"

        response = ses.send_email(
            Source
