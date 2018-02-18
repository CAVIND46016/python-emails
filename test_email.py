from send_email import SendEmail

def main():       
    """Connect to smtp.gmail.com on port 587 since we are using TLS.)"""     
    
    s = SendEmail(['smtp.gmail.com', 587, 'abc@gmail.com', 'abc123']);
    s.send(to = ['xyz@gmail.com'])

if(__name__ == "__main__"):
    main()
