"""
Creates a SMTP connection and sends an email.
"""
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os.path as op
import socket

import smtplib
from validate_email import validate_email

class SendEmail:
    """
    Contains the logic for sending an email.
    """
    def __init__(self, conn_param, use_TLS=True):
        """
            conn_param = [host, port, user, password] in that order. <list>
            use_TLS = Boolean value indicating usage of TLS. <boolean>
        """
        if not isinstance(conn_param, list):
            return "Connection parameters are in invalid format."
        
        self.is_ok = True
        self.default_from_name = conn_param[2]
        
        try:
            if use_TLS:
                self.smtp_conn = smtplib.SMTP(conn_param[0], conn_param[1])
                self.smtp_conn.starttls()
            else:
                self.smtp_conn = smtplib.SMTP_SSL(conn_param[0], conn_param[1])
                
            self.smtp_conn.login(conn_param[2], conn_param[3])
        except socket.gaierror as err: 
            # This exception is raised for address-related errors, 
            # for getaddrinfo() and getnameinfo().
            print("Error: {}".format(err))
            self.is_ok = False
        except smtplib.SMTPNotSupportedError:
            print("SMTP AUTH extension not supported by server.")
            self.is_ok = False
        except smtplib.SMTPAuthenticationError:
            print("The server didn't accept the username/password combination provided \
                    OR\naccount does not provide access to less secure apps.")
            self.is_ok = False
        except smtplib.SMTPServerDisconnected: 
            print("Connection closed unexpectedly.")
            self.is_ok = False
    
    @staticmethod       
    def parse_attachments(msg, attachments):
        """
            msg: <class 'email.mime.multipart.MIMEMultipart'>
            attachments: a list of full file paths of respective attachments. <list>
        """
        for path in attachments:
            part = MIMEBase('application', "octet-stream")
            with open(path, 'rb') as file:
                part.set_payload(file.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition',
                            'attachment; filename="{}"'.format(op.basename(path)))
            
            msg.attach(part)
    
    @staticmethod 
    def check_mail_address(emails):
        """
            mail: list of email addresses. <list>
        """
        if not isinstance(emails, list):
            return False
        
        for mail in emails:
            if not validate_email(mail):
                return False
            
        return True
            
    def send(self, to_address, from_name=None, cc_address=None, \
             bcc_address=None, subject='', body='', attachments=None):
        """
            to:            'To' email address <list> ==> mandatory parameter
            ********  Rest are optional parameters  **********
            from_name:      From name to be displayed. <str> default value is user email address
            cc:            'cc' email address <list>
            bcc:           'bcc' email address <list>
            subject:       Subject matter of email <str>
            body:          Body of the email. <str>
            attachments:   a list of full file paths of respective attachments. <list>
        """
        
        if not self.is_ok:
            print("Message sending failed. Connection not found.")
        else: 
            # setup the parameters of the message
            msg = MIMEMultipart()
            
            if not from_name:
                from_name = self.default_from_name
            
            msg['From'] = from_name 
            
            if not to_address:
                print("'to' address not specified.")
                return
            
            if not self.check_mail_address(to_address) or \
                (cc_address and not self.check_mail_address(cc_address)) or \
                 (bcc_address and not self.check_mail_address(bcc_address)):
                print("Email address is not in required format and/or is invalid.")
                return
            
            msg['To'] = ', '.join(to_address)
            
            if cc_address:
                msg['Cc'] = ', '.join(cc_address)
                
            if bcc_address:
                msg['Bcc'] = ', '.join(bcc_address)
            
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))
           
            if attachments: 
                if isinstance(attachments, list):
                    self.parse_attachments(msg, attachments)
                else:
                    print("Attachments are provided in an invalid format.")
            
            # send the message via the server set up earlier.
            try:
                self.smtp_conn.send_message(msg)
            except smtplib.SMTPSenderRefused:
                print("Your message exceeded allowed message size limits.\
                        \nMessage sending failed. Connection not found.")
                return
            
            self.smtp_conn.quit()
            print("Your message has been sent successfully.")
