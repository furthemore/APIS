from django.conf.urls import url, include
from django.contrib.auth import views as auth_views
from django.conf import settings

from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),

    url(r'^logout/$', auth_views.logout, name='logout'),

    url(r'^upgrade/lookup/?$', views.findUpgrade, name='findUpgrade'),
    url(r'^upgrade/info/?$', views.infoUpgrade, name='infoUpgrade'),
    url(r'^upgrade/add/?$', views.addUpgrade, name='addUpgrade'),
    url(r'^upgrade/invoice/?$', views.invoiceUpgrade, name='invoiceUpgrade'),
    url(r'^upgrade/checkout/?$', views.checkoutUpgrade, name='checkoutUpgrade'),
    url(r'^upgrade/done/?$', views.doneUpgrade, name='doneUpgrade'),
    url(r'^upgrade/(?P<guid>\w+)/?$', views.upgrade, name='upgrade'),

    url(r'^staff/done/?$', views.staffDone, name='doneStaff'),
    url(r'^staff/lookup/?$', views.findStaff, name='findStaff'),
    url(r'^staff/info/?$', views.infoStaff, name='infoStaff'),
    url(r'^staff/add/?$', views.addStaff, name='addStaff'),
    url(r'^staff/(?P<guid>\w+)/?$', views.staff, name='staff'),

    url(r'^newstaff/done/?$', views.staffDone, name='doneNewStaff'),
    url(r'^newstaff/lookup/?$', views.findNewStaff, name='findNewStaff'),
    url(r'^newstaff/info/?$', views.infoNewStaff, name='infoNewStaff'),
    url(r'^newstaff/add/?$', views.addNewStaff, name='addNewStaff'),
    url(r'^newstaff/(?P<guid>\w+)/?$', views.newStaff, name='newstaff'),    

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
    url(r'^onsite/register/?$', views.onsiteAdmin, name='onsiteAdmin'),
    url(r'^onsite/register/search/?$', views.onsiteAdminSearch, name='onsiteAdminSearch'),
    url(r'^onsite/register/cart/?$', views.onsiteAdminCart, name='onsiteAdminCart'),
    url(r'^onsite/register/cart/add/?$', views.onsiteAddToCart, name='onsiteAddToCart'),
    url(r'^onsite/register/cart/remove/?$', views.onsiteRemoveFromCart, name='onsiteRemoveFromCart'),
    url(r'^onsite/register/open/?$', views.openTerminal, name='openTerminal'),
    url(r'^onsite/register/close/?$', views.closeTerminal, name='closeTerminal'),
    url(r'^onsite/register/payment/?$', views.enablePayment, name='enablePayment'),
    url(r'^onsite/register/clear/?$', views.onsiteAdminClearCart, name='onsiteAdminClearCart'),
    url(r'^onsite/register/badge/assign/?$', views.assignBadgeNumber, name='assignBadgeNumber'),
    url(r'^onsite/register/badge/print/?$', views.onsitePrintBadges, name='onsitePrintBadges'),
    url(r'^onsite/square/complete/?$', views.completeSquareTransaction, name='completeSquareTransaction'),
    url(r'^onsite/cash/complete/?$', views.completeCashTransaction, name='completeCashTransaction'),

    url(r'^onsite/signature/?$', views.onsiteSignature, name='onsiteSignature'),

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
    url(r'^adultpricelevels/?$', views.getAdultPriceLevels, name='adultpricelevels'),
    url(r'^minorpricelevels/?$', views.getMinorPriceLevels, name='minorpricelevels'),
    url(r'^accompaniedpricelevels/?$', views.getAccompaniedPriceLevels, name='accompaniedpricelevels'),
    url(r'^freepricelevels/?$', views.getFreePriceLevels, name='freepricelevels'),
    url(r'^shirts/?$', views.getShirtSizes, name='shirtsizes'),
    url(r'^tables/?$', views.getTableSizes, name='tablesizes'),
    url(r'^addresses/?$', views.getSessionAddresses, name='addresses'),

    url(r'^utility/badges?$', views.basicBadges, name='basicBadges'),
    url(r'^utility/vips?$', views.vipBadges, name='vipBadges'),

    url(r'^flush/?$', views.flush, name='flush'),

    url(r'^pdf/?$', views.servePDF, name='pdf'),
    url(r'^print/?$', views.printNametag, name='print'),

    url(r'^firebase/register/?', views.firebaseRegister, name='firebaseRegister'),
    url(r'^firebase/lookup/?', views.firebaseLookup, name='firebaseLookup'),

]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
