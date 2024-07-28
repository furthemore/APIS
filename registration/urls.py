from django.contrib.auth.views import LogoutView
from django.urls import include, re_path

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
    re_path(r"^sentry-debug/", trigger_error),
    re_path(r'^_nested_admin/', include('nested_admin.urls')),
    re_path(r"^$", registration.views.common.index, name="index"),
    re_path(r"^logout/$", LogoutView.as_view(), name="logout"),
    re_path(
        r"^upgrade/lookup/?$",
        registration.views.upgrade.find_upgrade,
        name="find_upgrade",
    ),
    re_path(
        r"^upgrade/info/?$",
        registration.views.upgrade.info_upgrade,
        name="info_upgrade",
    ),
    re_path(r"^upgrade/add/?$", registration.views.upgrade.add_upgrade, name="add_upgrade"),
    re_path(
        r"^upgrade/invoice/?$",
        registration.views.upgrade.invoice_upgrade,
        name="invoice_upgrade",
    ),
    re_path(
        r"^upgrade/checkout/?$",
        registration.views.upgrade.checkout_upgrade,
        name="checkout_upgrade",
    ),
    re_path(
        r"^upgrade/done/?$",
        registration.views.upgrade.done_upgrade,
        name="done_upgrade",
    ),
    re_path(
        r"^upgrade/(?P<guid>\w+)/?$", registration.views.upgrade.upgrade, name="upgrade"
    ),
    re_path(r"^staff/done/?$", registration.views.staff.staff_done, name="staff_done"),
    re_path(r"^staff/lookup/?$", registration.views.staff.find_staff, name="find_staff"),
    re_path(r"^staff/info/?$", registration.views.staff.info_staff, name="info_staff"),
    re_path(r"^staff/add/?$", registration.views.staff.add_staff, name="add_staff"),
    re_path(r"^staff/(?P<guid>\w+)/?$", registration.views.staff.staff_index, name="staff"),
    re_path(r"^newstaff/done/?$", registration.views.staff.staff_done, name="doneNewStaff"),
    re_path(
        r"^newstaff/lookup/?$",
        registration.views.staff.find_new_staff,
        name="find_new_staff",
    ),
    re_path(
        r"^newstaff/info/?$",
        registration.views.staff.info_new_staff,
        name="info_new_staff",
    ),
    re_path(
        r"^newstaff/add/?$",
        registration.views.staff.add_new_staff,
        name="add_new_staff",
    ),
    re_path(
        r"^newstaff/(?P<guid>\w+)/?$",
        registration.views.staff.new_staff,
        name="new_staff",
    ),
    re_path(r"^dealer/?$", registration.views.dealers.new_dealer, name="new_dealer"),
    re_path(
        r"^dealer/addNew/?$",
        registration.views.dealers.addNewDealer,
        name="addNewDealer",
    ),
    re_path(r"^dealer/done/?$", registration.views.dealers.done_dealer, name="done_dealer"),
    re_path(
        r"^dealer/thanks/?$",
        registration.views.dealers.thanks_dealer,
        name="thanks_dealer",
    ),
    re_path(
        r"^dealer/lookup/?$", registration.views.dealers.find_dealer, name="find_dealer"
    ),
    re_path(r"^dealer/add/?$", registration.views.dealers.add_dealer, name="add_dealer"),
    re_path(r"^dealer/info/?$", registration.views.dealers.info_dealer, name="info_dealer"),
    re_path(
        r"^dealer/invoice/?$",
        registration.views.dealers.invoice_dealer,
        name="invoice_dealer",
    ),
    re_path(
        r"^dealer/checkout/?$",
        registration.views.dealers.checkout_dealer,
        name="checkout_dealer",
    ),
    re_path(
        r"^dealer/(?P<guid>\w+)/?$", registration.views.dealers.dealers, name="dealers"
    ),
    re_path(
        r"^dealer/(?P<guid>\w+)/assistants/?$",
        registration.views.dealers.find_dealer_to_add_assistant,
        name="find_dealer_to_add_assistant",
    ),
    re_path(
        r"^dealer/assistants/lookup/?$",
        registration.views.dealers.find_dealer_to_add_assistant_post,
        name="find_dealer_to_add_assistant_post",
    ),
    re_path(
        r"^dealer/assistants/add/?$",
        registration.views.dealers.add_assistants,
        name="add_assistants",
    ),
    re_path(
        r"^dealer/assistants/checkout/?$",
        registration.views.dealers.add_assistants_checkout,
        name="add_assistants_checkout",
    ),
    re_path(
        r"^dealerassistant/(?P<guid>\w+)/?$",
        registration.views.dealers.dealer_asst,
        name="dealer_asst",
    ),
    re_path(
        r"^dealerassistant/add/find/?$",
        registration.views.dealers.find_asst_dealer,
        name="find_asst_dealer",
    ),
    re_path(
        r"^dealerassistant/add/done/?$",
        registration.views.dealers.done_asst_dealer,
        name="done_asst_dealer",
    ),
    re_path(r"^onsite/?$", registration.views.onsite.onsite, name="onsite"),
    re_path(r"^onsite/cart/?$", registration.views.onsite.onsite_cart, name="onsite_cart"),
    re_path(r"^onsite/done/?$", registration.views.onsite.onsite_done, name="onsite_done"),
    re_path(
        r"^onsite/admin/?$",
        registration.views.onsite_admin.onsite_admin,
        name="onsite_admin",
    ),
    re_path(
        r"^onsite/admin/search/?$",
        registration.views.onsite_admin.onsite_admin_search,
        name="onsite_admin_search",
    ),
    re_path(
        r"^onsite/admin/cart/?$",
        registration.views.onsite_admin.onsite_admin_cart,
        name="onsite_admin_cart",
    ),
    re_path(
        r"^onsite/admin/cart/add/?$",
        registration.views.onsite_admin.onsite_add_to_cart,
        name="onsite_add_to_cart",
    ),
    re_path(
        r"^onsite/admin/cart/remove/?$",
        registration.views.onsite_admin.onsite_remove_from_cart,
        name="onsite_remove_from_cart",
    ),
    re_path(
        r"^onsite/admin/open/?$",
        registration.views.onsite_admin.open_terminal,
        name="open_terminal",
    ),
    re_path(
        r"^onsite/admin/close/?$",
        registration.views.onsite_admin.close_terminal,
        name="close_terminal",
    ),
    re_path(
        r"^onsite/admin/ready/?$",
        registration.views.onsite_admin.ready_terminal,
        name="ready_terminal",
    ),
    re_path(
        r"^onsite/admin/payment/?$",
        registration.views.onsite_admin.enable_payment,
        name="enable_payment",
    ),
    re_path(
        r"^onsite/admin/clear/?$",
        registration.views.onsite_admin.onsite_admin_clear_cart,
        name="onsite_admin_clear_cart",
    ),
    re_path(
        r"^onsite/admin/badge/assign/?$",
        registration.views.onsite_admin.assign_badge_number,
        name="assign_badge_number",
    ),
    re_path(
        r"^onsite/admin/badge/print/?$",
        registration.views.onsite_admin.onsite_print_badges,
        name="onsite_print_badges",
    ),
    re_path(
        r"^onsite/square/complete/?$",
        registration.views.onsite_admin.complete_square_transaction,
        name="complete_square_transaction",
    ),
    re_path(
        r"^onsite/cash/complete/?$",
        registration.views.onsite_admin.complete_cash_transaction,
        name="complete_cash_transaction",
    ),
    re_path(
        r"^onsite/cashdrawer/status/?$",
        registration.views.onsite_admin.drawer_status,
        name="drawer_status",
    ),
    re_path(
        r"^onsite/cashdrawer/open/?$",
        registration.views.onsite_admin.open_drawer,
        name="open_drawer",
    ),
    re_path(
        r"^onsite/cashdrawer/deposit/?$",
        registration.views.onsite_admin.cash_deposit,
        name="cash_deposit",
    ),
    re_path(
        r"^onsite/cashdrawer/safedrop/?$",
        registration.views.onsite_admin.safe_drop,
        name="safe_drop",
    ),
    re_path(
        r"^onsite/cashdrawer/pickup/?$",
        registration.views.onsite_admin.cash_pickup,
        name="cash_pickup",
    ),
    re_path(
        r"^onsite/cashdrawer/close/?$",
        registration.views.onsite_admin.close_drawer,
        name="close_drawer",
    ),
    re_path(
        r"^onsite/cashdrawer/no_sale/?$",
        registration.views.onsite_admin.no_sale,
        name="no_sale",
    ),
    re_path(
        r"^onsite/admin/discount/create/?$",
        registration.views.onsite_admin.create_discount,
        name="onsite_create_discount",
    ),
    re_path(r"^cart/?$", registration.views.cart.get_cart, name="cart"),
    re_path(r"^cart/add/?$", registration.views.cart.add_to_cart, name="add_to_cart"),
    re_path(
        r"^cart/remove/?$",
        registration.views.cart.remove_from_cart,
        name="remove_from_cart",
    ),
    re_path(
        r"^cart/abandon/?$",
        registration.views.ordering.cancel_order,
        name="cancel_order",
    ),
    re_path(
        r"^cart/discount/?$",
        registration.views.ordering.apply_discount,
        name="discount",
    ),
    re_path(r"^cart/checkout/?$", registration.views.ordering.checkout, name="checkout"),
    re_path(r"^cart/done/?$", registration.views.cart.cart_done, name="done"),
    re_path(r"^events/?$", registration.views.common.get_events, name="events"),
    re_path(
        r"^departments/?$",
        registration.views.common.get_departments,
        name="departments",
    ),
    re_path(
        r"^alldepartments/?$",
        registration.views.common.get_all_departments,
        name="alldepartments",
    ),
    re_path(
        r"^pricelevels/?$",
        registration.views.attendee.get_price_levels,
        name="pricelevels",
    ),
    re_path(
        r"^adultpricelevels/?$",
        registration.views.attendee.get_adult_price_levels,
        name="adultpricelevels",
    ),
    re_path(
        r"^minorpricelevels/?$",
        registration.views.attendee.get_minor_price_levels,
        name="minorpricelevels",
    ),
    re_path(
        r"^accompaniedpricelevels/?$",
        registration.views.attendee.get_accompanied_price_levels,
        name="accompaniedpricelevels",
    ),
    re_path(
        r"^freepricelevels/?$",
        registration.views.attendee.get_free_price_levels,
        name="freepricelevels",
    ),
    re_path(r"^shirts/?$", registration.views.common.get_shirt_sizes, name="shirtsizes"),
    re_path(r"^tables/?$", registration.views.dealers.getTableSizes, name="tablesizes"),
    re_path(
        r"^addresses/?$",
        registration.views.common.get_session_addresses,
        name="addresses",
    ),
    re_path(
        r"^utility/badges?$", registration.views.common.basicBadges, name="basicBadges"
    ),
    re_path(r"^utility/vips?$", registration.views.common.vipBadges, name="vipBadges"),
    re_path(r"^flush/?$", registration.views.common.flush, name="flush"),
    re_path(r"^pdf/?$", registration.views.printing.servePDF, name="pdf"),
    re_path(r"^print/?$", registration.views.printing.printNametag, name="print"),
    re_path(
        r"^firebase/register/?",
        registration.views.onsite_admin.firebase_register,
        name="firebase_register",
    ),
    re_path(
        r"^firebase/lookup/?",
        registration.views.onsite_admin.firebase_lookup,
        name="firebase_lookup",
    ),
    re_path(
        r"webhook/square/v2",
        registration.views.webhooks.square_webhook,
        name="square_webhook",
    ),
]
