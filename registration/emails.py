from django.core.mail import send_mail
from django.template.loader import render_to_string
from .models import *

def sendRegistrationEmail(orderId, email):
    order = Order.objects.get(id=orderId)
    data = {'reference': order.reference}
    msgTxt = render_to_string('registration/emails/registrationPayment.txt', data)
    msgHtml = render_to_string('registration/emails/registrationPayment.html', data)
    sendEmail("registration@furthemore.org", [email], 
              "Furthemore 2017 Registration Payment", msgTxt, msgHtml)

    orderItems = OrderItem.objects.filter(order=order)
    for oi in orderItems:
        msgTxt = render_to_string('registration/emails/registration.txt', data)
        msgHtml = render_to_string('registration/emails/registration.html', data)
        sendEmail("registration@furthemore.org", [oi.attendee.email], 
                 "Furthemore 2017 Registration Confirmation", msgTxt, msgHtml)

def sendUpgradePaymentEmail(attendee, order):
    data = {'reference': order.reference}
    msgTxt = render_to_string('registration/emails/upgrade.txt', data)
    msgHtml = render_to_string('registration/emails/upgrade.html', data)
    sendEmail("registration@furthemore.org", [attendee.email], "Furthemore 2017 Upgrade Payment", 
              msgTxt, msgHtml)

def sendJerseyEmail(orderId, email):
    order = Order.objects.get(id=orderId)
    data = {'reference': order.reference}
    msgTxt = render_to_string('registration/emails/jersey.txt', data)
    msgHtml = render_to_string('registration/emails/jersey.html', data)
    sendEmail("registration@furthemore.org", [email], "Furthemore 2017 Jersey Payment", 
              msgTxt, msgHtml)

def sendStaffJerseyEmail(orderId, email):
    order = Order.objects.get(id=orderId)
    data = {'reference': order.reference}
    msgTxt = render_to_string('registration/emails/sjersey.txt', data)
    msgHtml = render_to_string('registration/emails/sjersey.html', data)
    sendEmail("registration@furthemore.org", [email], "Furthemore 2017 Staff Jersey Payment", 
              msgTxt, msgHtml)
        

def sendStaffRegistrationEmail(orderId, email):
    order = Order.objects.get(id=orderId)
    data = {'reference': order.reference}
    msgTxt = render_to_string('registration/emails/staffRegistration.txt', data)
    msgHtml = render_to_string('registration/emails/staffRegistration.html', data)
    sendEmail("registration@furthemore.org", [email], "Furthemore 2017 Staff Registration", 
              msgTxt, msgHtml)

def sendStaffPromotionEmail(staff):
    data = {'registrationToken': staff.registrationToken}
    msgTxt = render_to_string('registration/emails/staffPromotion.txt', data)
    msgHtml = render_to_string('registration/emails/staffPromotion.html', data)
    sendEmail("registration@furthemore.org", [staff.attendee.email], "Welcome to Furthemore Staff!", 
              msgTxt, msgHtml)

def sendDealerApplicationEmail(dealerId):
    dealer = Dealer.objects.get(id=dealerId)
    data = {}    
    msgTxt = render_to_string('registration/emails/dealer.txt', data)
    msgHtml = render_to_string('registration/emails/dealer.html', data)
    sendEmail("exhibitions@furthemore.org", [dealer.attendee.email], 
              "Fur The More 2017 Dealer Application", msgTxt, msgHtml)

    sendEmail("exhibitions@furthemore.org", ["exhibitions@furthemore.org"], 
              "Fur The More 2017 Dealer Application", "New dealer reg received.", "New dealer reg received.")

def sendDealerAsstFormEmail(dealer):
    data = {'dealer': dealer}    
    msgTxt = render_to_string('registration/emails/dealerAsstForm.txt', data)
    msgHtml = render_to_string('registration/emails/dealerAsstForm.html', data)
    sendEmail("exhibitions@furthemore.org", [dealer.attendee.email], 
              "Fur The More 2017 Dealer Assistant Addition", msgTxt, msgHtml)


def sendDealerAsstEmail(dealerId):
    dealer = Dealer.objects.get(id=dealerId)
    data = {}    
    msgTxt = render_to_string('registration/emails/dealerAsst.txt', data)
    msgHtml = render_to_string('registration/emails/dealerAsst.html', data)
    sendEmail("exhibitions@furthemore.org", [dealer.attendee.email], 
              "Fur The More 2017 Dealer Assistant Addition", msgTxt, msgHtml)

    sendEmail("exhibitions@furthemore.org", ["exhibitions@furthemore.org"], 
              "Fur The More 2017 Dealer Application", "Dealer assistant addition received.", "Dealer asistant addition received.")

def sendDealerPaymentEmail(dealer, order):
    orderItem = OrderItem.objects.filter(order=order).first()
    attendeeOptions = AttendeeOptions.objects.filter(orderItem=orderItem)
    data = {'order': order, 'dealer': dealer, 'orderItem': orderItem, 'options': attendeeOptions}
    msgTxt = render_to_string('registration/emails/dealerPayment.txt', data)
    msgHtml = render_to_string('registration/emails/dealerPayment.html', data)

    sendEmail("exhibitions@furthemore.org", [dealer.attendee.email],
              "Fur The More 2017 Dealer Payment", msgTxt, msgHtml)

def sendDealerUpdateEmail(dealerId):
    dealer = Dealer.objects.get(id=dealerId)
    data = {}
    msgTxt = render_to_string('registration/emails/dealerUpdate.txt', data)
    msgHtml = render_to_string('registration/emails/dealerUpdate.html', data)

    sendEmail("exhibitions@furthemore.org", [dealer.attendee.email],
              "Fur The More 2017 Dealer Information Update", msgTxt, msgHtml)
    

def sendApprovalEmail(dealerQueryset):
    for dealer in dealerQueryset:
        data = {'dealer': dealer}
        msgTxt = render_to_string('registration/emails/dealerApproval.txt', data)
        msgHtml = render_to_string('registration/emails/dealerApproval.html', data)
        sendEmail("exhibitions@furthemore.org", [dealer.attendee.email], 
                  "Fur The More 2017 Dealer Application", msgTxt, msgHtml)


def sendEmail(fromAddress, toAddressList, subject, message, htmlMessage):
    send_mail(
      subject,
      message,
      fromAddress,
      toAddressList,
      fail_silently=False,
      html_message=htmlMessage
    )
