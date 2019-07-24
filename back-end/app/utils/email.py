"""
File:email.py
Author:laoyang
"""
from flask import current_app
from flask_mail import Message
from app.extensions import mail
from threading import Thread


def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)


def send_email(subject, recipients:list, sender:str, text_body:str, html_body:str, attachments=None, sync=False):
    """发送邮件"""
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body

    if sync:
        mail.send(msg)
    else:
        Thread(target=send_async_email, args=(current_app._get_current_object(), msg)).start().start()
