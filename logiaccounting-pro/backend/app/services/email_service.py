"""
Email Notification Service (Simulated)
In production, integrate with SendGrid, AWS SES, or SMTP
"""

from datetime import datetime
from typing import Optional, Dict, List
from dataclasses import dataclass, asdict


@dataclass
class EmailLog:
    id: str
    to: str
    subject: str
    template: str
    data: dict
    status: str  # sent, failed, pending
    sent_at: str
    error: Optional[str] = None


class EmailService:
    """Simulated email service for demo purposes"""

    _instance = None
    _logs: List[EmailLog] = []
    _counter = 0

    TEMPLATES = {
        "payment_reminder": {
            "subject": "Payment Reminder: {reference}",
            "body": """
Hi {user_name},

This is a reminder that payment {reference} for ${amount:.2f} is due on {due_date}.

Please ensure timely payment to avoid late fees.

Best regards,
LogiAccounting Pro
            """
        },
        "payment_overdue": {
            "subject": "OVERDUE: Payment {reference}",
            "body": """
Hi {user_name},

Payment {reference} for ${amount:.2f} was due on {due_date} and is now overdue.

Please process this payment immediately.

Best regards,
LogiAccounting Pro
            """
        },
        "low_stock_alert": {
            "subject": "Low Stock Alert: {material_name}",
            "body": """
Hi {user_name},

Material "{material_name}" (Ref: {reference}) is running low.

Current quantity: {quantity}
Minimum stock: {min_stock}

Please reorder soon.

Best regards,
LogiAccounting Pro
            """
        },
        "anomaly_detected": {
            "subject": "Anomaly Detected: {anomaly_type}",
            "body": """
Hi {user_name},

Our system has detected an anomaly that requires your attention.

Type: {anomaly_type}
Severity: {severity}
Description: {description}

Please review this in the AI Dashboard.

Best regards,
LogiAccounting Pro
            """
        },
        "welcome": {
            "subject": "Welcome to LogiAccounting Pro",
            "body": """
Hi {user_name},

Welcome to LogiAccounting Pro! Your account has been created.

Email: {email}
Role: {role}

You can login at: {login_url}

Best regards,
LogiAccounting Pro Team
            """
        }
    }

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._logs = []
            cls._counter = 0
        return cls._instance

    def send(
        self,
        to: str,
        template: str,
        data: Dict,
        subject_override: Optional[str] = None
    ) -> EmailLog:
        """Send an email (simulated - logs to memory)"""
        self._counter += 1

        if template not in self.TEMPLATES:
            raise ValueError(f"Unknown template: {template}")

        tmpl = self.TEMPLATES[template]

        try:
            subject = subject_override or tmpl["subject"].format(**data)
            body = tmpl["body"].format(**data)

            log = EmailLog(
                id=f"EMAIL-{self._counter:06d}",
                to=to,
                subject=subject,
                template=template,
                data=data,
                status="sent",
                sent_at=datetime.utcnow().isoformat()
            )

            # In production: Actually send email here
            # For demo: Just log it
            print(f"[EMAIL] To: {to}, Subject: {subject}")

        except Exception as e:
            log = EmailLog(
                id=f"EMAIL-{self._counter:06d}",
                to=to,
                subject=f"[{template}]",
                template=template,
                data=data,
                status="failed",
                sent_at=datetime.utcnow().isoformat(),
                error=str(e)
            )

        self._logs.insert(0, log)

        # Keep last 1000 logs
        if len(self._logs) > 1000:
            self._logs = self._logs[:1000]

        return log

    def get_logs(
        self,
        limit: int = 50,
        offset: int = 0,
        status: Optional[str] = None,
        template: Optional[str] = None
    ) -> tuple:
        """Get email logs with optional filters"""
        filtered = self._logs.copy()

        if status:
            filtered = [l for l in filtered if l.status == status]

        if template:
            filtered = [l for l in filtered if l.template == template]

        total = len(filtered)
        paginated = filtered[offset:offset + limit]

        return [asdict(l) for l in paginated], total

    def get_templates(self) -> Dict:
        """Get available email templates"""
        return {
            name: {
                "subject": tmpl["subject"],
                "preview": tmpl["body"][:200] + "..."
            }
            for name, tmpl in self.TEMPLATES.items()
        }


# Global instance
email_service = EmailService()
