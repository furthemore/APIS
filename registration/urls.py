from django.conf import settings
from django.conf.urls import include, url
from django.contrib.auth import views as auth_views

import registration.views.attendee
import registration.views.cart
import registration.views.common
import registration.views.dealers
import registration.views.onsite
import registration.views.onsite_admin
import registration.views.orders
import registration.views.printing
import registration.views.staff
import registration.views.upgrade

from . import views

urlpatterns = [
    url(r"^$", registration.views.common.index, name="index"),
    url(r"^logout/$", auth_views.logout, name="logout"),
    url(
        r"^upgrade/lookup/?$",
        registration.views.upgrade.findUpgrade,
        name="findUpgrade",
    ),
    url(
        r"^upgrade/info/?$", registration.views.upgrade.infoUpgrade, name="infoUpgrade"
    ),
    url(r"^upgrade/add/?$", registration.views.upgrade.addUpgrade, name="addUpgrade"),
    url(
        r"^upgrade/invoice/?$",
        registration.views.upgrade.invoiceUpgrade,
        name="invoiceUpgrade",
    ),
    url(
        r"^upgrade/checkout/?$",
        registration.views.upgrade.checkoutUpgrade,
        name="checkoutUpgrade",
    ),
    url(
        r"^upgrade/done/?$", registration.views.upgrade.doneUpgrade, name="doneUpgrade"
    ),
    url(
        r"^upgrade/(?P<guid>\w+)/?$", registration.views.upgrade.upgrade, name="upgrade"
    ),
    url(r"^staff/done/?$", registration.views.staff.staffDone, name="doneStaff"),
    url(r"^staff/lookup/?$", registration.views.staff.findStaff, name="findStaff"),
    url(r"^staff/info/?$", registration.views.staff.infoStaff, name="infoStaff"),
    url(r"^staff/add/?$", registration.views.staff.addStaff, name="addStaff"),
    url(r"^staff/(?P<guid>\w+)/?$", registration.views.staff.staff, name="staff"),
    url(r"^newstaff/done/?$", registration.views.staff.staffDone, name="doneNewStaff"),
    url(
        r"^newstaff/lookup/?$",
        registration.views.staff.findNewStaff,
        name="findNewStaff",
    ),
    url(
        r"^newstaff/info/?$", registration.views.staff.infoNewStaff, name="infoNewStaff"
    ),
    url(r"^newstaff/add/?$", registration.views.staff.addNewStaff, name="addNewStaff"),
    url(
        r"^newstaff/(?P<guid>\w+)/?$",
        registration.views.staff.newStaff,
        name="newstaff",
    ),
    url(r"^dealer/?$", registration.views.dealers.newDealer, name="newDealer"),
    url(
        r"^dealer/addNew/?$",
        registration.views.dealers.addNewDealer,
        name="addNewDealer",
    ),
    url(r"^dealer/done/?$", registration.views.dealers.doneDealer, name="doneDealer"),
    url(
        r"^dealer/thanks/?$",
        registration.views.dealers.thanksDealer,
        name="thanksDealer",
    ),
    url(
        r"^dealer/update/?$",
        registration.views.dealers.updateDealer,
        name="updateDealer",
    ),
    url(r"^dealer/lookup/?$", registration.views.dealers.findDealer, name="findDealer"),
    url(r"^dealer/add/?$", registration.views.dealers.addDealer, name="addDealer"),
    url(r"^dealer/info/?$", registration.views.dealers.infoDealer, name="infoDealer"),
    url(
        r"^dealer/invoice/?$",
        registration.views.dealers.invoiceDealer,
        name="invoiceDealer",
    ),
    url(
        r"^dealer/checkout/?$",
        registration.views.dealers.checkoutDealer,
        name="checkoutDealer",
    ),
    url(
        r"^dealer/(?P<guid>\w+)/?$", registration.views.dealers.dealers, name="dealers"
    ),
    url(
        r"^dealerassistant/lookup/?$",
        registration.views.dealers.findAsstDealer,
        name="findAsstDealer",
    ),
    url(
        r"^dealerassistant/add/?$",
        registration.views.dealers.addAsstDealer,
        name="addAsstDealer",
    ),
    url(
        r"^dealerassistant/checkout/?$",
        registration.views.dealers.checkoutAsstDealer,
        name="checkoutAsstDealer",
    ),
    url(
        r"^dealerassistant/done/?$",
        registration.views.dealers.doneAsstDealer,
        name="doneAsstDealer",
    ),
    url(
        r"^dealerassistant/(?P<guid>\w+)/?$",
        registration.views.dealers.dealerAsst,
        name="dealerAsst",
    ),
    url(r"^onsite/?$", registration.views.onsite.onsite, name="onsite"),
    url(r"^onsite/cart/?$", registration.views.onsite.onsiteCart, name="onsiteCart"),
    url(r"^onsite/done/?$", registration.views.onsite.onsiteDone, name="onsiteDone"),
    url(
        r"^onsite/register/?$",
        registration.views.onsite_admin.onsiteAdmin,
        name="onsiteAdmin",
    ),
    url(
        r"^onsite/register/search/?$",
        registration.views.onsite_admin.onsiteAdminSearch,
        name="onsiteAdminSearch",
    ),
    url(
        r"^onsite/register/cart/?$",
        registration.views.onsite_admin.onsiteAdminCart,
        name="onsiteAdminCart",
    ),
    url(
        r"^onsite/register/cart/add/?$",
        registration.views.onsite_admin.onsiteAddToCart,
        name="onsiteAddToCart",
    ),
    url(
        r"^onsite/register/cart/remove/?$",
        registration.views.onsite_admin.onsiteRemoveFromCart,
        name="onsiteRemoveFromCart",
    ),
    url(
        r"^onsite/register/open/?$",
        registration.views.onsite_admin.openTerminal,
        name="openTerminal",
    ),
    url(
        r"^onsite/register/close/?$",
        registration.views.onsite_admin.closeTerminal,
        name="closeTerminal",
    ),
    url(
        r"^onsite/register/payment/?$",
        registration.views.onsite_admin.enablePayment,
        name="enablePayment",
    ),
    url(
        r"^onsite/register/clear/?$",
        registration.views.onsite_admin.onsiteAdminClearCart,
        name="onsiteAdminClearCart",
    ),
    url(
        r"^onsite/register/badge/assign/?$",
        registration.views.onsite_admin.assignBadgeNumber,
        name="assignBadgeNumber",
    ),
    url(
        r"^onsite/register/badge/print/?$",
        registration.views.onsite_admin.onsitePrintBadges,
        name="onsitePrintBadges",
    ),
    url(
        r"^onsite/square/complete/?$",
        registration.views.onsite_admin.completeSquareTransaction,
        name="completeSquareTransaction",
    ),
    url(
        r"^onsite/cash/complete/?$",
        registration.views.onsite_admin.completeCashTransaction,
        name="completeCashTransaction",
    ),
    url(
        r"^onsite/signature/?$",
        registration.views.onsite_admin.onsiteSignature,
        name="onsiteSignature",
    ),
    url(r"^cart/?$", registration.views.cart.getCart, name="cart"),
    url(r"^cart/add/?$", registration.views.cart.addToCart, name="addToCart"),
    url(
        r"^cart/remove/?$",
        registration.views.cart.removeFromCart,
        name="removeFromCart",
    ),
    url(r"^cart/discount/?$", registration.views.orders.applyDiscount, name="discount"),
    url(r"^cart/checkout/?$", registration.views.orders.checkout, name="checkout"),
    url(r"^cart/done/?$", registration.views.cart.cartDone, name="done"),
    url(r"^events/?$", registration.views.common.getEvents, name="events"),
    url(
        r"^departments/?$", registration.views.common.getDepartments, name="departments"
    ),
    url(
        r"^alldepartments/?$",
        registration.views.common.getAllDepartments,
        name="alldepartments",
    ),
    url(
        r"^pricelevels/?$",
        registration.views.attendee.getPriceLevels,
        name="pricelevels",
    ),
    url(
        r"^adultpricelevels/?$",
        registration.views.attendee.getAdultPriceLevels,
        name="adultpricelevels",
    ),
    url(
        r"^minorpricelevels/?$",
        registration.views.attendee.getMinorPriceLevels,
        name="minorpricelevels",
    ),
    url(
        r"^accompaniedpricelevels/?$",
        registration.views.attendee.getAccompaniedPriceLevels,
        name="accompaniedpricelevels",
    ),
    url(
        r"^freepricelevels/?$",
        registration.views.attendee.getFreePriceLevels,
        name="freepricelevels",
    ),
    url(r"^shirts/?$", registration.views.common.getShirtSizes, name="shirtsizes"),
    url(r"^tables/?$", registration.views.dealers.getTableSizes, name="tablesizes"),
    url(
        r"^addresses/?$",
        registration.views.common.getSessionAddresses,
        name="addresses",
    ),
    url(
        r"^utility/badges?$", registration.views.common.basicBadges, name="basicBadges"
    ),
    url(r"^utility/vips?$", registration.views.common.vipBadges, name="vipBadges"),
    url(r"^flush/?$", registration.views.common.flush, name="flush"),
    url(r"^pdf/?$", registration.views.printing.servePDF, name="pdf"),
    url(r"^print/?$", registration.views.printing.printNametag, name="print"),
    url(
        r"^firebase/register/?",
        registration.views.onsite_admin.firebaseRegister,
        name="firebaseRegister",
    ),
    url(
        r"^firebase/lookup/?",
        registration.views.onsite_admin.firebaseLookup,
        name="firebaseLookup",
    ),
]

if settings.DEBUG:
    import debug_toolbar

    urlpatterns = [url(r"^__debug__/", include(debug_toolbar.urls)),] + urlpatterns
