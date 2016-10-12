from django.core.mail import send_mail
from .models import *

def sendRegistrationEmail(orderId):
    order = Order.objects.get(id=orderId)
    sendEmail("registration@furthemore.org", order.attendee.email, "Registration Complete!", "Thanks!")


def sendEmail(fromAddress, toAddress, subject, message):
    send_mail(
      subject,
      message,
      fromAddress,
      [toAddress],
      fail_silently=False,
    )
