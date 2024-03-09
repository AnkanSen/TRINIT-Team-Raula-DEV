from random import shuffle, choice

from django.conf import settings
from django.core.mail import send_mail


from smtplib import SMTP
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import datetime
from bs4 import BeautifulSoup as bb
from django import forms

def get_code() -> str:
    a = list("12345678901234567890")
    shuffle(a)
    a = "".join(a)
    return "".join(choice(a) for _ in range(6))


def send_code(email: str) -> str:
    code: str = get_code()
    # curr = datetime.datetime.now()
    email = email
    SERVER = "smtp.gmail.com"
    PORT = 587
    FROM = "ankitch860@gmail.com"
    TO = email
    PASS = 'stcuyuhbivtltoey'
    msg = MIMEMultipart()
    msg['subject'] = "Verify your account"
    msg['From'] = FROM
    msg['To'] = TO
    co=f"Verify your account.Your verification code is {code}"
    msg.attach(MIMEText(co, 'html'))
    print("Creating mail")
    server = SMTP(SERVER, PORT)
    server.set_debuglevel(1)
    server.ehlo()
    server.starttls()
    server.login(FROM, PASS)
    server.sendmail(FROM, TO, msg.as_string())
    print('Sending Email')
    server.quit()
    print('Email sent ......')
 
    return code
