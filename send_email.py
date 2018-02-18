from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from validate_email import validate_email
from email import encoders
import os.path as op
import smtplib
import socket


class SendEmail:
    def __init__(self, conn_param, use_TLS = True):
        """
            conn_param = [host, port, user, password] in that order. <list>
            use_TLS = Boolean value indicating usage of TLS. <boolean>
        """
        if(not isinstance(conn_param, list)):
            return "Connection parameters are in invalid format."
        
        self.is_OK = True;
        self.default_from_name = conn_param[2]
        
        try:
            if(use_TLS):
                self.s = smtplib.SMTP(conn_param[0], conn_param[1])
                self.s.starttls()
            else:
                self.s = smtplib.SMTP_SSL(conn_param[0], conn_param[1])
                
            self.s.login(conn_param[2], conn_param[3])
            """This exception is raised for address-related errors, for getaddrinfo() and getnameinfo()."""
        except socket.gaierror as err: 
            print("Error: {}".format(err))
            self.is_OK = False;
        except smtplib.SMTPNotSupportedError:
            print("SMTP AUTH extension not supported by server.")
            self.is_OK = False;
        except smtplib.SMTPAuthenticationError:
            print("The server didn't accept the username/password combination provided OR\naccount does not provide access to less secure apps.");
            self.is_OK = False;
        except smtplib.SMTPServerDisconnected: 
            print("Connection closed unexpectedly.")
            self.is_OK = False;
            
    def parse_attachments(self, msg, attachments):
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
    
    def check_mail_address(self, mail):
        """
            mail: list of email addresses. <list>
        """
        if(not isinstance(mail, list)):
            return False;
        
        """Validate each email in the list"""
        for i in mail:
            if(not validate_email(i)):
                return False;
            
        return True
            
    def send(self, to, from_name = None, cc = None, bcc = None, subject = '', body = '', attachments = None):
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
        
        if(not self.is_OK):
            print("Message sending failed. Connection not found.")
        else: 
            # setup the parameters of the message
            msg = MIMEMultipart()
            
            if(not from_name):
                from_name = self.default_from_name
            
            msg['From'] = from_name; 
            
            if(not to):
                print("'to' address not specified.")
                return
            
            if(not self.check_mail_address(to) or \
                (cc and not self.check_mail_address(cc)) or \
                 (bcc and not self.check_mail_address(bcc))):
                print("Email address is not in required format and/or is invalid.")
                return
            
            msg['To']= ', '.join(to);
            
            if(cc):
                msg['Cc'] = ', '.join(cc);
                
            if(bcc):
                msg['Bcc'] = ', '.join(bcc);
            
            msg['Subject'] = subject

            msg.attach(MIMEText(body, 'plain'))
           
            if(attachments): 
                if(isinstance(attachments, list)):
                    self.parse_attachments(msg, attachments)
                else:
                    print("Attachments are provided in invalid format.")
            
            # send the message via the server set up earlier.
            self.s.send_message(msg)
            
            self.s.quit()
            
            print("Your message has been sent successfully.")
