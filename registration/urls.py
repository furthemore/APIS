from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^staff/done/?$', views.staffDone, name='staff'),
    url(r'^staff/lookup/?$', views.findStaff, name='findStaff'),
    url(r'^staff/add/?$', views.addStaff, name='addStaff'),
    url(r'^staff/info/?$', views.infoStaff, name='infoStaff'),
    url(r'^staff/invoice/?$', views.invoiceStaff, name='invoiceStaff'),
    url(r'^staff/checkout/?$', views.checkoutStaff, name='checkoutStaff'),
    url(r'^staff/(?P<guid>\w+)/?$', views.staff, name='staff'),

    url(r'^dealer/?$', views.newDealer, name='newDealer'),
    url(r'^dealer/addNew/?$', views.addNewDealer, name='addNewDealer'),
    url(r'^dealer/done/?$', views.doneDealer, name='doneDealer'),
    url(r'^dealer/thanks/?$', views.thanksDealer, name='thanksDealer'),
    url(r'^dealer/update/?$', views.updateDealer, name='updateDealer'),
    url(r'^dealer/lookup/?$', views.findDealer, name='findDealer'),
    url(r'^dealer/add/?$', views.addDealer, name='addDealer'),
    url(r'^dealer/info/?$', views.infoDealer, name='infoDealer'),
    url(r'^dealer/invoice/?$', views.invoiceDealer, name='invoiceDealer'),
    url(r'^dealer/checkout/?$', views.checkoutDealer, name='checkoutDealer'),
    url(r'^dealer/(?P<guid>\w+)/?$', views.dealers, name='dealers'),
    
    url(r'^cart/?$', views.getCart, name='cart'),
    url(r'^cart/add/?$', views.addToCart, name='addToCart'),
    url(r'^cart/remove/?$', views.removeFromCart, name='removeFromCart'),
    url(r'^cart/abandon/?$', views.cancelOrder, name='cancelOrder'),
    url(r'^cart/discount/?$', views.applyDiscount, name='discount'),
    url(r'^cart/checkout/?$', views.checkout, name='checkout'),
    url(r'^cart/done/?$', views.cartDone, name='done'),

    url(r'^jersey/lookup/?$', views.lookupJersey, name='lookupjersey'),    
    url(r'^jersey/add/?$', views.addJersey, name='addjersey'),    
    url(r'^jersey/checkout/?$', views.checkoutJersey, name='checkoutjersey'),    
    url(r'^jersey/done/?$', views.doneJersey, name='donejersey'),    
    url(r'^jersey/(?P<guid>\w+)/?$', views.getJersey, name='jersey'),    

    url(r'^events/?$', views.getEvents, name='events'),
    url(r'^departments/?$', views.getDepartments, name='departments'),
    url(r'^alldepartments/?$', views.getAllDepartments, name='alldepartments'),
    url(r'^pricelevels/?$', views.getPriceLevels, name='pricelevels'),
    url(r'^shirts/?$', views.getShirtSizes, name='shirtsizes'),
    url(r'^tables/?$', views.getTableSizes, name='tablesizes'),
    url(r'^addresses/?$', views.getSessionAddresses, name='addresses'),
    url(r'^takenJerseys/?$', views.getJerseyNumbers, name='takenJerseys'),
    url(r'^takenStaffJerseys/?$', views.getJerseyNumbers, name='takenStaffJerseys'),

    url(r'^flush/?$', views.flush, name='flush'),

]
