import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional
import logging
from datetime import datetime

from app.config import settings

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        self.smtp_server = settings.SMTP_SERVER
        self.smtp_port = settings.SMTP_PORT
        self.smtp_username = settings.SMTP_USERNAME
        self.smtp_password = settings.SMTP_PASSWORD
        self.from_email = settings.FROM_EMAIL
    
    # Sends emails to managers
    def send_email(self, to_emails: List[str], subject: str, body: str, html_body: Optional[str] = None) -> bool:
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = ', '.join(to_emails)
            
            # Add plain text version
            text_part = MIMEText(body, 'plain')
            msg.attach(text_part)
            
            # Add HTML version if provided
            if html_body:
                html_part = MIMEText(html_body, 'html')
                msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            print(f"Email sent successfully to {len(to_emails)} recipients")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False
    
    # Format emails, then call send_email
    def send_sale_notification_email(self, to_emails: List[str], expiring_sales: List) -> bool:
        if not expiring_sales:
            return True
        
        subject = f"Sales Notification - {len(expiring_sales)} sales expiring soon"
        
        # Plain text version
        body_lines = [
            "Sales Expiring Soon",
            "=" * 20,
            "",
        ]
        
        # HTML version
        html_lines = [
            "<html><body>",
            "<h2>Sales Expiring Soon</h2>",
            "<table border='1' cellpadding='8' cellspacing='0' style='border-collapse: collapse;'>",
            "<tr style='background-color: #f2f2f2;'>",
            "<th>Product</th><th>Sale Price</th><th>End Date</th><th>Days Remaining</th>",
            "</tr>"
        ]

        for sale in expiring_sales:
            end = sale["sale_end"]
            product_name = sale["product"]["name"]
            price = sale["sale_price"]
            days_left = (end - datetime.now().date()).days
            status = "TODAY" if days_left == 0 else f"{days_left} days"

            # Plain text
            body_lines.append(f'{product_name}: ${price} (ends {status})')

            
            # HTML
            row_color = "#ffebee" if days_left == 0 else "#fff"
            html_lines.append(f"""
                <tr style='background-color: {row_color};'>
                    <td>{product_name}</td>
                    <td>${price}</td>
                    <td>{end}</td>
                    <td><strong>{status}</strong></td>
                </tr>
            """)
        
        body_lines.extend([
            "",
            "Please take action on these sales as needed.",
            "",
            f"Sent at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        ])
        
        html_lines.extend([
            "</table>",
            "<br><p>Please take action on these sales as needed.</p>",
            f"<p><small>Sent at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</small></p>",
            "</body></html>"
        ])
        
        plain_text = "\n".join(body_lines)
        html_text = "\n".join(html_lines)
        
        return self.send_email(to_emails, subject, plain_text, html_text)

# Global instance
email_service = EmailService()