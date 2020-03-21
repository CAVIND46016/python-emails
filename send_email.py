"""
Creates a SMTP connection and sends an email.
"""
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os

import smtplib
from validate_email import validate_email

class Email:
    """
    Contains the logic for sending an email.
    """
    def __init__(self, **kwargs):
        """
        Args:
            **kwargs: Keyword arguments with host, port,
            user, password and use_tls as keys.
        """
        self.__dict__.update(kwargs)

    def _login(self):
        """
        Sets up an SMTP connection object using the connection parameters.
        """
        try:
            if self.use_tls:
                smtp_conn = smtplib.SMTP(self.host, self.port)
                smtp_conn.starttls()
            else:
                smtp_conn = smtplib.SMTP_SSL(self.host, self.port)

            smtp_conn.login(self.user, self.password)
        except smtplib.SMTPNotSupportedError as err:
            raise Exception(f"SMTP AUTH extension not supported by server.\n{err}")
        except smtplib.SMTPAuthenticationError as err:
            raise Exception(f"The server didn't accept the username/password " 
                            f"combination provided OR account does not provide "
                            f"access to less secure apps.\n{err}")
        except smtplib.SMTPServerDisconnected as err:
            raise Exception(f"Connection closed unexpectedly.\n{err}")
        except:
            raise Exception("Something went wrong.")

        return smtp_conn

    @staticmethod
    def _parse_attachments(attachments):
        """
        Args:
            attachments<list>: a list of full file paths of respective attachments.
        """
        parts = []
        for path in attachments:
            part = MIMEBase('application', "octet-stream")
            with open(path, 'rb') as file:
                part.set_payload(file.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition',
                            'attachment; filename="{}"'.format(os.path.basename(path)))
            parts.append(part)

        return parts

    @staticmethod
    def _check_mail_address(emails):
        """
            mail: list of email addresses. <list>
        """
        if not isinstance(emails, list):
            return False

        for mail in emails:
            if not validate_email(mail):
                return False

        return True

    def send(self, to_address, from_name=None, cc_address=None,
             bcc_address=None, subject='', body='', attachments=None):
        """
        Args:
            to_address <list>:   'To' email address (mandatory parameter)

            (optional parameters)
            from_name <str>:     From name to be displayed. Default value is user email address
            cc_address <list>:   'cc' email address
            bcc_address <list>:  'bcc' email address
            subject <str>:       Email subject
            body <str>:          Email body
            attachments <list>:  A list of full file paths of respective attachments
        """
        msg = MIMEMultipart()
        msg['From'] = from_name if from_name else self.user

        if not to_address:
            raise ValueError("'to' address not specified.")

        if not self._check_mail_address(to_address) or \
            (cc_address and not self._check_mail_address(cc_address)) or \
             (bcc_address and not self._check_mail_address(bcc_address)):
            raise ValueError("Email address is not in required format and/or is invalid.")

        msg['To'] = ', '.join(to_address)
        msg['Cc'] = ', '.join(cc_address) if cc_address else None
        msg['Bcc'] = ', '.join(bcc_address) if bcc_address else None

        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        if attachments and not isinstance(attachments, list):
            raise ValueError("Attachments are provided in an invalid format.")

        attachment_parts = self._parse_attachments(attachments) if attachments else []
        for part in attachment_parts:
            msg.attach(part)

        smtp_conn = self._login()
        try:
            smtp_conn.send_message(msg)
            print("Message sent.")
        except smtplib.SMTPSenderRefused:
            raise Exception("Your message exceeded allowed message size limits.\n"
                            "Message sending failed. Connection not found.")
        finally:
            smtp_conn.quit()
