from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^test/?$', views.testForm, name='testForm'),

    url(r'^upgrade/lookup/?$', views.findUpgrade, name='findUpgrade'),
    url(r'^upgrade/info/?$', views.infoUpgrade, name='infoUpgrade'),
    url(r'^upgrade/add/?$', views.addUpgrade, name='addUpgrade'),
    url(r'^upgrade/invoice/?$', views.invoiceUpgrade, name='invoiceUpgrade'),
    url(r'^upgrade/checkout/?$', views.checkoutUpgrade, name='checkoutUpgrade'),
    url(r'^upgrade/done/?$', views.doneUpgrade, name='doneUpgrade'),
    url(r'^upgrade/(?P<guid>\w+)/?$', views.upgrade, name='upgrade'),

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

    url(r'^dealerassistant/lookup/?$', views.findAsstDealer, name='findAsstDealer'),
    url(r'^dealerassistant/add/?$', views.addAsstDealer, name='addAsstDealer'),
    url(r'^dealerassistant/checkout/?$', views.checkoutAsstDealer, name='checkoutAsstDealer'),
    url(r'^dealerassistant/done/?$', views.doneAsstDealer, name='doneAsstDealer'),
    url(r'^dealerassistant/(?P<guid>\w+)/?$', views.dealerAsst, name='dealerAsst'),

    url(r'^onsite/?$', views.onsite, name='onsite'),
    url(r'^onsite/cart/?$', views.onsiteCart, name='onsiteCart'),
    url(r'^onsite/done/?$', views.onsiteDone, name='onsiteDone'),
    
    url(r'^cart/?$', views.getCart, name='cart'),
    url(r'^cart/add/?$', views.addToCart, name='addToCart'),
    url(r'^cart/remove/?$', views.removeFromCart, name='removeFromCart'),
    url(r'^cart/abandon/?$', views.cancelOrder, name='cancelOrder'),
    url(r'^cart/discount/?$', views.applyDiscount, name='discount'),
    url(r'^cart/checkout/?$', views.checkout, name='checkout'),
    url(r'^cart/done/?$', views.cartDone, name='done'),

    url(r'^events/?$', views.getEvents, name='events'),
    url(r'^departments/?$', views.getDepartments, name='departments'),
    url(r'^alldepartments/?$', views.getAllDepartments, name='alldepartments'),
    url(r'^pricelevels/?$', views.getPriceLevels, name='pricelevels'),
    url(r'^minorpricelevels/?$', views.getMinorPriceLevels, name='minorpricelevels'),
    url(r'^accompaniedpricelevels/?$', views.getAccompaniedPriceLevels, name='accompaniedpricelevels'),
    url(r'^freepricelevels/?$', views.getFreePriceLevels, name='freepricelevels'),
    url(r'^shirts/?$', views.getShirtSizes, name='shirtsizes'),
    url(r'^tables/?$', views.getTableSizes, name='tablesizes'),
    url(r'^addresses/?$', views.getSessionAddresses, name='addresses'),

#    url(r'^utility/badges?$', views.badgeList, name='badgeList'),

    url(r'^flush/?$', views.flush, name='flush'),

    url(r'^pdf/?$', views.servePDF, name='pdf'),
    url(r'^print/?$', views.printNametag, name='print'),
]
