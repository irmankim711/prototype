"""
Email Service for sending reports and notifications
Handles sending reports via email with attachments
"""

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

# Try importing SendGrid
try:
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail, Attachment, FileContent, FileName, FileType, Disposition
    import base64
    HAS_SENDGRID = True
except ImportError:
    HAS_SENDGRID = False

logger = logging.getLogger(__name__)

def send_report_email(to_email: str, report: Any, attach_file: bool = True) -> Dict[str, Any]:
    """
    Send report via email
    
    Args:
        to_email: Recipient email address
        report: Report object with title, description, output_url
        attach_file: Whether to attach the report file
        
    Returns:
        Dictionary with send result
    """
    try:
        # Try SendGrid first, then fall back to SMTP
        if HAS_SENDGRID and os.getenv('SENDGRID_API_KEY'):
            return _send_via_sendgrid(to_email, report, attach_file)
        else:
            return _send_via_smtp(to_email, report, attach_file)
            
    except Exception as e:
        logger.error(f"Error sending email: {e}")
        return {'status': 'error', 'error': str(e)}


def _send_via_sendgrid(to_email: str, report: Any, attach_file: bool = True) -> Dict[str, Any]:
    """Send email via SendGrid service"""
    try:
        sg = SendGridAPIClient(api_key=os.getenv('SENDGRID_API_KEY'))
        
        # Create email content
        subject = f"Report Ready: {report.title}"
        
        html_content = f"""
        <html>
        <body>
            <h2>Your Report is Ready</h2>
            <p>Dear User,</p>
            <p>Your requested report "<strong>{report.title}</strong>" has been generated and is ready for review.</p>
            
            <h3>Report Details:</h3>
            <ul>
                <li><strong>Title:</strong> {report.title}</li>
                <li><strong>Generated:</strong> {report.created_at.strftime('%B %d, %Y at %I:%M %p')}</li>
                <li><strong>Status:</strong> {report.status.title()}</li>
            </ul>
            
            {f'<p><strong>Description:</strong> {report.description}</p>' if report.description else ''}
            
            <p>The report has been attached to this email for your convenience.</p>
            
            <hr>
            <p><small>This is an automated message from the Report Generation System.</small></p>
        </body>
        </html>
        """
        
        # Create message
        message = Mail(
            from_email=os.getenv('FROM_EMAIL', 'reports@example.com'),
            to_emails=to_email,
            subject=subject,
            html_content=html_content
        )
        
        # Add attachment if requested and file exists
        if attach_file and report.output_url and os.path.exists(report.output_url):
            try:
                with open(report.output_url, 'rb') as f:
                    data = f.read()
                    encoded_file = base64.b64encode(data).decode()
                
                filename = os.path.basename(report.output_url)
                attachment = Attachment(
                    FileContent(encoded_file),
                    FileName(filename),
                    FileType('application/vnd.openxmlformats-officedocument.wordprocessingml.document'),
                    Disposition('attachment')
                )
                message.attachment = attachment
                
            except Exception as e:
                logger.warning(f"Could not attach file: {e}")
        
        # Send email
        response = sg.send(message)
        
        return {
            'status': 'sent',
            'service': 'sendgrid',
            'status_code': response.status_code,
            'message_id': response.headers.get('X-Message-Id', 'unknown')
        }
        
    except Exception as e:
        logger.error(f"SendGrid error: {e}")
        raise


def _send_via_smtp(to_email: str, report: Any, attach_file: bool = True) -> Dict[str, Any]:
    """Send email via SMTP"""
    try:
        # SMTP configuration
        smtp_host = os.getenv('SMTP_HOST', 'smtp.gmail.com')
        smtp_port = int(os.getenv('SMTP_PORT', 587))
        smtp_user = os.getenv('SMTP_USER')
        smtp_pass = os.getenv('SMTP_PASS')
        from_email = os.getenv('FROM_EMAIL', smtp_user)
        
        if not smtp_user or not smtp_pass:
            raise ValueError("SMTP credentials not configured")
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = from_email
        msg['To'] = to_email
        msg['Subject'] = f"Report Ready: {report.title}"
        
        # Email body
        body = f"""
Dear User,

Your requested report "{report.title}" has been generated and is ready for review.

Report Details:
- Title: {report.title}
- Generated: {report.created_at.strftime('%B %d, %Y at %I:%M %p')}
- Status: {report.status.title()}
"""
        
        if report.description:
            body += f"- Description: {report.description}\n"
        
        body += """
The report has been attached to this email for your convenience.

Best regards,
Report Generation System

---
This is an automated message.
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Add attachment if requested and file exists
        if attach_file and report.output_url and os.path.exists(report.output_url):
            try:
                with open(report.output_url, 'rb') as attachment:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment.read())
                
                encoders.encode_base64(part)
                
                filename = os.path.basename(report.output_url)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename= {filename}'
                )
                
                msg.attach(part)
                
            except Exception as e:
                logger.warning(f"Could not attach file: {e}")
        
        # Send email
        server = smtplib.SMTP(smtp_host, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_pass)
        text = msg.as_string()
        server.sendmail(from_email, to_email, text)
        server.quit()
        
        return {
            'status': 'sent',
            'service': 'smtp',
            'smtp_host': smtp_host
        }
        
    except Exception as e:
        logger.error(f"SMTP error: {e}")
        raise


def send_notification_email(to_email: str, subject: str, message: str, 
                          template: str = 'basic') -> Dict[str, Any]:
    """
    Send a notification email
    
    Args:
        to_email: Recipient email
        subject: Email subject
        message: Email message
        template: Email template to use
        
    Returns:
        Dictionary with send result
    """
    try:
        if HAS_SENDGRID and os.getenv('SENDGRID_API_KEY'):
            return _send_notification_sendgrid(to_email, subject, message, template)
        else:
            return _send_notification_smtp(to_email, subject, message, template)
            
    except Exception as e:
        logger.error(f"Error sending notification: {e}")
        return {'status': 'error', 'error': str(e)}


def _send_notification_sendgrid(to_email: str, subject: str, message: str, template: str) -> Dict[str, Any]:
    """Send notification via SendGrid"""
    sg = SendGridAPIClient(api_key=os.getenv('SENDGRID_API_KEY'))
    
    # Apply template
    if template == 'alert':
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif;">
            <div style="background-color: #f8d7da; border: 1px solid #f5c6cb; padding: 15px; border-radius: 5px;">
                <h3 style="color: #721c24; margin-top: 0;">⚠️ System Alert</h3>
                <p style="color: #721c24;">{message}</p>
            </div>
            <hr>
            <p><small>This is an automated message from the Report Generation System.</small></p>
        </body>
        </html>
        """
    elif template == 'success':
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif;">
            <div style="background-color: #d4edda; border: 1px solid #c3e6cb; padding: 15px; border-radius: 5px;">
                <h3 style="color: #155724; margin-top: 0;">✅ Success</h3>
                <p style="color: #155724;">{message}</p>
            </div>
            <hr>
            <p><small>This is an automated message from the Report Generation System.</small></p>
        </body>
        </html>
        """
    else:  # basic template
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif;">
            <div style="padding: 20px;">
                <p>{message}</p>
            </div>
            <hr>
            <p><small>This is an automated message from the Report Generation System.</small></p>
        </body>
        </html>
        """
    
    mail = Mail(
        from_email=os.getenv('FROM_EMAIL', 'notifications@example.com'),
        to_emails=to_email,
        subject=subject,
        html_content=html_content
    )
    
    response = sg.send(mail)
    
    return {
        'status': 'sent',
        'service': 'sendgrid',
        'status_code': response.status_code
    }


def _send_notification_smtp(to_email: str, subject: str, message: str, template: str) -> Dict[str, Any]:
    """Send notification via SMTP"""
    smtp_host = os.getenv('SMTP_HOST', 'smtp.gmail.com')
    smtp_port = int(os.getenv('SMTP_PORT', 587))
    smtp_user = os.getenv('SMTP_USER')
    smtp_pass = os.getenv('SMTP_PASS')
    from_email = os.getenv('FROM_EMAIL', smtp_user)
    
    if not smtp_user or not smtp_pass:
        raise ValueError("SMTP credentials not configured")
    
    # Create message
    msg = MIMEMultipart('alternative')
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = subject
    
    # Plain text version
    text_message = f"{message}\n\n---\nThis is an automated message from the Report Generation System."
    
    # HTML version based on template
    if template == 'alert':
        html_message = f"""
        <html>
        <body>
            <div style="background-color: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 5px;">
                <h3>⚠️ System Alert</h3>
                <p>{message}</p>
            </div>
            <hr>
            <p><small>This is an automated message from the Report Generation System.</small></p>
        </body>
        </html>
        """
    elif template == 'success':
        html_message = f"""
        <html>
        <body>
            <div style="background-color: #d4edda; border: 1px solid #c3e6cb; padding: 15px; border-radius: 5px;">
                <h3>✅ Success</h3>
                <p>{message}</p>
            </div>
            <hr>
            <p><small>This is an automated message from the Report Generation System.</small></p>
        </body>
        </html>
        """
    else:
        html_message = f"""
        <html>
        <body>
            <p>{message}</p>
            <hr>
            <p><small>This is an automated message from the Report Generation System.</small></p>
        </body>
        </html>
        """
    
    # Attach parts
    msg.attach(MIMEText(text_message, 'plain'))
    msg.attach(MIMEText(html_message, 'html'))
    
    # Send email
    server = smtplib.SMTP(smtp_host, smtp_port)
    server.starttls()
    server.login(smtp_user, smtp_pass)
    text = msg.as_string()
    server.sendmail(from_email, to_email, text)
    server.quit()
    
    return {
        'status': 'sent',
        'service': 'smtp',
        'smtp_host': smtp_host
    }


def send_bulk_notifications(recipients: List[str], subject: str, message: str, 
                          template: str = 'basic') -> Dict[str, Any]:
    """
    Send bulk notification emails
    
    Args:
        recipients: List of recipient email addresses
        subject: Email subject
        message: Email message
        template: Email template to use
        
    Returns:
        Dictionary with bulk send results
    """
    results = {
        'total': len(recipients),
        'sent': 0,
        'failed': 0,
        'errors': []
    }
    
    for recipient in recipients:
        try:
            result = send_notification_email(recipient, subject, message, template)
            if result['status'] == 'sent':
                results['sent'] += 1
            else:
                results['failed'] += 1
                results['errors'].append({
                    'recipient': recipient,
                    'error': result.get('error', 'Unknown error')
                })
        except Exception as e:
            results['failed'] += 1
            results['errors'].append({
                'recipient': recipient,
                'error': str(e)
            })
    
    return results


def test_email_configuration() -> Dict[str, Any]:
    """
    Test email configuration
    
    Returns:
        Dictionary with test results
    """
    results = {
        'sendgrid_available': False,
        'smtp_configured': False,
        'recommended_service': 'none'
    }
    
    # Check SendGrid
    if HAS_SENDGRID and os.getenv('SENDGRID_API_KEY'):
        results['sendgrid_available'] = True
        results['recommended_service'] = 'sendgrid'
    
    # Check SMTP
    smtp_user = os.getenv('SMTP_USER')
    smtp_pass = os.getenv('SMTP_PASS')
    if smtp_user and smtp_pass:
        results['smtp_configured'] = True
        if results['recommended_service'] == 'none':
            results['recommended_service'] = 'smtp'
    
    return results


def format_report_email_body(report: Any, include_summary: bool = True) -> str:
    """
    Format email body for report notifications
    
    Args:
        report: Report object
        include_summary: Whether to include report summary
        
    Returns:
        Formatted email body
    """
    body = f"""
Dear User,

Your report "{report.title}" has been successfully generated and is ready for review.

Report Details:
• Title: {report.title}
• Generated: {report.created_at.strftime('%B %d, %Y at %I:%M %p')}
• Status: {report.status.title()}
"""
    
    if report.description:
        body += f"• Description: {report.description}\n"
    
    # Add report summary if available and requested
    if include_summary and hasattr(report, 'data') and report.data:
        ai_analysis = report.data.get('ai_analysis', {})
        summary = ai_analysis.get('summary')
        if summary:
            body += f"\nReport Summary:\n{summary}\n"
        
        # Add key metrics
        key_metrics = ai_analysis.get('key_metrics', {})
        if key_metrics:
            body += "\nKey Metrics:\n"
            for metric, value in key_metrics.items():
                if isinstance(value, (int, float)):
                    body += f"• {metric.replace('_', ' ').title()}: {value}\n"
    
    body += """
The full report has been attached to this email for your convenience.

If you have any questions or need assistance, please don't hesitate to contact our support team.

Best regards,
The Report Generation Team

---
This is an automated message from the Report Generation System.
Generated at """ + datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    return body
