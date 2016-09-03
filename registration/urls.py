from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^cart/?$', views.getCart, name='cart'),
    url(r'^cart/add/?$', views.addToCart, name='addToCart'),
    url(r'^cart/remove/?$', views.removeFromCart, name='removeFromCart'),
    url(r'^cart/abandon/?$', views.cancelOrder, name='cancelOrder'),
    url(r'^cart/checkout/?$', views.checkout, name='checkout'),
    url(r'^departments/?$', views.getDepartments, name='departments'),
    url(r'^pricelevels/?$', views.getPriceLevels, name='pricelevels'),
    url(r'^shirts/?$', views.getShirtSizes, name='shirtsizes'),

]
