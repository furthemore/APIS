from django.conf import settings
from django.conf.urls import include, url
from django.contrib.auth.views import LogoutView

import registration.views.attendee
import registration.views.cart
import registration.views.common
import registration.views.dealers
import registration.views.onsite
import registration.views.onsite_admin
import registration.views.ordering
import registration.views.printing
import registration.views.staff
import registration.views.upgrade

app_name = "registration"


def trigger_error(request):
    division_by_zero = 1 / 0


urlpatterns = [
    url(r"^sentry-debug/", trigger_error),
    url(r"^$", registration.views.common.index, name="index"),
    url(r"^logout/$", LogoutView.as_view(), name="logout"),
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
        r"^dealer/(?P<guid>\w+)/assistants/?$",
        registration.views.dealers.find_dealer_to_add_assistant,
        name="find_dealer_to_add_assistant",
    ),
    url(
        r"^dealer/assistants/lookup/?$",
        registration.views.dealers.find_dealer_to_add_assistant_post,
        name="find_dealer_to_add_assistant_post",
    ),
    url(
        r"^dealer/assistants/add/?$",
        registration.views.dealers.add_assistants,
        name="add_assistants",
    ),
    url(
        r"^dealer/assistants/checkout/?$",
        registration.views.dealers.add_assistants_checkout,
        name="add_assistants_checkout",
    ),
    url(
        r"^dealerassistant/(?P<guid>\w+)/?$",
        registration.views.dealers.dealerAsst,
        name="dealerAsst",
    ),
    url(
        r"^dealerassistant/add/find/?$",
        registration.views.dealers.findAsstDealer,
        name="findAsstDealer",
    ),
    url(
        r"^dealerassistant/add/done/?$",
        registration.views.dealers.doneAsstDealer,
        name="doneAsstDealer",
    ),
    url(r"^onsite/?$", registration.views.onsite.onsite, name="onsite"),
    url(r"^onsite/cart/?$", registration.views.onsite.onsite_cart, name="onsite_cart"),
    url(r"^onsite/done/?$", registration.views.onsite.onsite_done, name="onsite_done"),
    url(
        r"^onsite/admin/?$",
        registration.views.onsite_admin.onsiteAdmin,
        name="onsiteAdmin",
    ),
    url(
        r"^onsite/admin/search/?$",
        registration.views.onsite_admin.onsiteAdminSearch,
        name="onsiteAdminSearch",
    ),
    url(
        r"^onsite/admin/cart/?$",
        registration.views.onsite_admin.onsiteAdminCart,
        name="onsiteAdminCart",
    ),
    url(
        r"^onsite/admin/cart/add/?$",
        registration.views.onsite_admin.onsiteAddToCart,
        name="onsiteAddToCart",
    ),
    url(
        r"^onsite/admin/cart/remove/?$",
        registration.views.onsite_admin.onsiteRemoveFromCart,
        name="onsiteRemoveFromCart",
    ),
    url(
        r"^onsite/admin/open/?$",
        registration.views.onsite_admin.openTerminal,
        name="openTerminal",
    ),
    url(
        r"^onsite/admin/close/?$",
        registration.views.onsite_admin.closeTerminal,
        name="closeTerminal",
    ),
    url(
        r"^onsite/admin/payment/?$",
        registration.views.onsite_admin.enablePayment,
        name="enablePayment",
    ),
    url(
        r"^onsite/admin/clear/?$",
        registration.views.onsite_admin.onsiteAdminClearCart,
        name="onsiteAdminClearCart",
    ),
    url(
        r"^onsite/admin/badge/assign/?$",
        registration.views.onsite_admin.assignBadgeNumber,
        name="assignBadgeNumber",
    ),
    url(
        r"^onsite/admin/badge/print/?$",
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
        r"^onsite/cashdrawer/status/?$",
        registration.views.onsite_admin.drawerStatus,
        name="drawerStatus",
    ),
    url(
        r"^onsite/cashdrawer/open/?$",
        registration.views.onsite_admin.openDrawer,
        name="openDrawer",
    ),
    url(
        r"^onsite/cashdrawer/deposit/?$",
        registration.views.onsite_admin.cashDeposit,
        name="cashDeposit",
    ),
    url(
        r"^onsite/cashdrawer/safedrop/?$",
        registration.views.onsite_admin.safeDrop,
        name="safeDrop",
    ),
    url(
        r"^onsite/cashdrawer/pickup/?$",
        registration.views.onsite_admin.cashPickup,
        name="cashPickup",
    ),
    url(
        r"^onsite/cashdrawer/close/?$",
        registration.views.onsite_admin.closeDrawer,
        name="closeDrawer",
    ),
    url(
        r"^onsite/signature/?$",
        registration.views.onsite_admin.onsiteSignature,
        name="onsiteSignature",
    ),
    url(
        r"^onsite/admin/signature/?$",
        registration.views.onsite_admin.onsiteSignaturePrompt,
        name="onsiteSignaturePrompt",
    ),
    url(r"^cart/?$", registration.views.cart.get_cart, name="cart"),
    url(r"^cart/add/?$", registration.views.cart.add_to_cart, name="add_to_cart"),
    url(
        r"^cart/remove/?$",
        registration.views.cart.remove_from_cart,
        name="remove_from_cart",
    ),
    url(
        r"^cart/abandon/?$",
        registration.views.ordering.cancel_order,
        name="cancel_order",
    ),
    url(
        r"^cart/discount/?$",
        registration.views.ordering.apply_discount,
        name="discount",
    ),
    url(r"^cart/checkout/?$", registration.views.ordering.checkout, name="checkout"),
    url(r"^cart/done/?$", registration.views.cart.cart_done, name="done"),
    url(r"^events/?$", registration.views.common.get_events, name="events"),
    url(
        r"^departments/?$",
        registration.views.common.get_departments,
        name="departments",
    ),
    url(
        r"^alldepartments/?$",
        registration.views.common.get_all_departments,
        name="alldepartments",
    ),
    url(
        r"^pricelevels/?$",
        registration.views.attendee.get_price_levels,
        name="pricelevels",
    ),
    url(
        r"^adultpricelevels/?$",
        registration.views.attendee.get_adult_price_levels,
        name="adultpricelevels",
    ),
    url(
        r"^minorpricelevels/?$",
        registration.views.attendee.get_minor_price_levels,
        name="minorpricelevels",
    ),
    url(
        r"^accompaniedpricelevels/?$",
        registration.views.attendee.get_accompanied_price_levels,
        name="accompaniedpricelevels",
    ),
    url(
        r"^freepricelevels/?$",
        registration.views.attendee.get_free_price_levels,
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
