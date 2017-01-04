from django.core.mail import send_mail
from .models import *

def sendRegistrationEmail(orderId, email):
    order = Order.objects.get(id=orderId)
    sendEmail("registration@furthemore.org", [email], "Furthemore 2017 Registration Payment", 
              "Thank you for your payment." +
              "\r\nYour payment confirmation is: " + order.reference +
              "\r\nIf you have any questions about your order, please contact us at registration@furthemore.org." +
              "\r\nThank you! \r\n \r\n'Kiric \r\nHead of Registration", 
              "<h3>Thank you for your payment.</h3>" + 
              "<p>Your payment confirmation number is: " + order.reference + "</p>" + 
              "<p>If you have any questions about your order, please contact us at <a href='mailto:registration@furthemore.org'>registration@furthemore.org</a>.</p>" + 
              "<p>Thank you!</p><p>'Kiric<br/>Head of Registration</p>")
    orderItems = OrderItem.objects.filter(order=order)
    for oi in orderItems:
        sendEmail("registration@furthemore.org", [oi.attendee.email], "Furthemore 2017 Registration Confirmation", 
                  "Thank you for registering." + 
                  "\r\nYour registration confirmation is: " + order.reference +  
                  "\r\nYou my pick up your badge from the pre-reg line at the convention. If you have any questions regarding your registration, please contact registration@furthemore.org." + 
                  "\r\nSee you at the convention!" + 
                  "\r\n \r\nKiric \r\nHead of Registration", 
                  "<h3>Thank you for registering</h3>" + 
                  "<p>Your registration confirmation is: " + order.reference + "</p>" + 
                  "<p>You my pick up your badge from the pre-reg line at the convention. If you have any questions regarding your registration, please contact <a href='mailto:registration@furthemore.org'>registration@furthemore.org</a>.</p>" + 
                  "<p>See you at the convention!</p>" + 
                  "<p>&nbsp;</p>" + 
                  "<p>Kiric<br/> Head of Registration</p>")

def sendStaffRegistrationEmail(orderId, email):
    order = Order.objects.get(id=orderId)
    sendEmail("registration@furthemore.org", [email], "Furthemore 2017 Staff Registration", 
              "Thank you for registering as staff." +
              "\r\nYour registration confirmation number is: " + order.reference + 
              "\r\nIf you have any questions about your registration, please contact your supervisor or registration@furthemore.org." +
              "\r\nThank you! \r\n \r\nKiric \r\nHead of Registration", 
              "<h3>Thank you for registering as staff</h3>" +
              "<p>Your registration confirmation number is: " + order.reference + "</p>" + 
              "<p>If you have any questions about your order, please contact your supervisor or <a href='mailto:registration@furthemore.org'>registration@furthemore.org</a>.</p>" + 
              "<p>Thank you!</p><p>Kiric<br/>Head of Registration</p>")

def sendStaffPromotionEmail(staff):
    sendEmail("registration@furthemore.org", [staff.attendee.email], "Welcome to Furthemore Staff!", 
              "Use this link to register as staff: http://dawningbrooke.net/apis/registration/staff/" + staff.registrationToken, 
              "<p>Use this link to register as staff: <a href='http://dawningbrooke.net/apis/registration/staff/" + staff.registrationToken + "'>http://dawningbrooke.net/apis/registration/staff/" + staff.registrationToken + "</a></p>")

def sendDealerApplicationEmail(dealerId):
    dealer = Dealer.objects.get(id=dealerId)
    
    sendEmail("exhibitions@furthemore.org", [dealer.attendee.email], 
              "Fur The More 2017 Dealer Application", 
              "Thank you for your application to be a dealer at Furthemore 2017." + 
              "\r\nThe cut off date for primary applicants will be Nov 12th at 11:59pm, and selections will be made/notifications sent by November 19th. If you have not received an acceptance notification by that date, you will be placed on the waitlist for the next available spot. " +
              "\r\nIf you have any questions, please feel free to contact us: exhibitions@furthemore.org" +
              "\r\nIf you have listed any parters, they will receive an email with instructions about how to register after your payment has been received." + 
              "\r\nThank you!", 
              "<h3>Thank you for your application to be a dealer at Furthemore 2017</h3><p>The cut off date for primary applicants will be Nov 12th at 11:59pm, and selections will be made/notifications sent by November 19th. </p>" +
              "<p>If you have not received an acceptance notification by that date, you will be placed on the waitlist for the next available spot. If you have any questions, please feel free to contact us: <a href='mailto:exhibitions@furthemore.org'>exhibitions@furthemore.org</a></p>" + 
              "<p>If you have listed any parters, they will receive an email with instructions about how to register after your payment has been received.</p>" + 
              "<p>Thank you!</p>"
              )

    sendEmail("exhibitions@furthemore.org", ["exhibitions@furthemore.org"], 
              "Fur The More 2017 Dealer Application", "New dealer reg received.", "New dealer reg received.")

def sendDealerPaymentEmail(dealerId, confirmation):
    dealer = Dealer.objects.get(id=dealerId)

    sendEmail("exhibitions@furthemore.org", [dealer.attendee.email],
              "Fur The More 2017 Dealer Payment",
              "Thank you for your payment! \r\n Your confirmation number is: " + confirmation + 
              "\r\nIf you have listed any partners, they will receive an email with instructions about how to register.",
              "<h3>Thank you for your payment!</h3> <p>Your confirmation number is: " + confirmation + "</p>" + 
              "<p>If you have listed any partners, they will receive an email with instructions about how to register.</p>"
    )

def sendDealerUpdateEmail(dealerId):
    dealer = Dealer.objects.get(id=dealerId)

    sendEmail("exhibitions@furthemore.org", [dealer.attendee.email],
              "Fur The More 2017 Dealer Information Udate",
              "Your information has been updated in our database" + 
              "\r\nIf you did not do this, please contact exhibitions@furthemore.org ASAP to correct your information.",
              "<h3>Your information has been updated</h3><p>Your information has been updated in our database.</p>" + 
              "<p>If you did not do this, please contact <a href='mailto:exhibitions@furthemore.org'>exhibitions@furthemore.org</a> ASAP to correct your information.</p>"
    )
    

def sendApprovalEmail(dealerQueryset):
    for dealer in dealerQueryset:
        if not dealer.emailed:
            sendEmail("exhibitions@furthemore.org", [dealer.attendee.email], "Fur The More 2017 Dealer Application", 
                      "Your dealer application for Furthemore 2017 has been approved!" + 
                      "\r\nPlease go to the url below and enter the email address you used to register." + 
                      "\r\n http://www.furthemore.org/apis/registration/dealer/" + dealer.registrationToken + 
                      "\r\nDue to a bug in the dealer application form, we did not record badge names or save your Buttons for a Cause offer. Please enter the required badge name and update the Buttons for a Cause information if you would like to participate in that effort."
                      "\r\nYou will receive an email with a confirmation number after submitting your payment. If you have any further questions, please feel free to contact us: exhibitions@furthemore.org" + 
                      "\r\nThank you and welcome to the Furthemore 2017 Dealer's Den!",
                      "<h3>Your dealer application for Furthemore 2017 has been approved!</h3>" + 
                      "<p>Please go to the url below and enter the email address you used to register.</p>" + 
                      "<p><a href='http://www.furthemore.org/apis/registration/dealer/" + dealer.registrationToken + "'>http://www.furthemore.org/apis/registration/dealer/" + dealer.registrationToken + "</a></p>" 
                      "<p>Due to a bug in the dealer application form, we did not record badge names or save your Buttons for a Cause offer. Please enter the required badge name and update the Buttons for a Cause information if you would like to participate in that effort.</p>"
                      "<p>You will receive an email with a confirmation number after submitting your payment. If you have any further questions, please feel free to contact us: <a href='mailto:exhibitions@furthemore.org'>exhibitions@furthemore.org</a></p>" + 
                      "<p>Thank you and welcome to the Furthemore 2017 Dealer's Den!</p>"
            )


def sendEmail(fromAddress, toAddressList, subject, message, htmlMessage):
    send_mail(
      subject,
      message,
      fromAddress,
      toAddressList,
      fail_silently=False,
      html_message=htmlMessage
    )
