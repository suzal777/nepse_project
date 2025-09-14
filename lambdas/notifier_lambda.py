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

        # ---- Processing Summary Card ----
        html_counts = f"""
        <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius:16px; padding:24px; margin-bottom:24px; box-shadow: 0 8px 32px rgba(0,0,0,0.12); font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;'>
            <h2 style='color: #fff; font-size: 20px; font-weight: 600; margin: 0 0 20px 0; letter-spacing: -0.5px;'>Processing Summary</h2>
            <div style='display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 16px;'>
                <div style='background: rgba(255,255,255,0.15); backdrop-filter: blur(10px); border-radius: 12px; padding: 16px; border: 1px solid rgba(255,255,255,0.2);'>
                    <div style='color: rgba(255,255,255,0.8); font-size: 12px; font-weight: 500; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px;'>Raw Data</div>
                    <div style='color: #fff; font-size: 24px; font-weight: 700;'>{raw_count}</div>
                </div>
                <div style='background: rgba(255,255,255,0.15); backdrop-filter: blur(10px); border-radius: 12px; padding: 16px; border: 1px solid rgba(255,255,255,0.2);'>
                    <div style='color: rgba(255,255,255,0.8); font-size: 12px; font-weight: 500; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px;'>Processed</div>
                    <div style='color: #fff; font-size: 24px; font-weight: 700;'>{processed_count}</div>
                </div>
                <div style='background: rgba(255,255,255,0.15); backdrop-filter: blur(10px); border-radius: 12px; padding: 16px; border: 1px solid rgba(255,255,255,0.2);'>
                    <div style='color: rgba(255,255,255,0.8); font-size: 12px; font-weight: 500; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px;'>Rejected</div>
                    <div style='color: #fff; font-size: 24px; font-weight: 700;'>{rejected_count}</div>
                </div>
            </div>
        </div>
        """

        # ---- Market Summary Card ----
        market_summary_html = html.escape(market_summary).replace("\n", "<br>") if market_summary else "No market summary available."
        html_market_summary = f"""
        <div style='background: #fff; border-radius: 16px; padding: 28px; margin-bottom: 24px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); border: 1px solid rgba(0,0,0,0.05); font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;'>
            <h2 style='color: #1F2937; font-size: 24px; font-weight: 700; margin: 0 0 20px 0; letter-spacing: -0.5px;'>Market Overview</h2>
            <div style='color: #4B5563; font-size: 16px; line-height: 1.7; background: #F9FAFB; padding: 20px; border-radius: 12px; border-left: 4px solid #4F46E5;'>
                {market_summary_html}
            </div>
        </div>
        """

        # ---- Anomalies Card ----
        if anomalies_str:
            anomaly_lines = [line.strip() for line in anomalies_str.splitlines() if line.strip()]
            anomalies_html = """
            <div style='overflow-x: auto;'>
                <table style='border-collapse: collapse; width: 100%; min-width: 600px; background: #fff; border-radius: 12px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1);'>
                    <thead>
                        <tr style='background: linear-gradient(135deg, #F59E0B, #F97316);'>
                            <th style='padding: 16px 20px; text-align: left; color: #fff; font-weight: 600; font-size: 14px; text-transform: uppercase; letter-spacing: 0.5px;'>Symbol</th>
                            <th style='padding: 16px 20px; text-align: left; color: #fff; font-weight: 600; font-size: 14px; text-transform: uppercase; letter-spacing: 0.5px;'>Turnover</th>
                            <th style='padding: 16px 20px; text-align: left; color: #fff; font-weight: 600; font-size: 14px; text-transform: uppercase; letter-spacing: 0.5px;'>Price Change</th>
                            <th style='padding: 16px 20px; text-align: left; color: #fff; font-weight: 600; font-size: 14px; text-transform: uppercase; letter-spacing: 0.5px;'>Reason</th>
                        </tr>
                    </thead>
                    <tbody>
            """
            
            for idx, line in enumerate(anomaly_lines):
                parts = dict(part.strip().split(":", 1) for part in line.split(",") if ":" in part)
                price_change = parts.get('Price Change', '').strip()
                
                if price_change.startswith('+'):
                    price_color = '#10B981'
                    price_bg = '#ECFDF5'
                elif price_change.startswith('-'):
                    price_color = '#EF4444'
                    price_bg = '#FEF2F2'
                else:
                    price_color = '#10B981'
                    price_bg = '#ECFDF5'
                
                row_bg = '#FFFFFF' if idx % 2 == 0 else '#F9FAFB'
                
                anomalies_html += f"""
                    <tr style='background: {row_bg};'>
                        <td style='padding: 16px 20px; border-bottom: 1px solid #E5E7EB; font-weight: 600; color: #1F2937;'>{html.escape(parts.get('Symbol',''))}</td>
                        <td style='padding: 16px 20px; border-bottom: 1px solid #E5E7EB; color: #4B5563; font-family: monospace;'>{html.escape(parts.get('Turnover',''))}</td>
                        <td style='padding: 16px 20px; border-bottom: 1px solid #E5E7EB;'>
                            <span style='background: {price_bg}; color: {price_color}; padding: 6px 12px; border-radius: 20px; font-weight: 600; font-size: 14px; font-family: monospace;'>
                                {html.escape(price_change)}
                            </span>
                        </td>
                        <td style='padding: 16px 20px; border-bottom: 1px solid #E5E7EB; color: #4B5563;'>{html.escape(parts.get('Reason',''))}</td>
                    </tr>
                """
            
            anomalies_html += """
                    </tbody>
                </table>
            </div>
            """
            
            html_anomalies = f"""
            <div style='background: #fff; border-radius: 16px; padding: 28px; margin-bottom: 24px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); border: 1px solid rgba(0,0,0,0.05); font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;'>
                <h2 style='color: #1F2937; font-size: 24px; font-weight: 700; margin: 0 0 24px 0; letter-spacing: -0.5px;'>Market Anomalies</h2>
                {anomalies_html}
            </div>
            """
        else:
            html_anomalies = """
            <div style='background: #fff; border-radius: 16px; padding: 28px; margin-bottom: 24px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); border: 1px solid rgba(0,0,0,0.05); font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;'>
                <h2 style='color: #1F2937; font-size: 24px; font-weight: 700; margin: 0 0 20px 0; letter-spacing: -0.5px;'>Market Anomalies</h2>
                <div style='background: #F0FDF4; padding: 20px; border-radius: 12px; border-left: 4px solid #10B981; color: #15803D; font-size: 16px; text-align: center;'>
                    No anomalies detected - Market operating normally
                </div>
            </div>
            """

        # ---- Suggestions Cards ----
        opportunity_html = ""
        risk_html = ""
        if suggestions_str:
            for line in [l.strip() for l in suggestions_str.splitlines() if l.strip()]:
                if line.lower().startswith("opportunity"):
                    opportunity_html += f"""
                    <div style='background: #F0FDF4; border: 1px solid #BBF7D0; border-radius: 12px; padding: 16px; margin-bottom: 12px;'>
                        <div style='color: #15803D; font-size: 15px; line-height: 1.5;'>{html.escape(line)}</div>
                    </div>
                    """
                elif line.lower().startswith("risk"):
                    risk_html += f"""
                    <div style='background: #FEF2F2; border: 1px solid #FECACA; border-radius: 12px; padding: 16px; margin-bottom: 12px;'>
                        <div style='color: #B91C1C; font-size: 15px; line-height: 1.5;'>{html.escape(line)}</div>
                    </div>
                    """

        suggestions_html = ""
        if opportunity_html:
            suggestions_html += f"""
            <div style='background: #fff; border-radius: 16px; padding: 28px; margin-bottom: 24px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); border: 1px solid rgba(0,0,0,0.05); font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;'>
                <h2 style='color: #1F2937; font-size: 24px; font-weight: 700; margin: 0 0 24px 0; letter-spacing: -0.5px;'>Opportunities</h2>
                {opportunity_html}
            </div>
            """
        
        if risk_html:
            suggestions_html += f"""
            <div style='background: #fff; border-radius: 16px; padding: 28px; margin-bottom: 24px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); border: 1px solid rgba(0,0,0,0.05); font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;'>
                <h2 style='color: #1F2937; font-size: 24px; font-weight: 700; margin: 0 0 24px 0; letter-spacing: -0.5px;'>Risk Alerts</h2>
                {risk_html}
            </div>
            """

        if not opportunity_html and not risk_html:
            suggestions_html = """
            <div style='background: #fff; border-radius: 16px; padding: 28px; margin-bottom: 24px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); border: 1px solid rgba(0,0,0,0.05); font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;'>
                <h2 style='color: #1F2937; font-size: 24px; font-weight: 700; margin: 0 0 20px 0; letter-spacing: -0.5px;'>Insights</h2>
                <div style='background: #F9FAFB; padding: 20px; border-radius: 12px; color: #6B7280; font-size: 16px; text-align: center;'>
                    No specific suggestions available at this time
                </div>
            </div>
            """

        # ---- Responsive HTML Body ----
        html_body = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Daily Market Report</title>
            <style>
                @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
                
                * {{
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }}
                
                body {{
                    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    line-height: 1.6;
                    color: #1F2937;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                    padding: 20px;
                }}
                
                @media (min-width: 768px) {{
                    body {{
                        padding: 40px 20px;
                    }}
                }}
                
                .container {{
                    max-width: 1000px;
                    margin: 0 auto;
                    background: #F8FAFC;
                    border-radius: 16px;
                    padding: 20px;
                    box-shadow: 0 20px 50px rgba(0,0,0,0.15);
                }}
                
                @media (min-width: 768px) {{
                    .container {{
                        border-radius: 24px;
                        padding: 40px;
                    }}
                }}
                
                .header {{
                    text-align: center;
                    margin-bottom: 30px;
                    padding-bottom: 20px;
                    border-bottom: 1px solid #E5E7EB;
                }}
                
                @media (min-width: 768px) {{
                    .header {{
                        margin-bottom: 40px;
                        padding-bottom: 30px;
                    }}
                }}
                
                .header h1 {{
                    font-size: 28px;
                    font-weight: 800;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                    background-clip: text;
                    margin-bottom: 8px;
                    letter-spacing: -1px;
                }}
                
                @media (min-width: 768px) {{
                    .header h1 {{
                        font-size: 36px;
                        margin-bottom: 12px;
                    }}
                }}
                
                .metadata {{
                    background: #fff;
                    border-radius: 12px;
                    padding: 16px;
                    margin-bottom: 24px;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
                    border: 1px solid rgba(0,0,0,0.05);
                }}
                
                @media (min-width: 768px) {{
                    .metadata {{
                        padding: 20px;
                    }}
                }}
                
                .metadata-item {{
                    display: flex;
                    flex-direction: column;
                    gap: 8px;
                    padding: 8px 0;
                    border-bottom: 1px solid #F3F4F6;
                }}
                
                @media (min-width: 768px) {{
                    .metadata-item {{
                        flex-direction: row;
                        justify-content: space-between;
                        align-items: center;
                        gap: 0;
                    }}
                }}
                
                .metadata-item:last-child {{
                    border-bottom: none;
                }}
                
                .metadata-label {{
                    font-weight: 600;
                    color: #4B5563;
                    font-size: 14px;
                }}
                
                .metadata-value {{
                    font-family: monospace;
                    color: #1F2937;
                    background: #F9FAFB;
                    padding: 4px 8px;
                    border-radius: 6px;
                    font-size: 13px;
                    word-break: break-all;
                }}
                
                @media (min-width: 768px) {{
                    .metadata-value {{
                        word-break: normal;
                    }}
                }}
                
                /* Mobile-friendly table styles */
                @media (max-width: 767px) {{
                    table {{
                        font-size: 14px;
                    }}
                    
                    th, td {{
                        padding: 12px 8px !important;
                    }}
                    
                    .metadata-value {{
                        font-size: 12px;
                    }}
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Daily Market Report</h1>
                    <p style="color: #6B7280; font-size: 14px; margin: 0;">Comprehensive market analysis and insights</p>
                </div>
                
                <div class="metadata">
                    <div class="metadata-item">
                        <span class="metadata-label">File Reference</span>
                        <span class="metadata-value">{html.escape(file_key)}</span>
                    </div>
                    <div class="metadata-item">
                        <span class="metadata-label">Correlation ID</span>
                        <span class="metadata-value">{html.escape(correlation_id)}</span>
                    </div>
                </div>
                
                {html_counts}
                {html_market_summary}
                {html_anomalies}
                {suggestions_html}
            </div>
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