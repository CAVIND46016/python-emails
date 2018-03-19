"""Connect to smtp.gmail.com on port 587 for TLS, 
   port 465 for SSL)
""" 
from send_email import SendEmail

def main():           
    """
    Entry-point for the function.
    """
    send_email = SendEmail(['smtp.gmail.com', 587, 'abc@gmail.com', 'abc123'])
    send_email.send(to_address=['xyz@gmail.com'])

if __name__ == "__main__":
    main()
    
