"""
Connect to smtp.gmail.com
port 587 for TLS
port 465 for SSL
"""

from send_email import Email


def main():
    """
    Entry-point for the function.
    """

    email_connection_params = {
        "host": "smtp.gmail.com",
        "port": 587,
        "user": "sender@gmail.com",
        "password": "xxxxxxx",
        "use_tls": True
    }
    send_email = Email(**email_connection_params)
    send_email.send(to_address=['receiver@abc.com'])


if __name__ == "__main__":
    main()
