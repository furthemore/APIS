from django.core.mail import send_mail
from django.template.loader import render_to_string
from .models import *

def sendRegistrationEmail(order, email):
    orderItems = OrderItem.objects.filter(order=order)
    orderDict = {}
    for oi in orderItems:
        ao = AttendeeOptions.objects.filter(orderItem=oi)
        orderDict[oi] = ao
    # send payment receipt
#    import pdb; pdb.set_trace()
    data = {'reference': order.reference, 'order': order, 'orderItems': orderDict}
    msgTxt = render_to_string('registration/emails/registrationPayment.txt', data)
    msgHtml = render_to_string('registration/emails/registrationPayment.html', data)
    sendEmail("registration@furthemore.org", [email], 
              "Furthemore 2018 Registration Payment", msgTxt, msgHtml)

    # send registration confirmations to all people in the order
    for oi in orderItems:
        data = {'reference': order.reference, 'orderItem': oi}
        msgTxt = render_to_string('registration/emails/registration.txt', data)
        msgHtml = render_to_string('registration/emails/registration.html', data)
        sendEmail("registration@furthemore.org", [oi.badge.attendee.email], 
                 "Furthemore 2018 Registration Confirmation", msgTxt, msgHtml)

        # send vip notification if necessary
        if oi.priceLevel.emailVIP:
            data = {'badge': oi.badge}
            msgTxt = render_to_string('registration/emails/vipNotification.txt', data)
            msgHtml = render_to_string('registration/emails/vipNotification.html', data)
            sendEmail("registration@furthemore.org", [email for email in oi.priceLevel.emailVIPEmails.split(',')], 
                 "Furthemore 2018 VIP Registration", msgTxt, msgHtml)


def sendUpgradePaymentEmail(attendee, order):
    data = {'reference': order.reference}
    msgTxt = render_to_string('registration/emails/upgrade.txt', data)
    msgHtml = render_to_string('registration/emails/upgrade.html', data)
    sendEmail("registration@furthemore.org", [attendee.email], "Furthemore 2018 Upgrade Payment", 
              msgTxt, msgHtml)


def sendStaffRegistrationEmail(orderId, email):
    order = Order.objects.get(id=orderId)
    data = {'reference': order.reference}
    msgTxt = render_to_string('registration/emails/staffRegistration.txt', data)
    msgHtml = render_to_string('registration/emails/staffRegistration.html', data)
    sendEmail("registration@furthemore.org", [email], "Furthemore 2018 Staff Registration", 
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
    sendEmail("marketplace-noreply@furthemore.org", [dealer.attendee.email], 
              "Fur The More 2018 Dealer Application", msgTxt, msgHtml)

    data = {'dealer': dealer}
    msgTxt = render_to_string('registration/emails/dealerNotice.txt', data)
    msgHtml = render_to_string('registration/emails/dealerNotice.html', data)
    sendEmail("marketplace-noreply@furthemore.org", ["marketplacehead@furthemore.org"], 
              "Fur The More 2018 Dealer Application Received", msgTxt, msgHtml)

def sendDealerAsstFormEmail(dealer):
    data = {'dealer': dealer}    
    msgTxt = render_to_string('registration/emails/dealerAsstForm.txt', data)
    msgHtml = render_to_string('registration/emails/dealerAsstForm.html', data)
    sendEmail("marketplace-noreply@furthemore.org", [dealer.attendee.email], 
              "Fur The More 2018 Dealer Assistant Addition", msgTxt, msgHtml)


def sendDealerAsstEmail(dealerId):
    dealer = Dealer.objects.get(id=dealerId)
    data = {}    
    msgTxt = render_to_string('registration/emails/dealerAsst.txt', data)
    msgHtml = render_to_string('registration/emails/dealerAsst.html', data)
    sendEmail("marketplace-noreply@furthemore.org", [dealer.attendee.email], 
              "Fur The More 2018 Dealer Assistant Addition", msgTxt, msgHtml)

    sendEmail("marketplace-noreply@furthemore.org", ["marketplacehead@furthemore.org"], 
              "Fur The More 2018 Dealer Application", "Dealer assistant addition received.", "Dealer asistant addition received.")

def sendDealerPaymentEmail(dealer, order):
    orderItem = OrderItem.objects.filter(order=order).first()
    options = AttendeeOptions.objects.filter(orderItem=orderItem)
    data = {'order': order, 'dealer': dealer, 'orderItem': orderItem, 'options': options}
    msgTxt = render_to_string('registration/emails/dealerPayment.txt', data)
    msgHtml = render_to_string('registration/emails/dealerPayment.html', data)

    sendEmail("marketplace-noreply@furthemore.org", [dealer.attendee.email],
              "Fur The More 2018 Dealer Payment", msgTxt, msgHtml)

def sendDealerUpdateEmail(dealerId):
    dealer = Dealer.objects.get(id=dealerId)
    data = {}
    msgTxt = render_to_string('registration/emails/dealerUpdate.txt', data)
    msgHtml = render_to_string('registration/emails/dealerUpdate.html', data)

    sendEmail("marketplace-noreply@furthemore.org", [dealer.attendee.email],
              "Fur The More 2018 Dealer Information Update", msgTxt, msgHtml)
    

def sendApprovalEmail(dealerQueryset):
    for dealer in dealerQueryset:
        data = {'dealer': dealer}
        msgTxt = render_to_string('registration/emails/dealerApproval.txt', data)
        msgHtml = render_to_string('registration/emails/dealerApproval.html', data)
        sendEmail("marketplace-noreply@furthemore.org", [dealer.attendee.email], 
                  "Fur The More 2018 Dealer Application", msgTxt, msgHtml)


def sendEmail(fromAddress, toAddressList, subject, message, htmlMessage):
    send_mail(
      subject,
      message,
      fromAddress,
      toAddressList,
      fail_silently=False,
      html_message=htmlMessage
    )
