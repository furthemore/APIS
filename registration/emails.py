from django.core.mail import send_mail
from .models import *

def sendRegistrationEmail(orderId):
    pass


def sendEmail(fromAddress, toAddress, subject, message):
    send_mail(
      subject,
      message,
      fromAddress,
      [toAddress],
      fail_silently=False,
    )
