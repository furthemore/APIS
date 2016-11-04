from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^staff/(?P<guid>)/?$', views.staff, name='staff'),
    url(r'^dealer/?$', views.newDealer, name='newDealer'),
    url(r'^dealer/add/?$', views.addDealer, name='addDealer'),
    url(r'^dealer/thanks/?$', views.thanksDealer, name='thanksDealer'),
    url(r'^dealer/lookup/?$', views.findDealer, name='findDealer'),
    url(r'^dealer/invoice/?$', views.invoiceDealer, name='invoiceDealer'),
    url(r'^dealer/checkout/?$', views.checkoutDealer, name='checkoutDealer'),
    url(r'^dealer/(?P<guid>\w+)/?$', views.dealers, name='dealers'),
    
    url(r'^cart/?$', views.getCart, name='cart'),
    url(r'^cart/add/?$', views.addToCart, name='addToCart'),
    url(r'^cart/remove/?$', views.removeFromCart, name='removeFromCart'),
    url(r'^cart/abandon/?$', views.cancelOrder, name='cancelOrder'),
    url(r'^cart/checkout/?$', views.checkout, name='checkout'),

    url(r'^departments/?$', views.getDepartments, name='departments'),
    url(r'^pricelevels/?$', views.getPriceLevels, name='pricelevels'),
    url(r'^shirts/?$', views.getShirtSizes, name='shirtsizes'),
    url(r'^tables/?$', views.getTableSizes, name='tablesizes'),

]
