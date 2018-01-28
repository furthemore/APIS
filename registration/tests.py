from datetime import timedelta
from django.utils import timezone
from django.core.urlresolvers import reverse
from django.test import TestCase, Client
from .models import *


class OrdersTestCases(TestCase):
    def setUp(self):
        now = timezone.now()
        ten_days = timedelta(days=10)
        self.price1 = PriceLevel(name='Attendee', description='Some test description here', basePrice=45.00, 
                            startDate=now-ten_days, endDate=now+ten_days, public=True)
        self.price2 = PriceLevel(name='Sponsor', description='Woot!', basePrice=90.00, 
                            startDate=now-ten_days, endDate=now+ten_days, public=True)
        self.price3 = PriceLevel(name='Super', description='In the future', basePrice=150.00, 
                            startDate=now+ten_days, endDate=now+ten_days+ten_days, public=True)
        self.price4 = PriceLevel(name='Elite', description='ooOOOoooooo', basePrice=235.00, 
                            startDate=now-ten_days, endDate=now+ten_days, public=False)
        self.price5 = PriceLevel(name='Raven God', description='yay', basePrice=675.00, 
                            startDate=now-ten_days, endDate=now+ten_days, public=False,
                            emailVIP=True, emailVIPEmails='carissa.brittain@gmail.com' )
        self.price1.save()
        self.price2.save()
        self.price3.save()
        self.price4.save()
        self.price5.save()

        self.department1 = Department(name="BestDept")
        self.department2 = Department(name="WorstDept")

        self.department1.save()
        self.department2.save()

        self.discount = Discount(codeName="FiveOff", amountOff=5.00,
                                 startDate=now, endDate=now+ten_days)
        self.onetimediscount = Discount(codeName="OneTime", percentOff=10, oneTime=True,
                                 startDate=now, endDate=now+ten_days)

        self.staffdiscount = Discount(codeName="StaffDiscount", amountOff=45.00,
                                 startDate=now, endDate=now+ten_days)
        self.dealerdiscount = Discount(codeName="DealerDiscount", amountOff=45.00,
                                 startDate=now, endDate=now+ten_days)
        self.discount.save()
        self.onetimediscount.save()
        self.staffdiscount.save()
        self.dealerdiscount.save()

        self.shirt1 = ShirtSizes(name='Test_Large')
        self.shirt1.save()

        #TODO: shirt option type
        self.option1 = PriceLevelOption(optionName="Conbook",optionPrice=0.00,optionExtraType="bool")
        self.option2 = PriceLevelOption(optionName="Shirt Size",optionPrice=0.00,optionExtraType="ShirtSizes")
        self.option3 = PriceLevelOption(optionName="Something Pricy",optionPrice=100.00,optionExtraType="int")

        self.option1.save()
        self.option2.save()
        self.option3.save()

        self.price1.priceLevelOptions.add(self.option1)
        self.price1.priceLevelOptions.add(self.option2)
        self.price2.priceLevelOptions.add(self.option1)
        self.price3.priceLevelOptions.add(self.option1)
        self.price3.priceLevelOptions.add(self.option3)
        

        self.event = Event(name="Test Event 2050!", dealerRegStart=now-ten_days, dealerRegEnd=now+ten_days,
                           staffRegStart=now-ten_days, staffRegEnd=now+ten_days,
                           attendeeRegStart=now-ten_days, attendeeRegEnd=now+ten_days,
                           onlineRegStart=now-ten_days, onlineRegEnd=now+ten_days, 
                           eventStart=now-ten_days, eventEnd=now+ten_days)
        self.event.save()

        self.table1 = TableSize(name="Booth", description="description here", chairMin=0, chairMax=1,
                                tableMin=0, tableMax=1, partnerMin=0, partnerMax=1, basePrice=Decimal(130))
        self.table2 = TableSize(name="Booth", description="description here", chairMin=0, chairMax=1,
                                tableMin=0, tableMax=1, partnerMin=0, partnerMax=2, basePrice=Decimal(160))
       
        self.table1.save()
        self.table2.save()

        self.client = Client()

    def test_getprices(self):
        response = self.client.get(reverse('pricelevels'))
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertEqual(result.__len__(), 2)
        basic = [item for item in result if item['name'] == 'Attendee']
        self.assertEqual(basic[0]['base_price'], '45.00')
        special = [item for item in result if item['name'] == 'Special']
        self.assertEqual(special, [])

    def test_fullsingleorder(self):
        postData = {'attendee': {'firstName': "Tester", 'lastName': "Testerson",
                                 'address1': "123 Somewhere St",'address2': "",'city': "Place",'state': "PA",'country': "USA",'postal': "12345",
                                 'phone': "1112223333",'email': "testerson@mailinator.org",'birthdate': "01/01/1990",'asl': "false",
                                 'badgeName': "FluffyButz",'emailsOk': "true",'volunteer': "false",'volDepts': "", 'surveyOk': "false"},
                    'priceLevel': {'id': self.price1.id, 'options': [{'id': self.option1.id, 'value': "true"}, {'id': self.option2.id, 'value': self.shirt1.id}]},
                    'event': 'Test Event 2050!'}
	
        response = self.client.post(reverse('addToCart'), json.dumps(postData), content_type="application/json")
        self.assertEqual(response.status_code, 200)

        attendee = Attendee.objects.get(firstName="Tester")
        self.assertEqual(attendee.lastName, "Testerson")
        badge = Badge.objects.get(attendee=attendee, event=self.event)
        self.assertEqual(badge.badgeName, "FluffyButz")
        orderitem = OrderItem.objects.get(badge=badge)
        self.assertEqual(orderitem.priceLevel_id, self.price1.id)
        self.assertEqual(orderitem.enteredBy, "WEB")
        orderoption2 = orderitem.attendeeoptions_set.get(option__id=self.option2.id)
        self.assertEqual(orderoption2.optionValue, self.shirt1.id.__str__())

        response = self.client.get(reverse('cart'))
        self.assertEqual(response.status_code, 200)
        cart = response.context["orderItems"]
        self.assertEqual(len(cart), 1)
        self.assertEqual(cart[0].id, orderitem.id)
        total = response.context["total"]
        self.assertEqual(total, 45)

        response = self.client.get(reverse('cancelOrder'))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse('cart'))
        self.assertEqual(response.status_code, 200)
        cart = response.context["orderItems"]
        self.assertEqual(len(cart), 0)
        self.assertEqual(Attendee.objects.filter(firstName="Tester").count(), 0)
        self.assertEqual(Badge.objects.filter(badgeName="FluffyButz").count(), 0)
        self.assertEqual(OrderItem.objects.filter(id=orderitem.id).count(), 0)
        self.assertEqual(AttendeeOptions.objects.filter(orderItem=orderitem).count(), 0)
        self.assertEqual(PriceLevel.objects.filter(id=self.price1.id).count(), 1)

        

    def test_multipleorder(self):
        postData = {'attendee': {'firstName': "Frank", 'lastName': "Testerson",
                                 'address1': "123 Somewhere St",'address2': "",'city': "Place",'state': "PA",'country': "USA",'postal': "12345",
                                 'phone': "1112223333",'email': "testerson@mailinator.org",'birthdate': "01/01/1990", 'asl': "false",
                                 'badgeName': "FluffyButz",'emailsOk': "true",'volunteer': "false",'volDepts': "", 'surveyOk': "false"},
                    'priceLevel': {'id': self.price1.id, 'options': [{'id': self.option1.id, 'value': "true"}, {'id': self.option2.id, 'value': self.shirt1.id}]},
                    'event': 'Test Event 2050!'}

	
        response = self.client.post(reverse('addToCart'), json.dumps(postData), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        postData = {'attendee': {'firstName': "Felix", 'lastName': "Testerson",
                                 'address1': "123 Somewhere St",'address2': "",'city': "Place",'state': "PA",'country': "USA",'postal': "12345",
                                 'phone': "1112223333",'email': "testerson@mailinator.org",'birthdate': "01/01/1990", 'asl': "false",
                                 'badgeName': "FluffyButz",'emailsOk': "true",'volunteer': "false",'volDepts': "", 'surveyOk': "true"},
                    'priceLevel': {'id': self.price2.id, 'options': [{'id': self.option3.id, 'value': 1}]},
                    'event': 'Test Event 2050!'}

	
        response = self.client.post(reverse('addToCart'), json.dumps(postData), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        postData = {'attendee': {'firstName': "Julie", 'lastName': "Testerson",
                                 'address1': "123 Somewhere St",'address2': "",'city': "Place",'state': "PA",'country': "USA",'postal': "12345",
                                 'phone': "1112223333",'email': "testerson@mailinator.org",'birthdate': "01/01/1990", 'asl': "false",
                                 'badgeName': "FluffyButz",'emailsOk': "true",'volunteer': "false",'volDepts': "", 'surveyOk': "false"},
                    'priceLevel': {'id': self.price1.id, 'options': [{'id': self.option1.id, 'value': "true"}, {'id': self.option2.id, 'value': self.shirt1.id}]},
                    'event': 'Test Event 2050!'}
	
        response = self.client.post(reverse('addToCart'), json.dumps(postData), content_type="application/json")
        self.assertEqual(response.status_code, 200)

        response = self.client.get(reverse('cart'))
        self.assertEqual(response.status_code, 200)
        cart = response.context["orderItems"]
        self.assertEqual(len(cart), 3)
        total = response.context["total"]
        self.assertEqual(total, 45+90+100+45)

        attendee = Attendee.objects.get(firstName='Felix')
        badge = Badge.objects.get(attendee=attendee,event=self.event)
        postData = {'id': OrderItem.objects.get(badge=badge).id}
        response = self.client.post(reverse('removeFromCart'), json.dumps(postData), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse('cart'))
        self.assertEqual(response.status_code, 200)
        cart = response.context["orderItems"]
        self.assertEqual(len(cart), 2)
        total = response.context["total"]
        self.assertEqual(total, 45+45)
        self.assertEqual(Attendee.objects.filter(firstName="Felix").count(), 0)

        response = self.client.get(reverse('cancelOrder'))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse('cart'))
        self.assertEqual(response.status_code, 200)
        cart = response.context["orderItems"]
        self.assertEqual(len(cart), 0)
        self.assertEqual(Attendee.objects.filter(firstName="Frank").count(), 0)
        self.assertEqual(Attendee.objects.filter(firstName="Julie").count(), 0)

    def test_checkout(self):
        postData = {'attendee': {'firstName': "Bea", 'lastName': "Testerson",
                                 'address1': "123 Somewhere St",'address2': "",'city': "Place",'state': "PA",'country': "USA",'postal': "12345",
                                 'phone': "1112223333",'email': "carissa.brittain@gmail.com",'birthdate': "01/01/1990", 'asl': "false",
                                 'badgeName': "FluffyButz",'emailsOk': "true",'volunteer': "false",'volDepts': "", 'surveyOk': "false"},
                    'priceLevel': {'id': self.price1.id, 'options': [{'id': self.option1.id, 'value': "true"}, {'id': self.option2.id, 'value': self.shirt1.id}]},
                    'event': 'Test Event 2050!'}
	
        response = self.client.post(reverse('addToCart'), json.dumps(postData), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        attendee = Attendee.objects.get(firstName='Bea')
        postData = {'billingData': {'cc_firstname':attendee.firstName, 'cc_lastname': attendee.lastName, 'cc_number':"4111111111111111", 
                    'cc_month':"12", 'cc_year':"2020", 'cc_security':"123", 'address1':attendee.address1,
                    'address2':attendee.address2, 'city':attendee.city, 'state':attendee.state,
                    'country':attendee.country, 'postal':attendee.postalCode, 'email':attendee.email},
                    'orgDonation':'1.00', 'charityDonation':'10.00', 'eventId':self.event.id, 'onsite': False}
        response = self.client.post(reverse('checkout'), json.dumps(postData), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        attendee = Attendee.objects.get(firstName='Bea')
        badge = Badge.objects.get(attendee=attendee,event=self.event)
        self.assertNotEqual(badge.registeredDate, None)
        self.assertEqual(badge.orderitem_set.count(), 1)
        orderItem = badge.orderitem_set.first()
        self.assertNotEqual(orderItem.order, None)
        order = orderItem.order
        self.assertEqual(order.discount, None)
        self.assertEqual(order.total, 45+11)
        self.assertEqual(attendee.postalCode, order.billingPostal)
        self.assertEqual(order.orgDonation, 1.00)
        self.assertEqual(order.charityDonation, 10.00)

    def test_vip_checkout(self):
        postData = {'attendee': {'firstName': "Bea", 'lastName': "Testerson",
                                 'address1': "123 Somewhere St",'address2': "",'city': "Place",'state': "PA",'country': "USA",'postal': "12345",
                                 'phone': "1112223333",'email': "carissa.brittain@gmail.com",'birthdate': "01/01/1990", 'asl': "false",
                                 'badgeName': "FluffyButz",'emailsOk': "true",'volunteer': "false",'volDepts': "", 'surveyOk': "false"},
                    'priceLevel': {'id': self.price5.id, 'options': []},
                    'event': 'Test Event 2050!'}
	
        response = self.client.post(reverse('addToCart'), json.dumps(postData), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        attendee = Attendee.objects.get(firstName='Bea')
        postData = {'billingData': {'cc_firstname':attendee.firstName, 'cc_lastname': attendee.lastName, 'cc_number':"4111111111111111", 
                    'cc_month':"12", 'cc_year':"2020", 'cc_security':"123", 'address1':attendee.address1,
                    'address2':attendee.address2, 'city':attendee.city, 'state':attendee.state,
                    'country':attendee.country, 'postal':attendee.postalCode, 'email':attendee.email},
                    'orgDonation':'1.00', 'charityDonation':'10.00', 'eventId':self.event.id, 'onsite': False}
        response = self.client.post(reverse('checkout'), json.dumps(postData), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        attendee = Attendee.objects.get(firstName='Bea')
        badge = Badge.objects.get(attendee=attendee,event=self.event)
        self.assertNotEqual(badge.registeredDate, None)
        self.assertEqual(badge.orderitem_set.count(), 1)
        orderItem = badge.orderitem_set.first()
        self.assertNotEqual(orderItem.order, None)
        order = orderItem.order
        self.assertEqual(order.discount, None)
        self.assertEqual(order.total, 675+11)
        self.assertEqual(attendee.postalCode, order.billingPostal)
        self.assertEqual(order.orgDonation, 1.00)
        self.assertEqual(order.charityDonation, 10.00)



    def test_discount(self):
        postData = {'attendee': {'firstName': "Jenny", 'lastName': "Testerson",
                                 'address1': "123 Somewhere St",'address2': "",'city': "Place",'state': "PA",'country': "USA",'postal': "12345",
                                 'phone': "1112223333",'email': "testerson@mailinator.org",'birthdate': "01/01/1990", 'asl': "false",
                                 'badgeName': "FluffyButz",'emailsOk': "true",'volunteer': "false",'volDepts': "", 'surveyOk': "false"},
                    'priceLevel': {'id': self.price1.id, 'options': [{'id': self.option1.id, 'value': "true"}, {'id': self.option2.id, 'value': self.shirt1.id}]},
                    'event': 'Test Event 2050!'}
	
        response = self.client.post(reverse('addToCart'), json.dumps(postData), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        attendee = Attendee.objects.get(firstName='Jenny')
        badge = Badge.objects.get(attendee=attendee,event=self.event)
        self.assertNotEqual(badge.registeredDate, None)
        self.assertEqual(badge.orderitem_set.count(), 1)

        postData = {'discount': 'OneTime'}
        response = self.client.post(reverse('discount'), json.dumps(postData), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse('cart'))
        self.assertEqual(response.status_code, 200)
        cart = response.context["orderItems"]
        self.assertEqual(len(cart), 1)
        total = response.context["total"]
        self.assertEqual(total, 40.50)

        postData = {'billingData': {'cc_firstname':attendee.firstName, 'cc_lastname': attendee.lastName, 'cc_number':"4111111111111111", 
                    'cc_month':"12", 'cc_year':"2020", 'cc_security':"123", 'address1':attendee.address1,
                    'address2':attendee.address2, 'city':attendee.city, 'state':attendee.state,
                    'country':attendee.country, 'postal':attendee.postalCode, 'email':attendee.email},
                    'orgDonation':'0', 'charityDonation':'0', 'eventId':self.event.id, 'onsite':False}
        response = self.client.post(reverse('checkout'), json.dumps(postData), content_type="application/json")
        self.assertEqual(response.status_code, 200)

        discount = Discount.objects.get(codeName='OneTime')
        self.assertEqual(discount.used, 1)

        postData = {'discount': 'OneTime'}
        response = self.client.post(reverse('discount'), json.dumps(postData), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, '{"message": "That discount is not valid.", "success": false}')

        postData = {'discount': 'Bogus'}
        response = self.client.post(reverse('discount'), json.dumps(postData), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, '{"message": "That discount is not valid.", "success": false}')


    def test_discount_zero_sum(self):
        postData = {'attendee': {'firstName': "Harry", 'lastName': "Testerson",
                                 'address1': "123 Somewhere St",'address2': "",'city': "Place",'state': "PA",'country': "USA",'postal': "12345",
                                 'phone': "1112223333",'email': "testerson@mailinator.org",'birthdate': "01/01/1990", 'asl': "false",
                                 'badgeName': "FluffyButz",'emailsOk': "true",'volunteer': "false",'volDepts': "", 'surveyOk': "false"},
                    'priceLevel': {'id': self.price1.id, 'options': [{'id': self.option1.id, 'value': "true"}]},
                    'event': 'Test Event 2050!'}
	
        response = self.client.post(reverse('addToCart'), json.dumps(postData), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        attendee = Attendee.objects.get(firstName='Harry')
        badge = Badge.objects.get(attendee=attendee,event=self.event)
        self.assertNotEqual(badge.registeredDate, None)
        self.assertEqual(badge.orderitem_set.count(), 1)

        postData = {'discount': 'StaffDiscount'}
        response = self.client.post(reverse('discount'), json.dumps(postData), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse('cart'))
        self.assertEqual(response.status_code, 200)
        cart = response.context["orderItems"]
        self.assertEqual(len(cart), 1)
        total = response.context["total"]
        self.assertEqual(total, 0)

        postData = {}
        response = self.client.post(reverse('checkout'), json.dumps(postData), content_type="application/json")
        self.assertEqual(response.status_code, 200)




    def test_staff(self):
        attendee = Attendee(firstName="Staffer", lastName="Testerson",
                            address1="123 Somewhere St", city="Place", state="PA", country="USA", postalCode=12345,
                            phone="1112223333", email="testerson@mailinator.org", birthdate="1990-01-01")
        attendee.save()
        staff = Staff(attendee=attendee,event=self.event)
        staff.save()
        badge = Badge(attendee=attendee,event=self.event,badgeName="DisStaff")
        badge.save()
        attendee2 = Attendee(firstName="Staph", lastName="Testerson", 
                            address1="123 Somewhere St", city="Place", state="PA", country="USA", postalCode=12345,
                            phone="1112223333", email="testerson@mailinator.org", birthdate="1990-01-01")
        attendee2.save()
        staff2 = Staff(attendee=attendee2,event=self.event)
        staff2.save()
        badge2 = Badge(attendee=attendee2,event=self.event,badgeName="AnotherStaff")
        badge2.save()

        postData = {'email':attendee.email, 'token':staff.registrationToken}
        response = self.client.post(reverse('findStaff'), json.dumps(postData), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, '{"message": "STAFF", "success": true}')

        postData = {'attendee': {'id': attendee.id,'firstName': "Staffer", 'lastName': "Testerson",
                                 'address1': "123 Somewhere St",'address2': "",'city': "Place",'state': "PA",'country': "USA",'postal': "12345",
                                 'phone': "1112223333",'email': "carissa.brittain@gmail.com",'birthdate': "01/01/1990",
                                 'badgeName': "FluffyButz",'emailsOk': "true"},
                    'staff': {'id': staff.id, 
                    'department': self.department1.id, 'title': 'Something Cool',
                    'twitter': "@twitstaff", 'telegram': "@twitstaffagain",
                    'shirtsize': self.shirt1.id, 'specialSkills': "Something here",
                    'specialFood': "no water please", 'specialMedical': 'alerigic to bandaids',
                    'contactPhone': "4442223333", 'contactName': 'Test Testerson',
                    'contactRelation': 'Pet'},
                    'priceLevel': {'id': self.price3.id, 'options': [{'id': self.option3.id, 'value': 1}, {'id': self.option2.id, 'value': self.shirt1.id}]}
                    }
        response = self.client.post(reverse('addStaff'), json.dumps(postData), content_type="application/json")
        self.assertEqual(response.status_code, 200)

        response = self.client.get(reverse('invoiceStaff'))
        self.assertEqual(response.status_code, 200)
        cart = response.context["orderItems"]
        self.assertEqual(len(cart), 1)
        total = response.context["total"]
        self.assertEqual(total, 150+100-45)
        discount = response.context["discount"]
        self.assertEqual(discount.codeName, "StaffDiscount")

        postData = {'billingData': {
			'cc_number': "4111111111111111", 'cc_month': "01", 
			'cc_year': "2018", 'cc_security': "836",
			'cc_firstname': "Test", 'cc_lastname': "Credit", 'email': "thing@some.com",
                        'address1': "123 Somewhere", 'address2': "", 'city': "There",
                        'state': "PA", 'country': "USA", 'postal': "12345",
		    },
		    'charityDonation': "0",
		    'orgDonation': "0"}

        response = self.client.post(reverse('checkoutStaff'), json.dumps(postData), content_type="application/json")
        self.assertEqual(response.status_code, 200)

        badge = Badge.objects.get(attendee=attendee,event=self.event)
        orderItem = OrderItem.objects.get(badge=badge)
        orderItem = badge.orderitem_set.first()
        self.assertNotEqual(orderItem.order, None)
        order = orderItem.order
        self.assertEqual(order.discount.codeName, "StaffDiscount")
        self.assertEqual(order.total, 150+100-45)
        self.assertEqual(order.orgDonation, 0)
        self.assertEqual(order.charityDonation, 0)


        response = self.client.get(reverse('flush'))
        self.assertEqual(response.status_code, 200)

        # Staff zero-sum
        postData = {'email':attendee2.email, 'token':staff2.registrationToken}
        response = self.client.post(reverse('findStaff'), json.dumps(postData), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, '{"message": "STAFF", "success": true}')

        postData = {'attendee': {'id': attendee2.id,'firstName': "Staffer", 'lastName': "Testerson",
                                 'address1': "123 Somewhere St",'address2': "",'city': "Place",'state': "PA",'country': "USA",'postal': "12345",
                                 'phone': "1112223333",'email': "carissa.brittain@gmail.com",'birthdate': "01/01/1990",
                                 'badgeName': "FluffyButz",'emailsOk': "true"},
                    'staff': {'id': staff2.id, 
                    'department': self.department2.id, 'title': 'Something Cool',
                    'twitter': "@twitstaff", 'telegram': "@twitstaffagain",
                    'shirtsize': self.shirt1.id, 'specialSkills': "Something here",
                    'specialFood': "no water please", 'specialMedical': 'alerigic to bandaids',
                    'contactPhone': "4442223333", 'contactName': 'Test Testerson',
                    'contactRelation': 'Pet'},
                    'priceLevel': {'id': self.price1.id, 'options': [{'id': self.option1.id, 'value': "true"}, {'id': self.option2.id, 'value': self.shirt1.id}]},
                    }
        response = self.client.post(reverse('addStaff'), json.dumps(postData), content_type="application/json")
        self.assertEqual(response.status_code, 200)

        response = self.client.get(reverse('invoiceStaff'))
        self.assertEqual(response.status_code, 200)
        cart = response.context["orderItems"]
        self.assertEqual(len(cart), 1)
        total = response.context["total"]
        self.assertEqual(total, 45-45)
        discount = response.context["discount"]
        self.assertEqual(discount.codeName, "StaffDiscount")

        response = self.client.post(reverse('checkoutStaff'), "{}", content_type="application/json")
        self.assertEqual(response.status_code, 200)

        badge = Badge.objects.get(attendee=attendee2, event=self.event)
        orderItem = OrderItem.objects.get(badge=badge)
        self.assertNotEqual(orderItem.order, None)
        order = orderItem.order
        self.assertEqual(order.discount.codeName, "StaffDiscount")
        self.assertEqual(order.total, 0)

        response = self.client.get(reverse('flush'))
        self.assertEqual(response.status_code, 200)


    def test_dealer(self):
        postData = {'attendee': {'firstName': "Dealer", 'lastName': "Testerson",
                                 'address1': "123 Somewhere St",'address2': "",'city': "Place",'state': "PA",'country': "USA",'postal': "12345",
                                 'phone': "1112223333",'email': "testerson@mailinator.org",'birthdate': "01/01/1990",
                                 'badgeName': "FluffyButz",'emailsOk': "true", 'surveyOk': "true"},
                    'dealer': {'businessName':"Something Creative", 'website':"http://www.something.com",
                    'license':"jkah9435kd", 'power': True, 'wifi': True,
                    'wall': True, 'near': "Someone", 'far': "Someone Else",
                    'description': "Stuff for sale", 'tableSize': self.table1.id,  
                    'chairs': 1, 'partners': "name_1: , email_1: , license_1: , tempLicense_1: false,", 'tables': 0,
                    'reception': True, 'artShow': False, 
                    'charityRaffle': "Some stuff", 'agreeToRules': True,
                    'breakfast': True, 'switch': False,
                    'buttonOffer': "Buttons", 'asstbreakfast': False},
                    'event': 'Test Event 2050!'}

        response = self.client.post(reverse('addNewDealer'), json.dumps(postData), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        postData = {'attendee': {'firstName': "Free", 'lastName': "Testerson",
                                 'address1': "123 Somewhere St",'address2': "",'city': "Place",'state': "PA",'country': "USA",'postal': "12345",
                                 'phone': "1112223333",'email': "testerson@mailinator.org",'birthdate': "01/01/1990",
                                 'badgeName': "FluffyNutz",'emailsOk': "true", 'surveyOk': "true"},
                    'dealer': {'businessName':"Something Creative", 'website':"http://www.something.com",
				'license':"jkah9435kd", 'power': True, 'wifi': True,
                                'wall': True, 'near': "Someone", 'far': "Someone Else",
				'description': "Stuff for sale", 'tableSize': self.table1.id,  
				'chairs': 1, 'partners': "name_1: , email_1: , license_1: , tempLicense_1: false,", 'tables': 0,
				'reception': True, 'artShow': False, 
				'charityRaffle': "Some stuff", 'agreeToRules': True,
				'breakfast': True, 'switch': False,
				'buttonOffer': "Buttons", 'asstbreakfast': False},
                'event': 'Test Event 2050!'}

        response = self.client.post(reverse('addNewDealer'), json.dumps(postData), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        postData = {'attendee': {'firstName': "Dealz", 'lastName': "Testerson",
                                 'address1': "123 Somewhere St",'address2': "",'city': "Place",'state': "PA",'country': "USA",'postal': "12345",
                                 'phone': "1112223333",'email': "testerson@mailinator.org",'birthdate': "01/01/1990",
                                 'badgeName': "FluffyGutz",'emailsOk': "true", 'surveyOk': "true"},
                    'dealer': {'businessName':"Something Creative", 'website':"http://www.something.com",
				'license':"jkah9435kd", 'power': True, 'wifi': True,
                                'wall': True, 'near': "Someone", 'far': "Someone Else",
				'description': "Stuff for sale", 'tableSize': self.table2.id,  
				'chairs': 1, 'partners': "name_1: Someone, email_1: someone@here.com, license_1: temporary, tempLicense_1: true, name_2: , email_2: , license_2: , tempLicense_2: false", 'tables': 0,
				'reception': False, 'artShow': False, 
				'charityRaffle': "Some stuff", 'agreeToRules': True,
				'breakfast': True, 'switch': False,
				'buttonOffer': "Buttons", 'asstbreakfast': False},
                'event': 'Test Event 2050!'}

        response = self.client.post(reverse('addNewDealer'), json.dumps(postData), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        #import pdb; pdb.set_trace()
        attendee = Attendee.objects.get(firstName='Dealer')
        badge = Badge.objects.get(attendee=attendee,event=self.event)
        self.assertEqual(badge.badgeName, "FluffyButz")
        self.assertNotEqual(badge.registeredDate, None)
        self.assertEqual(badge.orderitem_set.count(), 0)
        dealer = Dealer.objects.get(attendee=attendee)
        self.assertNotEqual(dealer, None)
        attendee = Attendee.objects.get(firstName='Dealz')
        badge = Badge.objects.get(attendee=attendee,event=self.event)
        self.assertEqual(badge.badgeName, "FluffyGutz")
        self.assertNotEqual(badge.registeredDate, None)
        attendee = Attendee.objects.get(firstName='Free')
        badge = Badge.objects.get(attendee=attendee,event=self.event)
        self.assertEqual(badge.badgeName, "FluffyNutz")
        self.assertNotEqual(badge.registeredDate, None)

        response = self.client.get(reverse('flush'))
        self.assertEqual(response.status_code, 200)

        #Dealer
        attendee = Attendee.objects.get(firstName='Dealer')
        badge = Badge.objects.get(attendee=attendee, event=self.event)
        dealer = Dealer.objects.get(attendee=attendee)
        postData = {'token': dealer.registrationToken, 'email': attendee.email}
        response = self.client.post(reverse('findDealer'), json.dumps(postData), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        postData = {'attendee': {'id': attendee.id,'firstName': "Dealer", 'lastName': "Testerson",
                                 'address1': "123 Somewhere St",'address2': "",'city': "Place",'state': "PA",'country': "USA",'postal': "12345",
                                 'phone': "1112223333",'email': "testerson@mailinator.org",'birthdate': "01/01/1990",
                                 'badgeName': "FluffyButz",'emailsOk': "true"},
                    'dealer': {'id': dealer.id,'businessName':"Something Creative", 'website':"http://www.something.com",
				'license':"jkah9435kd", 'power': True, 'wifi': False,
                                'wall': True, 'near': "Someone", 'far': "Someone Else",
				'description': "Stuff for sale", 'tableSize': self.table1.id,  
				'chairs': 1, 'partners': "name_1: , email_1: , license_1: , tempLicense_1: false,", 'tables': 0,
				'reception': True, 'artShow': False, 
				'charityRaffle': "Some stuff", 'agreeToRules': True,
				'breakfast': True, 'switch': False,
				'buttonOffer': "Buttons", 'asstbreakfast': False},
                    'priceLevel': {'id': self.price1.id, 'options': [{'id': self.option1.id, 'value': "true"}]},
                'event': 'Test Event 2050!'}

        response = self.client.post(reverse('addDealer'), json.dumps(postData), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse('invoiceDealer'))
        self.assertEqual(response.status_code, 200)
        cart = response.context["orderItems"]
        self.assertEqual(len(cart), 1)
        total = response.context["total"]
        self.assertEqual(total, 45+130-45)
        orderItem = OrderItem.objects.get(badge=badge)
        orderItem.delete()

        response = self.client.get(reverse('flush'))
        self.assertEqual(response.status_code, 200)

        #Dealer, zero-sum
        attendee = Attendee.objects.get(firstName='Free')
        badge = Badge.objects.get(attendee=attendee, event=self.event)
        dealer = Dealer.objects.get(attendee=attendee)
        dealer.discount = 130
        dealer.save()
        postData = {'token': dealer.registrationToken, 'email': attendee.email}
        response = self.client.post(reverse('findDealer'), json.dumps(postData), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        postData = {'attendee': {'id': attendee.id,'firstName': "Free", 'lastName': "Testerson",
                                 'address1': "123 Somewhere St",'address2': "",'city': "Place",'state': "PA",'country': "USA",'postal': "12345",
                                 'phone': "1112223333",'email': "testerson@mailinator.org",'birthdate': "01/01/1990",
                                 'badgeName': "FluffyNutz",'emailsOk': "true"},
                    'dealer': {'id': dealer.id,'businessName':"Something Creative", 'website':"http://www.something.com",
				'license':"jkah9435kd", 'power': True, 'wifi': False,
                                'wall': True, 'near': "Someone", 'far': "Someone Else",
				'description': "Stuff for sale", 'tableSize': self.table1.id,  
				'chairs': 1, 'partners': "name_1: , email_1: , license_1: , tempLicense_1: false,", 'tables': 0,
				'reception': True, 'artShow': False, 
				'charityRaffle': "Some stuff", 'agreeToRules': True,
				'breakfast': True, 'switch': False,
				'buttonOffer': "Buttons", 'asstbreakfast': False},
                    'priceLevel': {'id': self.price1.id, 'options': [{'id': self.option1.id, 'value': "true"}]},
                'event': 'Test Event 2050!'}
                    
        response = self.client.post(reverse('addDealer'), json.dumps(postData), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse('invoiceDealer'))
        self.assertEqual(response.status_code, 200)
        cart = response.context["orderItems"]
        self.assertEqual(len(cart), 1)
        total = response.context["total"]
        self.assertEqual(total, 0)
        orderItem = OrderItem.objects.get(badge=badge)
        orderItem.delete()

        response = self.client.get(reverse('flush'))
        self.assertEqual(response.status_code, 200)

        #Dealer, upgrade, Wifi
        attendee = Attendee.objects.get(firstName='Dealer')
        badge = Badge.objects.get(attendee=attendee, event=self.event)
        dealer = Dealer.objects.get(attendee=attendee)
        postData = {'token': dealer.registrationToken, 'email': attendee.email}
        response = self.client.post(reverse('findDealer'), json.dumps(postData), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        postData = {'attendee': {'id': attendee.id,'firstName': "Dealer", 'lastName': "Testerson",
                                 'address1': "123 Somewhere St",'address2': "",'city': "Place",'state': "PA",'country': "USA",'postal': "12345",
                                 'phone': "1112223333",'email': "testerson@mailinator.org",'birthdate': "01/01/1990",
                                 'badgeName': "FluffyButz",'emailsOk': "true"},
                    'dealer': {'id': dealer.id,'businessName':"Something Creative", 'website':"http://www.something.com",
				'license':"jkah9435kd", 'power': True, 'wifi': True,
                                'wall': True, 'near': "Someone", 'far': "Someone Else",
				'description': "Stuff for sale", 'tableSize': self.table1.id,  
				'chairs': 1, 'partners': "name_1: , email_1: , license_1: , tempLicense_1: false,", 'tables': 0,
				'reception': True, 'artShow': False, 
				'charityRaffle': "Some stuff", 'agreeToRules': True,
				'breakfast': True, 'switch': False,
				'buttonOffer': "Buttons", 'asstbreakfast': False},
                    'priceLevel': {'id': self.price2.id, 'options': [{'id': self.option1.id, 'value': "true"}]},
                'event': 'Test Event 2050!'}
                    
        response = self.client.post(reverse('addDealer'), json.dumps(postData), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse('invoiceDealer'))
        self.assertEqual(response.status_code, 200)
        cart = response.context["orderItems"]
        self.assertEqual(len(cart), 1)
        total = response.context["total"]
        self.assertEqual(total, 90+130+45-45)
        orderItem = OrderItem.objects.get(badge=badge)
        orderItem.delete()

        response = self.client.get(reverse('flush'))
        self.assertEqual(response.status_code, 200)

        #Dealer, partners, upgrade, wifi
        attendee = Attendee.objects.get(firstName='Dealz')
        badge = Badge.objects.get(attendee=attendee, event=self.event)
        dealer = Dealer.objects.get(attendee=attendee)
        postData = {'token': dealer.registrationToken, 'email': attendee.email}
        response = self.client.post(reverse('findDealer'), json.dumps(postData), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        postData = {'attendee': {'id': attendee.id, 'firstName': "Dealz", 'lastName': "Testerson",
                                 'address1': "123 Somewhere St",'address2': "",'city': "Place",'state': "PA",'country': "USA",'postal': "12345",
                                 'phone': "1112223333",'email': "testerson@mailinator.org",'birthdate': "01/01/1990",
                                 'badgeName': "FluffyButz",'emailsOk': "true"},
                    'dealer': {'id': dealer.id, 'businessName':"Something Creative", 'website':"http://www.something.com",
				'license':"jkah9435kd", 'power': True, 'wifi': True,
                                'wall': True, 'near': "Someone", 'far': "Someone Else",
				'description': "Stuff for sale", 'tableSize': self.table2.id,  
				'chairs': 1, 'partners': "name_1: Someone, email_1: someone@here.com, license_1: temporary, tempLicense_1: true, name_2: , email_2: , license_2: , tempLicense_2: false", 'tables': 0,
				'reception': False, 'artShow': False, 
				'charityRaffle': "Some stuff", 'agreeToRules': True,
				'breakfast': True, 'switch': False,
				'buttonOffer': "Buttons", 'asstbreakfast': False},
                    'priceLevel': {'id': self.price2.id, 'options': [{'id': self.option1.id, 'value': "true"}]},
                'event': 'Test Event 2050!'}

        response = self.client.post(reverse('addDealer'), json.dumps(postData), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse('invoiceDealer'))
        self.assertEqual(response.status_code, 200)
        cart = response.context["orderItems"]
        self.assertEqual(len(cart), 1)
        total = response.context["total"]
        self.assertEqual(total, 90+45+45+160-45)
        orderItem = OrderItem.objects.get(badge=badge)
        orderItem.delete()

        response = self.client.get(reverse('flush'))
        self.assertEqual(response.status_code, 200)

        #Dealer, partners+breakfast, upgrade, discount, wifi
        attendee = Attendee.objects.get(firstName='Dealz')
        badge = Badge.objects.get(attendee=attendee, event=self.event)
        dealer = Dealer.objects.get(attendee=attendee)
        dealer.discount = 5
        dealer.save()
        postData = {'token': dealer.registrationToken, 'email': attendee.email}
        response = self.client.post(reverse('findDealer'), json.dumps(postData), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        postData = {'attendee': {'id': attendee.id, 'firstName': "Dealz", 'lastName': "Testerson",
                                 'address1': "123 Somewhere St",'address2': "",'city': "Place",'state': "PA",'country': "USA",'postal': "12345",
                                 'phone': "1112223333",'email': "testerson@mailinator.org",'birthdate': "01/01/1990",
                                 'badgeName': "FluffyButz",'emailsOk': "true"},
                    'dealer': {'id': dealer.id, 'businessName':"Something Creative", 'website':"http://www.something.com",
				'license':"jkah9435kd", 'power': True, 'wifi': True,
                                'wall': True, 'near': "Someone", 'far': "Someone Else",
				'description': "Stuff for sale", 'tableSize': self.table2.id,  
				'chairs': 1, 'partners': "name_1: Someone, email_1: someone@here.com, license_1: temporary, tempLicense_1: true, name_2: , email_2: , license_2: , tempLicense_2: false", 'tables': 0,
				'reception': False, 'artShow': False, 
				'charityRaffle': "Some stuff", 'agreeToRules': True,
				'breakfast': True, 'switch': False,
				'buttonOffer': "Buttons", 'asstbreakfast': True},
                    'priceLevel': {'id': self.price2.id, 'options': [{'id': self.option1.id, 'value': "true"}]},
                'event': 'Test Event 2050!'}

        response = self.client.post(reverse('addDealer'), json.dumps(postData), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse('invoiceDealer'))
        self.assertEqual(response.status_code, 200)
        cart = response.context["orderItems"]
        self.assertEqual(len(cart), 1)
        total = response.context["total"]
        self.assertEqual(total, 90+45+45+60+160-45-5)

        #Dealer, partners+breakfast, upgrade, wifi, discount, donations
        postData = {'billingData': {
			'cc_number': "4111111111111111", 'cc_month': "01", 
			'cc_year': "2018", 'cc_security': "836",
			'cc_firstname': "Test", 'cc_lastname': "Credit", 'email': "thing@some.com",
                        'address1': "123 Somewhere", 'address2': "", 'city': "There",
                        'state': "PA", 'country': "USA", 'postal': "12345",
		    },
		    'charityDonation': "10",
		    'orgDonation': "5"}
        response = self.client.post(reverse('checkoutDealer'), json.dumps(postData), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        orderItem = badge.orderitem_set.first()
        self.assertNotEqual(orderItem.order, None)
        order = orderItem.order
        self.assertNotEqual(order.discount, None)
        self.assertEqual(order.total, 90+45+45+60+160-45-5+15)
        self.assertEqual(order.orgDonation, 5.00)
        self.assertEqual(order.charityDonation, 10.00)

        response = self.client.get(reverse('flush'))
        self.assertEqual(response.status_code, 200)



class LookupTestCases(TestCase):
    def setUp(self):
        shirt1 = ShirtSizes(name='Test_Large')
        shirt2 = ShirtSizes(name='Test_Small')
        shirt1.save()
        shirt2.save()

        dept1 = Department(name='Reg',volunteerListOk=True)
        dept2 = Department(name='Safety')
        dept3 = Department(name='Charity',volunteerListOk=True)
        dept1.save()
        dept2.save()
        dept3.save()


    def test_shirts(self):
        client = Client()
        response = client.get(reverse('shirtsizes'))
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertEqual(result.__len__(), 2)
        large = [item for item in result if item['name'] == 'Test_Large']
        self.assertNotEqual(large, [])

    def test_departments(self):
        client = Client()
        response = client.get(reverse('departments'))
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertEqual(result.__len__(), 2)
        reg = [item for item in result if item['name'] == 'Reg']
        self.assertNotEqual(reg, [])
        safety = [item for item in result if item['name'] == 'Safety']
        self.assertEqual(safety, [])

       
