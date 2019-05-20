from datetime import datetime, timedelta
from django.utils import timezone
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test.utils import override_settings
from django.test import TestCase, Client
from django.conf import settings
from unittest import skip
import logging
import json

from .models import *

logger = logging.getLogger(__name__)
logging.disable(logging.NOTSET)
logger.setLevel(logging.DEBUG)
        
tz = timezone.get_current_timezone()
now = tz.localize(datetime.now())
ten_days = timedelta(days=10)

DEFAULT_EVENT_ARGS = dict(
    default=True,
    name="Test Event 2050!",
    dealerRegStart=now-ten_days, dealerRegEnd=now+ten_days,
    staffRegStart=now-ten_days, staffRegEnd=now+ten_days,
    attendeeRegStart=now-ten_days, attendeeRegEnd=now+ten_days,
    onlineRegStart=now-ten_days, onlineRegEnd=now+ten_days,
    eventStart=now-ten_days, eventEnd=now+ten_days,
)

class DebugURLTrigger(TestCase):
    @override_settings(DEBUG=True)
    def test_debug(self):
        assert settings.DEBUG

class Index(TestCase):
    def setUp(self):
        self.client = Client()
   
    # unit tests skip methods that start with uppercase letters
    def TestIndex(self):
        response = self.client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Welcome to the registration system')
   
    def TestIndexClosed(self):
        response = self.client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'is closed. If you have any')

    def TestIndexNoEvent(self):
        response = self.client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'no default event was found')

    # this one runs
    def test_index(self):
        self.TestIndexNoEvent()
        self.event = Event(**DEFAULT_EVENT_ARGS)
        self.event.save()
        self.TestIndex()
        self.event.attendeeRegEnd = now - ten_days
        self.event.save()
        self.TestIndexClosed()

class OrdersTestCases(TestCase):
    def setUp(self):
        self.price_minor_25 = PriceLevel(name='Minor', description='I am a Minor!', basePrice=25.00,
                            startDate=now-ten_days, endDate=now+ten_days, public=True, isMinor=True)
        self.price_45 = PriceLevel(name='Attendee', description='Some test description here', basePrice=45.00,
                            startDate=now-ten_days, endDate=now+ten_days, public=True)
        self.price_90 = PriceLevel(name='Sponsor', description='Woot!', basePrice=90.00,
                            startDate=now-ten_days, endDate=now+ten_days, public=True)
        self.price_150 = PriceLevel(name='Super', description='In the future', basePrice=150.00,
                            startDate=now+ten_days, endDate=now+ten_days+ten_days, public=True)
        self.price_235 = PriceLevel(name='Elite', description='ooOOOoooooo', basePrice=235.00,
                            startDate=now-ten_days, endDate=now+ten_days, public=False)
        self.price_675 = PriceLevel(name='Raven God', description='yay', basePrice=675.00,
                            startDate=now-ten_days, endDate=now+ten_days, public=False,
                            emailVIP=True, emailVIPEmails='apis@mailinator.com' )
        self.price_minor_25.save()
        self.price_45.save()
        self.price_90.save()
        self.price_150.save()
        self.price_235.save()
        self.price_675.save()

        self.department1 = Department(name="BestDept")
        self.department2 = Department(name="WorstDept")
        self.department1.save()
        self.department2.save()

        self.discount = Discount(codeName="FiveOff", amountOff=5.00, startDate=now, endDate=now+ten_days)
        self.onetimediscount = Discount(codeName="OneTime", percentOff=10, oneTime=True, startDate=now, endDate=now+ten_days)
        self.staffdiscount = Discount(codeName="StaffDiscount", amountOff=45.00, startDate=now, endDate=now+ten_days)
        self.dealerdiscount = Discount(codeName="DealerDiscount", amountOff=45.00, startDate=now, endDate=now+ten_days)
        self.discount.save()
        self.onetimediscount.save()
        self.staffdiscount.save()
        self.dealerdiscount.save()

        self.shirt1 = ShirtSizes(name='Test_Large')
        self.shirt1.save()

        #TODO: shirt option type
        self.option_conbook = PriceLevelOption(optionName="Conbook",optionPrice=0.00,optionExtraType="bool")
        self.option_shirt = PriceLevelOption(optionName="Shirt Size",optionPrice=0.00,optionExtraType="ShirtSizes")
        self.option_100_int = PriceLevelOption(optionName="Something Pricy",optionPrice=100.00,optionExtraType="int")

        self.option_conbook.save()
        self.option_shirt.save()
        self.option_100_int.save()

        self.price_45.priceLevelOptions.add(self.option_conbook)
        self.price_45.priceLevelOptions.add(self.option_shirt)
        self.price_90.priceLevelOptions.add(self.option_conbook)
        self.price_150.priceLevelOptions.add(self.option_conbook)
        self.price_150.priceLevelOptions.add(self.option_100_int)

        self.event = Event(**DEFAULT_EVENT_ARGS)
        self.event.staffDiscount = self.staffdiscount
        self.event.dealerDiscount = self.dealerdiscount
        self.event.save()

        self.table_130 = TableSize(name="Booth", description="description here", chairMin=0, chairMax=1,
                                tableMin=0, tableMax=1, partnerMin=0, partnerMax=1, basePrice=Decimal(130))
        self.table_160 = TableSize(name="Booth", description="description here", chairMin=0, chairMax=1,
                                tableMin=0, tableMax=1, partnerMin=0, partnerMax=2, basePrice=Decimal(160))
       
        self.table_130.save()
        self.table_160.save()

        self.attendee_regular_1 = {'firstName': "Tester", 'lastName': "Testerson", 'address1': "123 Somewhere St",'address2': "",'city': "Place",
                                 'state': "PA",'country': "US",'postal': "12345", 'phone': "1112223333",'email': "apis@mailinator.org",
                                 'birthdate': "1990-01-01",'asl': "false", 'badgeName': "FluffyButtz",'emailsOk': "true",
                                 'volunteer': "false",'volDepts': "", 'surveyOk': "false"}
        self.attendee_regular_2 = {'firstName': "Bea", 'lastName': "Testerson", 'address1': "123 Somewhere St", 'address2': "Ste 300", 'city': "Place",
                                 'state': "PA", 'country': "US", 'postal': "12345", 'phone': "1112223333", 'email': "apis@mailinator.com",
                                 'birthdate': "1990-01-01", 'asl': "false", 'badgeName': "FluffyButz", 'emailsOk': "true", 
                                 'volunteer': "false", 'volDepts': "", 'surveyOk': "false"}


        self.client = Client()

    def test_get_prices(self):
        response = self.client.get(reverse('pricelevels'))
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertEqual(result.__len__(), 3)
        basic = [item for item in result if item['name'] == 'Attendee']
        self.assertEqual(basic[0]['base_price'], '45.00')
        special = [item for item in result if item['name'] == 'Special']
        self.assertEqual(special, [])
        minor = [item for item in result if item['name'] == 'Minor']
        self.assertEqual(minor.__len__(), 1)

    def test_get_adult_prices(self):
        response = self.client.get(reverse('adultpricelevels'))
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertEqual(result.__len__(), 2)
        basic = [item for item in result if item['name'] == 'Attendee']
        self.assertEqual(basic[0]['base_price'], '45.00')
        special = [item for item in result if item['name'] == 'Special']
        self.assertEqual(special, [])
        minor = [item for item in result if item['name'] == 'Minor']
        self.assertEqual(minor, [])



    # Single transaction tests
    # =======================================================================

    def test_checkout(self):
        options = [{'id': self.option_conbook.id, 'value': "true"}, {'id': self.option_shirt.id, 'value': self.shirt1.id}]
        self.add_to_cart(self.attendee_regular_2, self.price_45, options)

        response = self.client.get(reverse('cart'))
        self.assertEqual(response.status_code, 200)
        cart = response.context["orderItems"]
        self.assertEqual(len(cart), 1)
        total = response.context["total"]
        self.assertEqual(total, 45)

        response = self.checkout('fake-card-nonce-ok', '20', '10')
        self.assertEqual(response.status_code, 200)
        
        # Check that user was succesfully saved
        attendee = Attendee.objects.get(firstName='Bea')
        badge = Badge.objects.get(attendee=attendee,event=self.event)
        self.assertNotEqual(badge.registeredDate, None)
        self.assertEqual(badge.orderitem_set.count(), 1)
        orderItem = badge.orderitem_set.first()
        self.assertNotEqual(orderItem.order, None)
       
        order = badge.getOrder()
        self.assertEqual(order.discount, None)
        self.assertEqual(order.total, 45+10+20)
        self.assertEqual(attendee.postalCode, order.billingPostal)
        self.assertEqual(order.orgDonation, 20)
        self.assertEqual(order.charityDonation, 10)

        # Square should overwrite this with a random sandbox value
        self.assertNotEqual(order.lastFour, '1111')
        self.assertNotEqual(order.lastFour, '')
        self.assertNotEqual(order.notes, '')
        self.assertNotEqual(order.apiData, '')

        # Clean up
        badge.delete()

    def test_zero_checkout(self):
        # TODO
        pass

    def assertSquareError(self, nonce, error): 
        self.add_to_cart(self.attendee_regular_2, self.price_45, [])
        result = self.checkout(nonce)
        self.assertEqual(result.status_code, 400)

        message = result.json()
        error_codes = [ err['code'] for err in message['reason']['errors'] ]
        logger.error(error_codes)
        self.assertIn(error, error_codes)

        # Ensure a badge wasn't created
        self.assertEqual(Attendee.objects.filter(firstName='Bea').count(), 0) 
    
    def test_bad_cvv(self):
        self.assertSquareError('fake-card-nonce-rejected-cvv', 'VERIFY_CVV_FAILURE')
    
    def test_bad_postalcode(self):
        self.assertSquareError('fake-card-nonce-rejected-postalcode', 'VERIFY_AVS_FAILURE')

    def test_bad_expiration(self):
        self.assertSquareError('fake-card-nonce-rejected-expiration', 'INVALID_EXPIRATION')

    def test_card_declined(self):
        self.assertSquareError('fake-card-nonce-declined', 'CARD_DECLINED')

    def test_nonce_already_used(self):
        self.assertSquareError('fake-card-nonce-already-used', 'CARD_TOKEN_USED')

    def add_to_cart(self, attendee, priceLevel, options):
        postData = {'attendee': attendee,
                    'priceLevel':
                        {'id': priceLevel.id,
                         'options': options},
                    'event': self.event.name}

        response = self.client.post(reverse('addToCart'), json.dumps(postData), content_type="application/json")
        logging.info(response.content)
        self.assertEqual(response.status_code, 200)

    def zero_checkout(self):
        postData = {}
        response = self.client.post(reverse('checkout'), json.dumps(postData), content_type="application/json")
        return response

    def checkout(self, nonce, orgDonation='', charityDonation=''):
        postData = {'billingData': 
                        {'address1': '123 Any Street',
                         'address2': 'Apt 4',
                         'card_data': {'billing_postal_code': '12345',
                                       'card_brand': 'VISA',
                                       'digital_wallet_type': 'NONE',
                                       'exp_month': 2,
                                       'exp_year': 2020,
                                       'last_4': '1111'},
                         'cc_firstname': 'Buffy',
                         'cc_lastname': 'Cleveland',
                         'city': '39535',
                         'country': 'ST',
                         'email': 'apis@mailinator.net',
                         'nonce': nonce,
                         'postal': '45733',
                         'state': 'ID'},
         'charityDonation': charityDonation,
         'onsite': False,
         'orgDonation': orgDonation}

        response = self.client.post(reverse('checkout'), json.dumps(postData), content_type="application/json")

        return response

    def test_full_single_order(self):
        options = [{'id': self.option_conbook.id, 'value': "true"}, {'id': self.option_shirt.id, 'value': self.shirt1.id}]

        self.add_to_cart(self.attendee_regular_1, self.price_45, options)

        response = self.client.get(reverse('cart'))
        self.assertEqual(response.status_code, 200)
        cart = response.context["orderItems"]
        self.assertEqual(len(cart), 1)
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
        self.assertEqual(PriceLevel.objects.filter(id=self.price_45.id).count(), 1)

    def test_vip_checkout(self):
        self.add_to_cart(self.attendee_regular_2, self.price_675, [])

        response = self.client.get(reverse('cart'))
        self.assertEqual(response.status_code, 200)
        cart = response.context["orderItems"]
        self.assertEqual(len(cart), 1)
        total = response.context["total"]
        self.assertEqual(total, 675)

        response = self.checkout('fake-card-nonce-ok', '1', '10')
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
        options = [{'id': self.option_conbook.id, 'value': "true"}, {'id': self.option_shirt.id, 'value': self.shirt1.id}]
        self.add_to_cart(self.attendee_regular_2, self.price_45, options)

        response = self.client.get(reverse('cart'))
        self.assertEqual(response.status_code, 200)
        cart = response.context["orderItems"]
        self.assertEqual(len(cart), 1)
        total = response.context["total"]
        self.assertEqual(total, 45)

        postData = {'discount': 'OneTime'}
        response = self.client.post(reverse('discount'), json.dumps(postData), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse('cart'))
        self.assertEqual(response.status_code, 200)
        cart = response.context["orderItems"]
        self.assertEqual(len(cart), 1)
        total = response.context["total"]
        self.assertEqual(total, 40.50)

        response = self.checkout('fake-card-nonce-ok', '1', '10')
        self.assertEqual(response.status_code, 200)

        discount = Discount.objects.get(codeName='OneTime')
        self.assertEqual(discount.used, 1)

        postData = {'discount': 'OneTime'}
        response = self.client.post(reverse('discount'), json.dumps(postData), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content), {"message": "That discount is not valid.", "success": False})

        postData = {'discount': 'Bogus'}
        response = self.client.post(reverse('discount'), json.dumps(postData), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content), {"message": "That discount is not valid.", "success": False})


    def test_discount_zero_sum(self):
        options = [{'id': self.option_conbook.id, 'value': "true"}]
        self.add_to_cart(self.attendee_regular_2, self.price_45, options)

        response = self.client.get(reverse('cart'))
        self.assertEqual(response.status_code, 200)
        cart = response.context["orderItems"]
        self.assertEqual(len(cart), 1)
        total = response.context["total"]
        self.assertEqual(total, 45)

        postData = {'discount': 'StaffDiscount'}
        response = self.client.post(reverse('discount'), json.dumps(postData), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse('cart'))
        self.assertEqual(response.status_code, 200)
        cart = response.context["orderItems"]
        self.assertEqual(len(cart), 1)
        total = response.context["total"]
        self.assertEqual(total, 0)

        discount = Discount.objects.get(codeName='StaffDiscount')
        discountUsed = discount.used

        response = self.zero_checkout()
        self.assertEqual(response.status_code, 200)

        discount = Discount.objects.get(codeName='StaffDiscount')
        self.assertEqual(discount.used, discountUsed+1)

    def test_new_staff(self):
        pass

    def test_promote_staff(self):
        pass

    def test_staff(self):
        attendee = Attendee(firstName="Staffer", lastName="Testerson",
                            address1="123 Somewhere St", city="Place", state="PA", country="US", postalCode=12345,
                            phone="1112223333", email="apis@mailinator.org", birthdate="1990-01-01")
        attendee.save()
        staff = Staff(attendee=attendee,event=self.event)
        staff.save()
        badge = Badge(attendee=attendee,event=self.event,badgeName="DisStaff")
        badge.save()
        attendee2 = Attendee(firstName="Staph", lastName="Testerson", 
                            address1="123 Somewhere St", city="Place", state="PA", country="US", postalCode=12345,
                            phone="1112223333", email="apis@mailinator.org", birthdate="1990-01-01")
        attendee2.save()
        staff2 = Staff(attendee=attendee2,event=self.event)
        staff2.save()
        badge2 = Badge(attendee=attendee2,event=self.event,badgeName="AnotherStaff")
        badge2.save()

        # Failed lookup
        postData = {'email': 'nottherightemail@somewhere.com', 'token':staff.registrationToken}
        response = self.client.post(reverse('findStaff'), json.dumps(postData), content_type="application/json")
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.content, 'Staff matching query does not exist.')

        # Regular staff reg
        postData = {'email':attendee.email, 'token':staff.registrationToken}
        response = self.client.post(reverse('findStaff'), json.dumps(postData), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content), {"message": "STAFF", "success": True})

        postData = {'attendee': {'id': attendee.id,'firstName': "Staffer", 'lastName': "Testerson",
                                 'address1': "123 Somewhere St",'address2': "",'city': "Place",'state': "PA",'country': "US",'postal': "12345",
                                 'phone': "1112223333",'email': "apis@mailinator.com",'birthdate': "1990-01-01",
                                 'badgeName': "FluffyButz",'emailsOk': "true"},
                    'staff': {'id': staff.id, 
                    'department': self.department1.id, 'title': 'Something Cool',
                    'twitter': "@twitstaff", 'telegram': "@twitstaffagain",
                    'shirtsize': self.shirt1.id, 'specialSkills': "Something here",
                    'specialFood': "no water please", 'specialMedical': 'alerigic to bandaids',
                    'contactPhone': "4442223333", 'contactName': 'Test Testerson',
                    'contactRelation': 'Pet'},
                    'priceLevel': {'id': self.price_150.id, 'options': [{'id': self.option_100_int.id, 'value': 1}, {'id': self.option_shirt.id, 'value': self.shirt1.id}]},
                    'event': self.event.name
                    }
        response = self.client.post(reverse('addStaff'), json.dumps(postData), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse('cart'))
        self.assertEqual(response.status_code, 200)
        cart = response.context["orderItems"]
        self.assertEqual(len(cart), 1)
        total = response.context["total"]
        self.assertEqual(total, 150+100-45)
        discount = response.context["discount"]
        self.assertEqual(discount.codeName, "StaffDiscount")
        discountUsed = discount.used

        response = self.checkout('fake-card-nonce-ok')
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
        self.assertEqual(order.discount.used, discountUsed+1)

        response = self.client.get(reverse('flush'))
        self.assertEqual(response.status_code, 200)

        # Staff zero-sum
        postData = {'email':attendee2.email, 'token':staff2.registrationToken}
        response = self.client.post(reverse('findStaff'), json.dumps(postData), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content), {"message": "STAFF", "success": True})

        postData = {'attendee': {'id': attendee2.id,'firstName': "Staffer", 'lastName': "Testerson",
                                 'address1': "123 Somewhere St",'address2': "",'city': "Place",'state': "PA",'country': "US",'postal': "12345",
                                 'phone': "1112223333",'email': "carissa.brittain@gmail.com",'birthdate': "1990-01-01",
                                 'badgeName': "FluffyButz",'emailsOk': "true"},
                    'staff': {'id': staff2.id, 
                    'department': self.department2.id, 'title': 'Something Cool',
                    'twitter': "@twitstaff", 'telegram': "@twitstaffagain",
                    'shirtsize': self.shirt1.id, 'specialSkills': "Something here",
                    'specialFood': "no water please", 'specialMedical': 'alerigic to bandaids',
                    'contactPhone': "4442223333", 'contactName': 'Test Testerson',
                    'contactRelation': 'Pet'},
                    'priceLevel': {'id': self.price_45.id, 'options': [{'id': self.option_conbook.id, 'value': "true"}, {'id': self.option_shirt.id, 'value': self.shirt1.id}]},
                    'event': self.event.name
                    }
        response = self.client.post(reverse('addStaff'), json.dumps(postData), content_type="application/json")
        self.assertEqual(response.status_code, 200)

        response = self.client.get(reverse('cart'))
        self.assertEqual(response.status_code, 200)
        cart = response.context["orderItems"]
        self.assertEqual(len(cart), 1)
        total = response.context["total"]
        self.assertEqual(total, 45-45)
        discount = response.context["discount"]
        self.assertEqual(discount.codeName, "StaffDiscount")
        discountUsed = discount.used

        response = self.zero_checkout()
        self.assertEqual(response.status_code, 200)

        badge = Badge.objects.get(attendee=attendee2, event=self.event)
        orderItem = OrderItem.objects.get(badge=badge)
        self.assertNotEqual(orderItem.order, None)
        order = orderItem.order
        self.assertEqual(order.discount.codeName, "StaffDiscount")
        self.assertEqual(order.total, 0)
        self.assertEqual(order.discount.used, discountUsed+1)

        response = self.client.get(reverse('flush'))
        self.assertEqual(response.status_code, 200)


    def test_dealer(self):
        dealer_pay = {'attendee': {'firstName': "Dealer", 'lastName': "Testerson",
                                 'address1': "123 Somewhere St",'address2': "",'city': "Place",'state': "PA",'country': "US",'postal': "12345",
                                 'phone': "1112223333",'email': "testerson@mailinator.org",'birthdate': "1990-01-01",
                                 'badgeName': "FluffyButz",'emailsOk': "true", 'surveyOk': "true"},
                    'dealer': {'businessName':"Something Creative", 'website':"http://www.something.com", 'logo':"",
                        'license':"jkah9435kd", 'power': False, 'wifi': False,
                        'wall': True, 'near': "Someone", 'far': "Someone Else",
                        'description': "Stuff for sale", 'tableSize': self.table_130.id,
                        'chairs': 1, 'partners': [], 'tables': 0,
                        'reception': True, 'artShow': False,
                        'charityRaffle': "Some stuff", 'agreeToRules': True,
                        'breakfast': True, 'switch': False,
                        'buttonOffer': "Buttons", 'asstbreakfast': False},
                    'event': self.event.name}

        response = self.client.post(reverse('addNewDealer'), json.dumps(dealer_pay), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        dealer_free = {'attendee': {'firstName': "Free", 'lastName': "Testerson",
                                 'address1': "123 Somewhere St",'address2': "",'city': "Place",'state': "PA",'country': "US",'postal': "12345",
                                 'phone': "1112223333",'email': "testerson@mailinator.org",'birthdate': "1990-01-01",
                                 'badgeName': "FluffyNutz",'emailsOk': "true", 'surveyOk': "true"},
                'dealer': {'businessName':"Something Creative", 'website':"http://www.something.com", "logo": "",
                    'license':"jkah9435kd", 'power': True, 'wifi': True,
                    'wall': True, 'near': "Someone", 'far': "Someone Else",
                    'description': "Stuff for sale", 'tableSize': self.table_130.id,
                    'chairs': 1, 'partners': [], 'tables': 0,
                    'reception': True, 'artShow': False,
                    'charityRaffle': "Some stuff", 'agreeToRules': True,
                    'breakfast': True, 'switch': False,
                    'buttonOffer': "Buttons", 'asstbreakfast': False},
                'event': self.event.name}

        response = self.client.post(reverse('addNewDealer'), json.dumps(dealer_free), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        dealer_partners = {'attendee': {'firstName': "Dealz", 'lastName': "Testerson",
                                 'address1': "123 Somewhere St",'address2': "",'city': "Place",'state': "PA",'country': "US",'postal': "12345",
                                 'phone': "1112223333",'email': "testerson@mailinator.org",'birthdate': "1990-01-01",
                                 'badgeName': "FluffyGutz",'emailsOk': "true", 'surveyOk': "true"},
                'dealer': {'businessName':"Something Creative", 'website':"http://www.something.com", "logo": "",
                    'license':"jkah9435kd", 'power': True, 'wifi': True,
                    'wall': True, 'near': "Someone", 'far': "Someone Else",
                    'description': "Stuff for sale", 'tableSize': self.table_160.id,
                    'partners': [{"name": "Someone", "email": "someone@here.com", "license": "temporary", "tempLicense": True},
                                 {"name": "", "email": "", "license": "", "tempLicense": False}],
                    'chairs':1, 'tables': 0,
                    'reception': False, 'artShow': False,
                    'charityRaffle': "Some stuff", 'agreeToRules': True,
                    'breakfast': True, 'switch': False,
                    'buttonOffer': "Buttons", 'asstbreakfast': False},
                'event': self.event.name}

        response = self.client.post(reverse('addNewDealer'), json.dumps(dealer_partners), content_type="application/json")
        self.assertEqual(response.status_code, 200)

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
        dealer = Dealer.objects.get(attendee=attendee)
        self.assertNotEqual(dealer, None)

        attendee = Attendee.objects.get(firstName='Free')
        badge = Badge.objects.get(attendee=attendee,event=self.event)
        self.assertEqual(badge.badgeName, "FluffyNutz")
        self.assertNotEqual(badge.registeredDate, None)
        dealer = Dealer.objects.get(attendee=attendee)
        self.assertNotEqual(dealer, None)

        response = self.client.get(reverse('flush'))
        self.assertEqual(response.status_code, 200)

        #Dealer
        attendee = Attendee.objects.get(firstName='Dealer')
        badge = Badge.objects.get(attendee=attendee, event=self.event)
        dealer = Dealer.objects.get(attendee=attendee)
        postData = {'token': dealer.registrationToken, 'email': attendee.email}
        response = self.client.post(reverse('findDealer'), json.dumps(postData), content_type="application/json")
        self.assertEqual(response.status_code, 200)

        dealer_pay['attendee']['id'] = attendee.id
        dealer_pay['dealer']['id'] = dealer.id
        dealer_pay['priceLevel'] = {'id': self.price_45.id, 'options': []}

        response = self.client.post(reverse('addDealer'), json.dumps(dealer_pay), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse('invoiceDealer'))
        self.assertEqual(response.status_code, 200)
        cart = response.context["orderItems"]
        self.assertEqual(len(cart), 1)
        total = response.context["total"]
   #     self.assertEqual(total, 45+130-45)
   #     orderItem = OrderItem.objects.get(badge=badge)
   #     orderItem.delete()

   #     response = self.client.get(reverse('flush'))
   #     self.assertEqual(response.status_code, 200)

    #    #Dealer, zero-sum
    #    attendee = Attendee.objects.get(firstName='Free')
    #    badge = Badge.objects.get(attendee=attendee, event=self.event)
    #    dealer = Dealer.objects.get(attendee=attendee)
    #    dealer.discount = 130
    #    dealer.save()
    #    postData = {'token': dealer.registrationToken, 'email': attendee.email}
    #    response = self.client.post(reverse('findDealer'), json.dumps(postData), content_type="application/json")
    #    self.assertEqual(response.status_code, 200)
    #    postData = {'attendee': {'id': attendee.id,'firstName': "Free", 'lastName': "Testerson",
    #                             'address1': "123 Somewhere St",'address2': "",'city': "Place",'state': "PA",'country': "US",'postal': "12345",
    #                             'phone': "1112223333",'email': "testerson@mailinator.org",'birthdate': "1990-01-01",
    #                             'badgeName': "FluffyNutz",'emailsOk': "true"},
    #            'dealer': {'id': dealer.id,'businessName':"Something Creative", 'website':"http://www.something.com",
    #            'license':"jkah9435kd", 'power': True, 'wifi': False,
    #            'wall': True, 'near': "Someone", 'far': "Someone Else",
    #            'description': "Stuff for sale", 'tableSize': self.table_130.id,  
    #            'chairs': 1, 'partners': "name_1: , email_1: , license_1: , tempLicense_1: false,", 'tables': 0,
    #            'reception': True, 'artShow': False, 
    #            'charityRaffle': "Some stuff", 'agreeToRules': True,
    #            'breakfast': True, 'switch': False,
    #            'buttonOffer': "Buttons", 'asstbreakfast': False},
    #            'priceLevel': {'id': self.price_45.id, 'options': [{'id': self.option_conbook.id, 'value': "true"}]},
    #            'event': 'Test Event 2050!'}
    #                
    #    response = self.client.post(reverse('addDealer'), json.dumps(postData), content_type="application/json")
    #    self.assertEqual(response.status_code, 200)
    #    response = self.client.get(reverse('invoiceDealer'))
    #    self.assertEqual(response.status_code, 200)
    #    cart = response.context["orderItems"]
    #    self.assertEqual(len(cart), 1)
    #    total = response.context["total"]
    #    self.assertEqual(total, 0)
    #    orderItem = OrderItem.objects.get(badge=badge)
    #    orderItem.delete()

    #    response = self.client.get(reverse('flush'))
    #    self.assertEqual(response.status_code, 200)

    #    #Dealer, upgrade, Wifi
    #    attendee = Attendee.objects.get(firstName='Dealer')
    #    badge = Badge.objects.get(attendee=attendee, event=self.event)
    #    dealer = Dealer.objects.get(attendee=attendee)
    #    postData = {'token': dealer.registrationToken, 'email': attendee.email}
    #    response = self.client.post(reverse('findDealer'), json.dumps(postData), content_type="application/json")
    #    self.assertEqual(response.status_code, 200)
    #    postData = {'attendee': {'id': attendee.id,'firstName': "Dealer", 'lastName': "Testerson",
    #                             'address1': "123 Somewhere St",'address2': "",'city': "Place",'state': "PA",'country': "US",'postal': "12345",
    #                             'phone': "1112223333",'email': "testerson@mailinator.org",'birthdate': "1990-01-01",
    #                             'badgeName': "FluffyButz",'emailsOk': "true"},
    #            'dealer': {'id': dealer.id,'businessName':"Something Creative", 'website':"http://www.something.com",
    #            'license':"jkah9435kd", 'power': True, 'wifi': True,
    #            'wall': True, 'near': "Someone", 'far': "Someone Else",
    #            'description': "Stuff for sale", 'tableSize': self.table_130.id,  
    #            'chairs': 1, 'partners': "name_1: , email_1: , license_1: , tempLicense_1: false,", 'tables': 0,
    #            'reception': True, 'artShow': False, 
    #            'charityRaffle': "Some stuff", 'agreeToRules': True,
    #            'breakfast': True, 'switch': False,
    #            'buttonOffer': "Buttons", 'asstbreakfast': False},
    #            'priceLevel': {'id': self.price_90.id, 'options': [{'id': self.option_conbook.id, 'value': "true"}]},
    #            'event': 'Test Event 2050!'}
    #                
    #    response = self.client.post(reverse('addDealer'), json.dumps(postData), content_type="application/json")
    #    self.assertEqual(response.status_code, 200)
    #    response = self.client.get(reverse('invoiceDealer'))
    #    self.assertEqual(response.status_code, 200)
    #    cart = response.context["orderItems"]
    #    self.assertEqual(len(cart), 1)
    #    total = response.context["total"]
    #    self.assertEqual(total, 90+130+50-45)
    #    orderItem = OrderItem.objects.get(badge=badge)
    #    orderItem.delete()

    #    response = self.client.get(reverse('flush'))
    #    self.assertEqual(response.status_code, 200)

    #    #Dealer, partners, upgrade, wifi
    #    attendee = Attendee.objects.get(firstName='Dealz')
    #    badge = Badge.objects.get(attendee=attendee, event=self.event)
    #    dealer = Dealer.objects.get(attendee=attendee)
    #    postData = {'token': dealer.registrationToken, 'email': attendee.email}
    #    response = self.client.post(reverse('findDealer'), json.dumps(postData), content_type="application/json")
    #    self.assertEqual(response.status_code, 200)
    #    postData = {'attendee': {'id': attendee.id, 'firstName': "Dealz", 'lastName': "Testerson",
    #                             'address1': "123 Somewhere St",'address2': "",'city': "Place",'state': "PA",'country': "US",'postal': "12345",
    #                             'phone': "1112223333",'email': "testerson@mailinator.org",'birthdate': "1990-01-01",
    #                             'badgeName': "FluffyButz",'emailsOk': "true"},
    #            'dealer': {'id': dealer.id, 'businessName':"Something Creative", 'website':"http://www.something.com",
    #            'license':"jkah9435kd", 'power': True, 'wifi': True,
    #            'wall': True, 'near': "Someone", 'far': "Someone Else",
    #            'description': "Stuff for sale", 'tableSize': self.table_160.id,  
    #            'chairs': 1, 'partners': "name_1: Someone, email_1: someone@here.com, license_1: temporary, tempLicense_1: true, name_2: , email_2: , license_2: , tempLicense_2: false", 'tables': 0,
    #            'reception': False, 'artShow': False, 
    #            'charityRaffle': "Some stuff", 'agreeToRules': True,
    #            'breakfast': False, 'switch': False,
    #            'buttonOffer': "Buttons", 'asstbreakfast': False},
    #            'priceLevel': {'id': self.price_90.id, 'options': [{'id': self.option_conbook.id, 'value': "true"}]},
    #            'event': 'Test Event 2050!'}

    #    response = self.client.post(reverse('addDealer'), json.dumps(postData), content_type="application/json")
    #    self.assertEqual(response.status_code, 200)
    #    response = self.client.get(reverse('invoiceDealer'))
    #    self.assertEqual(response.status_code, 200)
    #    cart = response.context["orderItems"]
    #    self.assertEqual(len(cart), 1)
    #    total = response.context["total"]
    #    self.assertEqual(total, 90+45+50+160-45)
    #    orderItem = OrderItem.objects.get(badge=badge)
    #    orderItem.delete()

    #    response = self.client.get(reverse('flush'))
    #    self.assertEqual(response.status_code, 200)

    #    #Dealer, partners+breakfast, upgrade, discount, wifi
    #    attendee = Attendee.objects.get(firstName='Dealz')
    #    badge = Badge.objects.get(attendee=attendee, event=self.event)
    #    dealer = Dealer.objects.get(attendee=attendee)
    #    dealer.discount = 5
    #    dealer.save()
    #    postData = {'token': dealer.registrationToken, 'email': attendee.email}
    #    response = self.client.post(reverse('findDealer'), json.dumps(postData), content_type="application/json")
    #    self.assertEqual(response.status_code, 200)
    #    postData = {'attendee': {'id': attendee.id, 'firstName': "Dealz", 'lastName': "Testerson",
    #                             'address1': "123 Somewhere St",'address2': "",'city': "Place",'state': "PA",'country': "US",'postal': "12345",
    #                             'phone': "1112223333",'email': "testerson@mailinator.org",'birthdate': "1990-01-01",
    #                             'badgeName': "FluffyButz",'emailsOk': "true"},
    #            'dealer': {'id': dealer.id, 'businessName':"Something Creative", 'website':"http://www.something.com",
    #            'license':"jkah9435kd", 'power': True, 'wifi': True,
    #            'wall': True, 'near': "Someone", 'far': "Someone Else",
    #            'description': "Stuff for sale", 'tableSize': self.table_160.id,  
    #            'chairs': 1, 'partners': "name_1: Someone, email_1: someone@here.com, license_1: temporary, tempLicense_1: true, name_2: , email_2: , license_2: , tempLicense_2: false", 'tables': 0,
    #            'reception': False, 'artShow': False, 
    #            'charityRaffle': "Some stuff", 'agreeToRules': True,
    #            'breakfast': True, 'switch': False,
    #            'buttonOffer': "Buttons", 'asstbreakfast': True},
    #            'priceLevel': {'id': self.price_90.id, 'options': [{'id': self.option_conbook.id, 'value': "true"}]},
    #            'event': 'Test Event 2050!'}

    #    response = self.client.post(reverse('addDealer'), json.dumps(postData), content_type="application/json")
    #    self.assertEqual(response.status_code, 200)
    #    response = self.client.get(reverse('invoiceDealer'))
    #    self.assertEqual(response.status_code, 200)
    #    cart = response.context["orderItems"]
    #    self.assertEqual(len(cart), 1)
    #    total = response.context["total"]
    #    self.assertEqual(total, 90+45+60+50+160-45-5)

    #    #Dealer, partners+breakfast, upgrade, wifi, discount, donations
    #    postData = {'billingData': {
    #            'nonce': 'fake-card-nonce-ok', 
    #            'cc_firstname': "Test", 'cc_lastname': "Credit", 'email': "thing@some.com",
    #            'address1': "123 Somewhere", 'address2': "", 'city': "There",
    #            'state': "PA", 'country': "US", 'postal': "12345",
    #        },
    #        'charityDonation': "10",
    #        'orgDonation': "5"}
    #    response = self.client.post(reverse('checkoutDealer'), json.dumps(postData), content_type="application/json")
    #    self.assertEqual(response.status_code, 200)
    #    orderItem = badge.orderitem_set.first()
    #    self.assertNotEqual(orderItem.order, None)
    #    order = orderItem.order
    #    self.assertNotEqual(order.discount, None)
    #    self.assertEqual(order.total, 90+45+60+50+160-45-5+15)
    #    self.assertEqual(order.orgDonation, 5.00)
    #    self.assertEqual(order.charityDonation, 10.00)

    #    response = self.client.get(reverse('flush'))
    #    self.assertEqual(response.status_code, 200)



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

class Onsite(TestCase):
    def setUp(self):
        # Create some users
        self.admin_user = User.objects.create_superuser('admin', 'admin@host', 'admin')
        self.admin_user.save()
        self.normal_user = User.objects.create_user('john', 'lennon@thebeatles.com', 'john')
        self.normal_user.save()

        # Create some test terminals to push notifications to
        self.terminal = Firebase(token="test", name="Terminal 1")
        self.terminal.save()

        # At least one event always mandatory
        self.event = Event(**DEFAULT_EVENT_ARGS)
        self.event.save()

        self.client = Client()

    def test_onsite_login_required(self):
        self.client.logout()
        response = self.client.get(reverse('onsiteAdmin'), follow=True)
        self.assertRedirects(response, '/admin/login/?next={0}'.format(reverse('onsiteAdmin')))

    def TEST_onsite_admin_required(self):
        # FIXME: always gets a 200
        self.assertTrue(self.client.login(username='john', password='john'))
        response = self.client.get(reverse('onsiteAdmin'), follow=True)
        self.assertEqual(response.status_code, 401)
        self.client.logout()

    def test_onsite_admin(self):
        self.client.logout()
        self.assertTrue(self.client.login(username='admin', password='admin'))
        response = self.client.get(reverse('onsiteAdmin'), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['errors']), 0)
        self.assertEqual(len(response.context['terminals']), 1)

        self.terminal.delete()
        response = self.client.get(reverse('onsiteAdmin'))
        self.assertEqual(response.status_code, 200)
        errors = [ e['code'] for e in response.context['errors'] ]
        #import pdb; pdb.set_trace()
        self.assertIn('ERROR_NO_TERMINAL', errors)

        self.terminal = Firebase(token="test", name="Terminal 1")
        self.terminal.save()
        response = self.client.get(
            reverse('onsiteAdmin'),
            { 'search' : 'doesntexist' }
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('results', response.context.keys())
        self.assertEqual(len(response.context['results']), 0)

        self.client.logout()

