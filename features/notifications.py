"""Sale and low-inventory notifications via email."""
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, List


class SaleNotifier:
    """Send email notifications for sales, low inventory, etc."""
    
    def __init__(
        self,
        smtp_host: Optional[str] = None,
        smtp_port: int = 587,
        smtp_user: Optional[str] = None,
        smtp_password: Optional[str] = None,
        from_email: Optional[str] = None
    ):
        self.smtp_host = smtp_host or os.environ.get('SMTP_HOST', 'smtp.gmail.com')
        self.smtp_port = smtp_port or int(os.environ.get('SMTP_PORT', '587'))
        self.smtp_user = smtp_user or os.environ.get('SMTP_USER')
        self.smtp_password = smtp_password or os.environ.get('SMTP_PASSWORD')
        self.from_email = from_email or os.environ.get('NOTIFY_FROM_EMAIL') or self.smtp_user
    
    def is_configured(self) -> bool:
        return bool(self.smtp_user and self.smtp_password and self.from_email)
    
    def send_sale_notification(
        self,
        to_email: str,
        listing_title: str,
        amount: float,
        buyer: Optional[str] = None,
        order_id: Optional[str] = None
    ) -> bool:
        """Notify seller that an item sold."""
        if not self.is_configured():
            return False
        subject = f"CardLister Pro: Sale! {listing_title[:50]}"
        body = f"""
Your listing sold!

Title: {listing_title}
Amount: ${amount:.2f}
{f'Buyer: {buyer}' if buyer else ''}
{f'Order ID: {order_id}' if order_id else ''}

View your eBay Seller Hub for details.
"""
        return self._send(to_email, subject, body)
    
    def send_low_inventory_alert(
        self,
        to_email: str,
        listings: List[dict]
    ) -> bool:
        """Notify when inventory is low on listings."""
        if not self.is_configured() or not listings:
            return False
        subject = f"CardLister Pro: Low inventory on {len(listings)} listing(s)"
        lines = "\n".join([f"- {item.get('title', 'Unknown')} (qty: {item.get('quantity', 0)})" for item in listings[:10]])
        body = f"""
The following listings have low or zero inventory:

{lines}
"""
        return self._send(to_email, subject, body)
    
    def _send(self, to: str, subject: str, body: str) -> bool:
        try:
            msg = MIMEMultipart()
            msg['From'] = self.from_email
            msg['To'] = to
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            return True
        except Exception:
            return False
