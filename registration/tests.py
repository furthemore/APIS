from datetime import timedelta
from django.utils import timezone
from django.core.urlresolvers import reverse
from django.test import TestCase, Client
from .models import *


class OrdersTestCases(TestCase):
    def setUp(self):
        now = timezone.now()
        ten_days = timedelta(days=10)
        price1 = PriceLevel(name='Basic', description='Some test description here', basePrice=40.00, 
                            startDate=now-ten_days, endDate=now+ten_days, public=True)
        price2 = PriceLevel(name='Super', description='Woot!', basePrice=80.00, 
                            startDate=now-ten_days, endDate=now+ten_days, public=True)
        price3 = PriceLevel(name='Later', description='In the future', basePrice=120.00, 
                            startDate=now+ten_days, endDate=now+ten_days+ten_days, public=True)
        price4 = PriceLevel(name='Special', description='ooOOOoooooo', basePrice=100.00, 
                            startDate=now-ten_days, endDate=now+ten_days, public=False)
        price1.save()
        price2.save()
        price3.save()
        price4.save()

        shirt1 = ShirtSizes(name='Test_Large')
        shirt1.save()

	#TODO: shirt option type
        option1 = PriceLevelOption(priceLevel=price1,optionName="Conbook",optionPrice=0.00)
        option2 = PriceLevelOption(priceLevel=price1,optionName="Shirt Size",optionPrice=0.00,optionExtraType="ShirtSizes")

	option1.save()
	option2.save()

	discount = Discount(codeName='FiveOff', amountOff=5.00, startDate=now-ten_days, endDate=now+ten_days)
	discount.save()

        event = Event(name="Test Event 2050!")
        event.save()


    def test_getprices(self):
        client = Client()
        response = client.get(reverse('pricelevels'))
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertEqual(result.__len__(), 2)
        basic = [item for item in result if item['name'] == 'Basic']
        self.assertEqual(basic[0]['base_price'], '40.00')
        special = [item for item in result if item['name'] == 'Special']
        self.assertEqual(special, [])

    def test_fullsingleorder(self):
        client = Client()
        priceLevel = PriceLevel.objects.first()
        option = priceLevel.priceleveloption_set.first()
        option2 = priceLevel.priceleveloption_set.last()
        shirt = ShirtSizes.objects.first()
        discount = Discount.objects.first()
        postData = {'attendee': {'firstName': "Tester", 'lastName': "Testerson",
                                 'address1': "123 Somewhere St",'address2': "",'city': "Place",'state': "PA",'country': "USA",'postal': "12345",
                                 'phone': "1112223333",'email': "testerson@mailinator.org",'birthdate': "01/01/1990",
                                 'badgeName': "FluffyButz",'emailsOk': "true",'volunteer': "false",'volDepts': ""},
                    'priceLevel': {'id': priceLevel.id, 'options': [{'id': option.id, 'value': "true"}, {'id': option2.id, 'value': shirt.id}]},
                    'discount': discount.codeName}
	
        response = client.post(reverse('addToCart'), json.dumps(postData), content_type="application/json")
        self.assertEqual(response.status_code, 200)

	attendee = Attendee.objects.get(firstName="Tester")
	self.assertEqual(attendee.lastName, "Testerson")
	orderitem = OrderItem.objects.get(attendee=attendee)
	self.assertEqual(orderitem.priceLevel_id, priceLevel.id)
	self.assertEqual(orderitem.enteredBy, "WEB")
        self.assertNotEqual(orderitem.confirmationCode, "")
        orderoption2 = orderitem.attendeeoptions_set.get(option__id=option2.id)
        self.assertEqual(orderoption2.optionValue, shirt.id.__str__())
        self.assertEqual(orderitem.discount, discount)
	

    def test_multipleorder(self):
        pass

    def test_discount(self):
        pass
        

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

       
