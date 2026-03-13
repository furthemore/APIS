from django.contrib.auth.views import LogoutView
from django.urls import path

import registration.views.attendee
import registration.views.cart
import registration.views.common
import registration.views.dealers
import registration.views.onsite
import registration.views.onsite_admin
import registration.views.ordering
import registration.views.pricelevels
import registration.views.printing
import registration.views.staff
import registration.views.upgrade
import registration.views.webhooks

app_name = "registration"


def trigger_error(request):
    division_by_zero = 1 / 0
    return division_by_zero


urlpatterns = [
    path("sentry-debug/", trigger_error),
    path('', registration.views.common.index, name="index"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("upgrade/lookup/", registration.views.upgrade.find_upgrade, name="find_upgrade"),
    path("upgrade/info/", registration.views.upgrade.info_upgrade, name="info_upgrade"),
    path("upgrade/add/", registration.views.upgrade.add_upgrade, name="add_upgrade"),
    path("upgrade/invoice/", registration.views.upgrade.invoice_upgrade, name="invoice_upgrade"),
    path("upgrade/checkout/", registration.views.upgrade.checkout_upgrade, name="checkout_upgrade"),
    path("upgrade/done/", registration.views.upgrade.done_upgrade, name="done_upgrade"),
    path('upgrade/<slug:guid>/', registration.views.upgrade.upgrade, name="upgrade"),
    path("returning-staff/done/", registration.views.staff.staff_done, name="returning_staff_done"),
    path("returning-staff/lookup/", registration.views.staff.find_returning_staff, name="find_returning_staff"),
    path("returning-staff/info/", registration.views.staff.info_returning_staff, name="info_returning_staff"),
    path("returning-staff/add/", registration.views.staff.add_returning_staff, name="add_returning_staff"),
    path('returning-staff/<slug:guid>/', registration.views.staff.returning_staff, name="returning_staff"),
    path("new-staff/done/", registration.views.staff.staff_done, name="new_staff_done"),
    path("new-staff/lookup/", registration.views.staff.find_new_staff, name="find_new_staff"),
    path("new-staff/info/", registration.views.staff.info_new_staff, name="info_new_staff"),
    path("new-staff/add/", registration.views.staff.add_new_staff, name="add_new_staff"),
    path('new-staff/<slug:guid>/', registration.views.staff.new_staff, name="new_staff"),
    path("dealer/", registration.views.dealers.new_dealer, name="new_dealer"),
    path("dealer/addNew/", registration.views.dealers.addNewDealer, name="addNewDealer"),
    path("dealer/done/", registration.views.dealers.done_dealer, name="done_dealer"),
    path("dealer/thanks/", registration.views.dealers.thanks_dealer, name="thanks_dealer"),
    path("dealer/lookup/", registration.views.dealers.find_dealer, name="find_dealer"),
    path("dealer/add/", registration.views.dealers.add_dealer, name="add_dealer"),
    path("dealer/info/", registration.views.dealers.info_dealer, name="info_dealer"),
    path("dealer/invoice/", registration.views.dealers.invoice_dealer, name="invoice_dealer"),
    path("dealer/checkout/", registration.views.dealers.checkout_dealer, name="checkout_dealer"),
    path('dealer/<slug:guid>/', registration.views.dealers.dealers, name="dealers"),
    path('dealer/<slug:guid>/assistants/',
        registration.views.dealers.find_dealer_to_add_assistant,
        name="find_dealer_to_add_assistant",
    ),
    path("dealer/assistants/lookup/", registration.views.dealers.find_dealer_to_add_assistant_post, name="find_dealer_to_add_assistant_post"),
    path("dealer/assistants/add/", registration.views.dealers.add_assistants, name="add_assistants"),
    path("dealer/assistants/checkout/", registration.views.dealers.add_assistants_checkout, name="add_assistants_checkout"),
    path('dealerassistant/<slug:guid>/', registration.views.dealers.dealer_asst, name="dealer_asst"),
    path("dealerassistant/add/find/", registration.views.dealers.find_asst_dealer, name="find_asst_dealer"),
    path("dealerassistant/add/done/", registration.views.dealers.done_asst_dealer, name="done_asst_dealer"),
    path("onsite/", registration.views.onsite.onsite, name="onsite"),
    path("onsite/cart/", registration.views.onsite.onsite_cart, name="onsite_cart"),
    path("onsite/done/", registration.views.onsite.onsite_done, name="onsite_done"),
    path("onsite/admin/", registration.views.onsite_admin.onsite_admin, name="onsite_admin"),
    path("onsite/admin/search/", registration.views.onsite_admin.onsite_admin_search, name="onsite_admin_search"),
    path("onsite/admin/cart/", registration.views.onsite_admin.onsite_admin_cart, name="onsite_admin_cart"),
    path("onsite/admin/cart/add/", registration.views.onsite_admin.onsite_add_to_cart, name="onsite_add_to_cart"),
    path("onsite/admin/cart/remove/", registration.views.onsite_admin.onsite_remove_from_cart, name="onsite_remove_from_cart"),
    path("onsite/admin/cart/transfer/", registration.views.onsite_admin.onsite_admin_transfer_cart, name="onsite_admin_transfer_cart"),
    path("onsite/admin/terminal/status/", registration.views.onsite_admin.set_terminal_status, name="terminal_status"),
    path("onsite/admin/payment/", registration.views.onsite_admin.enable_payment, name="enable_payment"),
    path("onsite/admin/clear/", registration.views.onsite_admin.onsite_admin_clear_cart, name="onsite_admin_clear_cart"),
    path("onsite/admin/badge/assign/", registration.views.onsite_admin.assign_badge_number, name="assign_badge_number"),
    path("onsite/admin/badge/print/", registration.views.onsite_admin.onsite_print_badges, name="onsite_print_badges"),
    path("onsite/admin/badge/print/clear/", registration.views.onsite_admin.onsite_print_clear, name="onsite_print_clear"),
    path("onsite/square/complete/", registration.views.onsite_admin.complete_square_transaction, name="complete_square_transaction"),
    path("onsite/cash/complete/", registration.views.onsite_admin.complete_cash_transaction, name="complete_cash_transaction"),
    path("onsite/admin/receipt/", registration.views.onsite_admin.print_receipts, name="onsite_print_receipts"),
    path("onsite/cashdrawer/status/", registration.views.onsite_admin.drawer_status, name="drawer_status"),
    path("onsite/cashdrawer/open/", registration.views.onsite_admin.open_drawer, name="open_drawer"),
    path("onsite/cashdrawer/deposit/", registration.views.onsite_admin.cash_deposit, name="cash_deposit"),
    path("onsite/cashdrawer/safedrop/", registration.views.onsite_admin.safe_drop, name="safe_drop"),
    path("onsite/cashdrawer/pickup/", registration.views.onsite_admin.cash_pickup, name="cash_pickup"),
    path("onsite/cashdrawer/close/", registration.views.onsite_admin.close_drawer, name="close_drawer"),
    path("onsite/cashdrawer/no_sale/", registration.views.onsite_admin.no_sale, name="no_sale"),
    path("onsite/admin/discount/create/", registration.views.onsite_admin.create_discount, name="onsite_create_discount"),
    path("onsite/admin/regtoken", registration.views.onsite_admin.regtoken, name="onsite_regtoken"),
    path("onsite/admin/attendee", registration.views.onsite_admin.attendee_details, name="onsite_attendee_details"),
    path("cart/", registration.views.cart.get_cart, name="cart"),
    path("cart/add/", registration.views.cart.add_to_cart, name="add_to_cart"),
    path("cart/remove/", registration.views.cart.remove_from_cart, name="remove_from_cart"),
    path("cart/abandon/", registration.views.ordering.cancel_order, name="cancel_order"),
    path("cart/discount/", registration.views.ordering.apply_discount, name="discount"),
    path("cart/checkout/", registration.views.ordering.checkout, name="checkout"),
    path("cart/done/", registration.views.cart.cart_done, name="done"),
    path('events/', registration.views.common.get_events, name="events"),
    path('departments/', registration.views.common.get_departments, name="departments"),
    path('alldepartments/', registration.views.common.get_all_departments, name="alldepartments"),
    path('pricelevels/', registration.views.pricelevels.get_price_levels, name="pricelevels"),
    path('shirts/', registration.views.common.get_shirt_sizes, name="shirtsizes"),
    path('tables/', registration.views.dealers.getTableSizes, name="tablesizes"),
    path('addresses/', registration.views.common.get_session_addresses, name="addresses"),
    path('utility/badges/', registration.views.common.basicBadges, name="basicBadges"),
    path('utility/vips', registration.views.common.vipBadges, name="vipBadges"),
    path("flush/", registration.views.common.flush, name="flush"),
    path("pdf/", registration.views.printing.servePDF, name="pdf"),
    path("print/", registration.views.printing.printNametag, name="print"),
    path("firebase/register/", registration.views.onsite_admin.firebase_register, name="firebase_register"),
    path("firebase/lookup/", registration.views.onsite_admin.firebase_lookup, name="firebase_lookup"),
    path("webhook/square/v2", registration.views.webhooks.square_webhook, name="square_webhook"),
    path("terminal/square/token", registration.views.onsite_admin.terminal_square_token, name="terminal_square_token"),
    path("terminal/square/completed", registration.views.onsite_admin.complete_square_transaction, name="terminal_square_completed"),
    path("oauth/square", registration.views.onsite_admin.oauth_square, name="oauth_square"),
]
