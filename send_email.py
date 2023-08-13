"""
Creates an SMTP connection and sends an email.
"""

import os
import ast
import logging
from email.header import Header
from email.utils import formataddr
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

import smtplib
from smtplib import SMTPNotSupportedError, SMTPAuthenticationError, \
    SMTPServerDisconnected, SMTPSenderRefused, SMTPConnectError
from validate_email import validate_email

logger = logging.getLogger(__name__)

DEFAULT_EMAIL_CREDENTIALS = ast.literal_eval(
    os.getenv("DEFAULT_EMAIL_CREDENTIALS")
)


class Email:

    def __init__(
        self,
        credentials=DEFAULT_EMAIL_CREDENTIALS
    ):
        self.credentials = credentials
        self.smtp_conn = self.connect()
        self.msg = MIMEMultipart()

    @property
    def credentials(self):
        return self._credentials

    @credentials.setter
    def credentials(self, codes):
        if not codes:
            raise ValueError("'Credentials' cannot be empty")

        self._credentials = codes

    def connect(self):
        """
        Establishes an SMTP connection with the email server.
        """

        con = None
        use_tls = self.credentials.get("use_tls", True)
        try:
            con_method = smtplib.SMTP if use_tls else smtplib.SMTP_SSL
            con = con_method(
                self.credentials.get("host"),
                self.credentials.get("port"),
            )

            con.login(
                self.credentials.get("user"),
                self.credentials.get("password")
            )
        except (
            SMTPNotSupportedError,
            SMTPAuthenticationError,
            SMTPServerDisconnected,
            SMTPConnectError
        ) as ex:
            logger.error(f"<%s>: %s", type(ex).__name__, ex, exc_info=True)

        return con

    @staticmethod
    def parse_attachments(attachments):
        """
        Parse and prepare attachments for the email message.

        :param attachments: List of file paths for attachments.
        :return: List of MIMEBase attachment parts.
        """

        if not isinstance(attachments, (list, tuple)):
            raise ValueError("Attachments are provided in an invalid format.")

        parts = []
        for path in attachments:
            part = MIMEBase("application", "octet-stream")
            with open(path, "rb") as file:
                part.set_payload(file.read())
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition",
                f'attachment; filename="{os.path.basename(path)}"'
            )
            parts.append(part)

        return parts

    def init_msg(
        self,
        subject,
        body,
        attachments=None
    ):
        """
        Initialize the email message.

        :param subject: The subject of the email.
        :param body: The body/content of the email.
        :param attachments: List of file paths for attachments (optional).
        :return: None
        """

        if not attachments:
            attachments = []
        self.msg["Subject"] = subject
        self.msg.attach(MIMEText(body, "plain"))

        attachment_parts = Email.parse_attachments(attachments)
        for part in attachment_parts:
            self.msg.attach(part)

    def add_recipients(
        self,
        from_name,
        to_address,
        cc_address,
        bcc_address
    ):
        """
        Add recipients to the email message.

        :param from_name: The name of the sender.
        :param to_address: List of email addresses for the primary recipients.
        :param cc_address: List of email addresses for the carbon copy recipients.
        :param bcc_address: List of email addresses for the blind carbon copy recipients.
        """

        def validate(emails_):
            if emails_ is None:
                return True
            return isinstance(
                emails_, (list, tuple, set)
            ) and all(validate_email(k) for k in emails_)

        if not validate(to_address) or not validate(cc_address) or not validate(bcc_address):
            raise ValueError("Email address is not in required format and/or is invalid.")

        self.msg["From"] = formataddr(
            (str(Header(from_name, "utf-8")),
             self.credentials.get("user"))) if from_name else self.credentials.get("user")

        self.msg["To"] = ", ".join(to_address) if to_address else None
        self.msg["Cc"] = ", ".join(cc_address) if cc_address else None
        self.msg["Bcc"] = ", ".join(bcc_address) if bcc_address else None

    def send(
        self,
        to_address=None,
        from_name=None,
        cc_address=None,
        bcc_address=None,
        subject="",
        body="",
        attachments=None
    ):
        """
        Send an email.

        :param to_address: List of email addresses for the primary recipients.
        :param from_name: The name of the sender.
        :param cc_address: List of email addresses for the carbon copy recipients.
        :param bcc_address: List of email addresses for the blind carbon copy recipients.
        :param subject: The subject of the email.
        :param body: The body/content of the email.
        :param attachments: List of file paths for attachments (optional).
        """

        self.init_msg(
            subject,
            body,
            attachments
        )
        self.add_recipients(
            from_name,
            to_address,
            cc_address,
            bcc_address
        )

        try:
            self.smtp_conn.send_message(self.msg)
        except SMTPSenderRefused as ex:
            logger.error(f"<%s>: %s", type(ex).__name__, ex, exc_info=True)
        finally:
            self.smtp_conn.quit()
