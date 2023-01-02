"""
Creates an SMTP connection and sends an email.
"""

from email.header import Header
from email.utils import formataddr
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os
import ast

import smtplib
from smtplib import SMTPNotSupportedError, SMTPAuthenticationError, SMTPServerDisconnected, SMTPSenderRefused, \
    SMTPConnectError
from validate_email import validate_email

DEFAULT_EMAIL_CREDENTIALS = ast.literal_eval(os.environ.get('DEFAULT_EMAIL_CREDENTIALS'))


class Email:

    def __init__(self, credentials=DEFAULT_EMAIL_CREDENTIALS):
        self.credentials = credentials
        self.smtp_conn = self.__connect()
        self.msg = MIMEMultipart()

    @property
    def credentials(self):
        return self._credentials

    @credentials.setter
    def credentials(self, codes):
        if not codes:
            raise ValueError('\'Credentials\' cannot be empty')

        if not isinstance(codes, dict):
            raise TypeError(f'Invalid type(s) for credentials: {type(codes)}')

        self._credentials = codes

    def __connect(self):
        __use_tls = self.credentials.get('use_tls', True)
        try:
            if __use_tls:
                con = smtplib.SMTP(self.credentials.get('host'), self.credentials.get('port'))
                con.starttls()
            else:
                con = smtplib.SMTP_SSL(self.credentials.get('host'), self.credentials.get('port'))

            con.login(self.credentials.get('user'), self.credentials.get('password'))
        except (SMTPNotSupportedError, SMTPAuthenticationError, SMTPServerDisconnected, SMTPConnectError) as ex:
            print(f"<{type(ex).__name__}>: {ex}")
            raise

        return con

    @staticmethod
    def __parse_attachments(attachments):
        if not isinstance(attachments, (list, tuple)):
            raise ValueError("Attachments are provided in an invalid format.")

        parts = []
        for path in attachments:
            part = MIMEBase('application', "octet-stream")
            with open(path, 'rb') as file:
                part.set_payload(file.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f'attachment; filename="{os.path.basename(path)}"')
            parts.append(part)

        return parts

    def init_msg(self, subject, body, attachments):
        self.msg['Subject'] = subject
        self.msg.attach(MIMEText(body, 'plain'))

        attachment_parts = self.__parse_attachments(attachments) if attachments else []
        for part in attachment_parts:
            self.msg.attach(part)

    def add_recipients(self, from_name, to_address, cc_address, bcc_address):
        def __validate(emails_):
            return emails_ and isinstance(emails_, (list, tuple)) and all(validate_email(k) for k in emails_)

        if not __validate(to_address) or not __validate(cc_address) or not __validate(bcc_address):
            raise ValueError("Email address is not in required format and/or is invalid.")

        self.msg['From'] = formataddr(
            (str(Header(from_name, 'utf-8')), self.credentials.get('user'))) if from_name else self.credentials.get(
            'user')

        self.msg['To'] = ', '.join(to_address) if to_address else None
        self.msg['Cc'] = ', '.join(cc_address) if cc_address else None
        self.msg['Bcc'] = ', '.join(bcc_address) if bcc_address else None

    def send(self, to_address=None, from_name=None, cc_address=None,
             bcc_address=None, subject='', body='', attachments=None):

        self.init_msg(subject, body, attachments)
        self.add_recipients(from_name, to_address, cc_address, bcc_address)

        try:
            self.smtp_conn.send_message(self.msg)
        except SMTPSenderRefused as ex:
            print(f"<{type(ex).__name__}>: {ex}")
            raise
        finally:
            self.smtp_conn.quit()
