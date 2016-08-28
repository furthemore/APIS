from datetime import timedelta
from django.utils import timezone
from django.core.urlresolvers import reverse
from django.test import TestCase, Client
from .models import *


class OrdersTestCases(TestCase):
    def setUp(self):
        now = timezone.now()
        ten_days = timedelta(days=10)
        self.price1 = PriceLevel(name='Basic', description='Some test description here', basePrice=40.00, 
                            startDate=now-ten_days, endDate=now+ten_days, public=True)
        self.price2 = PriceLevel(name='Super', description='Woot!', basePrice=80.00, 
                            startDate=now-ten_days, endDate=now+ten_days, public=True)
        self.price3 = PriceLevel(name='Later', description='In the future', basePrice=120.00, 
                            startDate=now+ten_days, endDate=now+ten_days+ten_days, public=True)
        self.price4 = PriceLevel(name='Special', description='ooOOOoooooo', basePrice=100.00, 
                            startDate=now-ten_days, endDate=now+ten_days, public=False)
        self.price1.save()
        self.price2.save()
        self.price3.save()
        self.price4.save()

        self.shirt1 = ShirtSizes(name='Test_Large')
        self.shirt1.save()

	#TODO: shirt option type
        self.option1 = PriceLevelOption(priceLevel=self.price1,optionName="Conbook",optionPrice=0.00)
        self.option2 = PriceLevelOption(priceLevel=self.price1,optionName="Shirt Size",optionPrice=0.00,optionExtraType="ShirtSizes")
        self.option3 = PriceLevelOption(priceLevel=self.price2,optionName="Conbook",optionPrice=0.00)

	self.option1.save()
	self.option2.save()
	self.option3.save()

        self.event = Event(name="Test Event 2050!")
        self.event.save()
       
        self.client = Client()

    def test_getprices(self):
        response = self.client.get(reverse('pricelevels'))
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertEqual(result.__len__(), 2)
        basic = [item for item in result if item['name'] == 'Basic']
        self.assertEqual(basic[0]['base_price'], '40.00')
        special = [item for item in result if item['name'] == 'Special']
        self.assertEqual(special, [])

    def test_fullsingleorder(self):
        postData = {'attendee': {'firstName': "Tester", 'lastName': "Testerson",
                                 'address1': "123 Somewhere St",'address2': "",'city': "Place",'state': "PA",'country': "USA",'postal': "12345",
                                 'phone': "1112223333",'email': "testerson@mailinator.org",'birthdate': "01/01/1990",
                                 'badgeName': "FluffyButz",'emailsOk': "true",'volunteer': "false",'volDepts': ""},
                    'priceLevel': {'id': self.price1.id, 'options': [{'id': self.option1.id, 'value': "true"}, {'id': self.option2.id, 'value': self.shirt1.id}]}}
	
        response = self.client.post(reverse('addToCart'), json.dumps(postData), content_type="application/json")
        self.assertEqual(response.status_code, 200)

	attendee = Attendee.objects.get(firstName="Tester")
	self.assertEqual(attendee.lastName, "Testerson")
	orderitem = OrderItem.objects.get(attendee=attendee)
	self.assertEqual(orderitem.priceLevel_id, self.price1.id)
	self.assertEqual(orderitem.enteredBy, "WEB")
        self.assertNotEqual(orderitem.confirmationCode, "")
        orderoption2 = orderitem.attendeeoptions_set.get(option__id=self.option2.id)
        self.assertEqual(orderoption2.optionValue, self.shirt1.id.__str__())

        response = self.client.get(reverse('cart'))
	self.assertEqual(response.status_code, 200)
        cart = response.context["orderItems"]
        self.assertEqual(len(cart), 1)
        self.assertEqual(cart[0].id, orderitem.id)
        total = response.context["total"]
        self.assertEqual(total, 40.00)

	response = self.client.get(reverse('cancelOrder'))
	self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse('cart'))
	self.assertEqual(response.status_code, 200)
        cart = response.context["orderItems"]
        self.assertEqual(len(cart), 0)
        self.assertEqual(Attendee.objects.filter(firstName="Tester").count(), 0)
        self.assertEqual(OrderItem.objects.filter(id=orderitem.id).count(), 0)
        self.assertEqual(AttendeeOptions.objects.filter(orderItem=orderitem).count(), 0)
        self.assertEqual(PriceLevel.objects.filter(id=self.price1.id).count(), 1)

        

    def test_multipleorder(self):
        postData = {'attendee': {'firstName': "Frank", 'lastName': "Testerson",
                                 'address1': "123 Somewhere St",'address2': "",'city': "Place",'state': "PA",'country': "USA",'postal': "12345",
                                 'phone': "1112223333",'email': "testerson@mailinator.org",'birthdate': "01/01/1990",
                                 'badgeName': "FluffyButz",'emailsOk': "true",'volunteer': "false",'volDepts': ""},
                    'priceLevel': {'id': self.price1.id, 'options': [{'id': self.option1.id, 'value': "true"}, {'id': self.option2.id, 'value': self.shirt1.id}]}}
	
        response = self.client.post(reverse('addToCart'), json.dumps(postData), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        postData = {'attendee': {'firstName': "Felix", 'lastName': "Testerson",
                                 'address1': "123 Somewhere St",'address2': "",'city': "Place",'state': "PA",'country': "USA",'postal': "12345",
                                 'phone': "1112223333",'email': "testerson@mailinator.org",'birthdate': "01/01/1990",
                                 'badgeName': "FluffyButz",'emailsOk': "true",'volunteer': "false",'volDepts': ""},
                    'priceLevel': {'id': self.price2.id, 'options': [{'id': self.option3.id, 'value': "true"}]}}
	
        response = self.client.post(reverse('addToCart'), json.dumps(postData), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        postData = {'attendee': {'firstName': "Julie", 'lastName': "Testerson",
                                 'address1': "123 Somewhere St",'address2': "",'city': "Place",'state': "PA",'country': "USA",'postal': "12345",
                                 'phone': "1112223333",'email': "testerson@mailinator.org",'birthdate': "01/01/1990",
                                 'badgeName': "FluffyButz",'emailsOk': "true",'volunteer': "false",'volDepts': ""},
                    'priceLevel': {'id': self.price1.id, 'options': [{'id': self.option1.id, 'value': "true"}, {'id': self.option2.id, 'value': self.shirt1.id}]}}
	
        response = self.client.post(reverse('addToCart'), json.dumps(postData), content_type="application/json")
        self.assertEqual(response.status_code, 200)

        response = self.client.get(reverse('cart'))
	self.assertEqual(response.status_code, 200)
        cart = response.context["orderItems"]
        self.assertEqual(len(cart), 3)
        total = response.context["total"]
        self.assertEqual(total, 160.00)

	postData = {'id': Attendee.objects.get(firstName='Felix').id}
        response = self.client.post(reverse('removeFromCart'), json.dumps(postData), content_type='application/json')
	self.assertEqual(response.status_code, 200)

        response = self.client.get(reverse('cart'))
	self.assertEqual(response.status_code, 200)
        cart = response.context["orderItems"]
        self.assertEqual(len(cart), 2)
        total = response.context["total"]
        self.assertEqual(total, 80.00)
        self.assertEqual(Attendee.objects.filter(firstName="Felix").count(), 0)

        response = self.client.get(reverse('cancelOrder'))
	self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse('cart'))
	self.assertEqual(response.status_code, 200)
        cart = response.context["orderItems"]
        self.assertEqual(len(cart), 0)
        self.assertEqual(Attendee.objects.filter(firstName="Frank").count(), 0)
        self.assertEqual(Attendee.objects.filter(firstName="Julie").count(), 0)
        

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

       
