from django.conf.urls import url
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
import registration.views.webhooks

app_name = "registration"


def trigger_error(request):
    division_by_zero = 1 / 0
    return division_by_zero


urlpatterns = [
    url(r"^sentry-debug/", trigger_error),
    url(r"^$", registration.views.common.index, name="index"),
    url(r"^logout/$", LogoutView.as_view(), name="logout"),
    url(
        r"^upgrade/lookup/?$",
        registration.views.upgrade.find_upgrade,
        name="find_upgrade",
    ),
    url(
        r"^upgrade/info/?$",
        registration.views.upgrade.info_upgrade,
        name="info_upgrade",
    ),
    url(r"^upgrade/add/?$", registration.views.upgrade.add_upgrade, name="add_upgrade"),
    url(
        r"^upgrade/invoice/?$",
        registration.views.upgrade.invoice_upgrade,
        name="invoice_upgrade",
    ),
    url(
        r"^upgrade/checkout/?$",
        registration.views.upgrade.checkout_upgrade,
        name="checkout_upgrade",
    ),
    url(
        r"^upgrade/done/?$",
        registration.views.upgrade.done_upgrade,
        name="done_upgrade",
    ),
    url(
        r"^upgrade/(?P<guid>\w+)/?$", registration.views.upgrade.upgrade, name="upgrade"
    ),
    url(r"^staff/done/?$", registration.views.staff.staff_done, name="staff_done"),
    url(r"^staff/lookup/?$", registration.views.staff.find_staff, name="find_staff"),
    url(r"^staff/info/?$", registration.views.staff.info_staff, name="info_staff"),
    url(r"^staff/add/?$", registration.views.staff.add_staff, name="add_staff"),
    url(r"^staff/(?P<guid>\w+)/?$", registration.views.staff.staff_index, name="staff"),
    url(r"^newstaff/done/?$", registration.views.staff.staff_done, name="doneNewStaff"),
    url(
        r"^newstaff/lookup/?$",
        registration.views.staff.find_new_staff,
        name="find_new_staff",
    ),
    url(
        r"^newstaff/info/?$",
        registration.views.staff.info_new_staff,
        name="info_new_staff",
    ),
    url(
        r"^newstaff/add/?$",
        registration.views.staff.add_new_staff,
        name="add_new_staff",
    ),
    url(
        r"^newstaff/(?P<guid>\w+)/?$",
        registration.views.staff.new_staff,
        name="new_staff",
    ),
    url(r"^dealer/?$", registration.views.dealers.new_dealer, name="new_dealer"),
    url(
        r"^dealer/addNew/?$",
        registration.views.dealers.addNewDealer,
        name="addNewDealer",
    ),
    url(r"^dealer/done/?$", registration.views.dealers.done_dealer, name="done_dealer"),
    url(
        r"^dealer/thanks/?$",
        registration.views.dealers.thanks_dealer,
        name="thanks_dealer",
    ),
    url(
        r"^dealer/lookup/?$", registration.views.dealers.find_dealer, name="find_dealer"
    ),
    url(r"^dealer/add/?$", registration.views.dealers.add_dealer, name="add_dealer"),
    url(r"^dealer/info/?$", registration.views.dealers.info_dealer, name="info_dealer"),
    url(
        r"^dealer/invoice/?$",
        registration.views.dealers.invoice_dealer,
        name="invoice_dealer",
    ),
    url(
        r"^dealer/checkout/?$",
        registration.views.dealers.checkout_dealer,
        name="checkout_dealer",
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
        registration.views.dealers.dealer_asst,
        name="dealer_asst",
    ),
    url(
        r"^dealerassistant/add/find/?$",
        registration.views.dealers.find_asst_dealer,
        name="find_asst_dealer",
    ),
    url(
        r"^dealerassistant/add/done/?$",
        registration.views.dealers.done_asst_dealer,
        name="done_asst_dealer",
    ),
    url(r"^onsite/?$", registration.views.onsite.onsite, name="onsite"),
    url(r"^onsite/cart/?$", registration.views.onsite.onsite_cart, name="onsite_cart"),
    url(r"^onsite/done/?$", registration.views.onsite.onsite_done, name="onsite_done"),
    url(
        r"^onsite/admin/?$",
        registration.views.onsite_admin.onsite_admin,
        name="onsite_admin",
    ),
    url(
        r"^onsite/admin/search/?$",
        registration.views.onsite_admin.onsite_admin_search,
        name="onsite_admin_search",
    ),
    url(
        r"^onsite/admin/cart/?$",
        registration.views.onsite_admin.onsite_admin_cart,
        name="onsite_admin_cart",
    ),
    url(
        r"^onsite/admin/cart/add/?$",
        registration.views.onsite_admin.onsite_add_to_cart,
        name="onsite_add_to_cart",
    ),
    url(
        r"^onsite/admin/cart/remove/?$",
        registration.views.onsite_admin.onsite_remove_from_cart,
        name="onsite_remove_from_cart",
    ),
    url(
        r"^onsite/admin/open/?$",
        registration.views.onsite_admin.open_terminal,
        name="open_terminal",
    ),
    url(
        r"^onsite/admin/close/?$",
        registration.views.onsite_admin.close_terminal,
        name="close_terminal",
    ),
    url(
        r"^onsite/admin/ready/?$",
        registration.views.onsite_admin.ready_terminal,
        name="ready_terminal",
    ),
    url(
        r"^onsite/admin/payment/?$",
        registration.views.onsite_admin.enable_payment,
        name="enable_payment",
    ),
    url(
        r"^onsite/admin/clear/?$",
        registration.views.onsite_admin.onsite_admin_clear_cart,
        name="onsite_admin_clear_cart",
    ),
    url(
        r"^onsite/admin/badge/assign/?$",
        registration.views.onsite_admin.assign_badge_number,
        name="assign_badge_number",
    ),
    url(
        r"^onsite/admin/badge/print/?$",
        registration.views.onsite_admin.onsite_print_badges,
        name="onsite_print_badges",
    ),
    url(
        r"^onsite/admin/badge/print/clear/?$",
        registration.views.onsite_admin.onsite_print_clear,
        name="onsite_print_clear",
    ),
    url(
        r"^onsite/square/complete/?$",
        registration.views.onsite_admin.complete_square_transaction,
        name="complete_square_transaction",
    ),
    url(
        r"^onsite/cash/complete/?$",
        registration.views.onsite_admin.complete_cash_transaction,
        name="complete_cash_transaction",
    ),
    url(
        r"^onsite/cashdrawer/status/?$",
        registration.views.onsite_admin.drawer_status,
        name="drawer_status",
    ),
    url(
        r"^onsite/cashdrawer/open/?$",
        registration.views.onsite_admin.open_drawer,
        name="open_drawer",
    ),
    url(
        r"^onsite/cashdrawer/deposit/?$",
        registration.views.onsite_admin.cash_deposit,
        name="cash_deposit",
    ),
    url(
        r"^onsite/cashdrawer/safedrop/?$",
        registration.views.onsite_admin.safe_drop,
        name="safe_drop",
    ),
    url(
        r"^onsite/cashdrawer/pickup/?$",
        registration.views.onsite_admin.cash_pickup,
        name="cash_pickup",
    ),
    url(
        r"^onsite/cashdrawer/close/?$",
        registration.views.onsite_admin.close_drawer,
        name="close_drawer",
    ),
    url(
        r"^onsite/cashdrawer/no_sale/?$",
        registration.views.onsite_admin.no_sale,
        name="no_sale",
    ),
    url(
        r"^onsite/admin/discount/create/?$",
        registration.views.onsite_admin.create_discount,
        name="onsite_create_discount",
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
    url(r"^shirts/?$", registration.views.common.get_shirt_sizes, name="shirtsizes"),
    url(r"^tables/?$", registration.views.dealers.getTableSizes, name="tablesizes"),
    url(
        r"^addresses/?$",
        registration.views.common.get_session_addresses,
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
        registration.views.onsite_admin.firebase_register,
        name="firebase_register",
    ),
    url(
        r"^firebase/lookup/?",
        registration.views.onsite_admin.firebase_lookup,
        name="firebase_lookup",
    ),
    url(
        r"webhook/square/v2",
        registration.views.webhooks.square_webhook,
        name="square_webhook",
    ),
]
