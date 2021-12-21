
function getAssistants() {
    var partners = [];
    var partnerList = $(".partnerGroup");
    $.each(partnerList, function(key, item) {
        var partner = {};
        var itemList = $(item).find("input")
        var hasValues = false;
        $.each(itemList, function(key2, item2){
            var id = item2.id.split('_')[0];
            if (($(item2).val() != "") && ($(item2).is(":enabled"))) {
                hasValues = true;
            }
            // partner['existing'] = item2.id.split('_')[1];
            partner[id] = $(item2).val();
        });
        if (hasValues){
            partner['license'] = 'NA';
            partners.push(partner);
        }
    });
    return partners;
}

$(document).ready(function () {
    var on_partner_keyup = function (e) {
        var partners = getAssistants();
        $("#total").text("$" + 55*partners.length + ".00");
    };

    $(".partnerGroup input").keyup(on_partner_keyup);
    on_partner_keyup();
})

$("#checkout").click(function (e) {
    e.preventDefault();
    $("form").validator('validate');
    var errorCount = $(".has-error").length;
    if (errorCount > 0) {return;}

    $("#checkout").attr("disabled", "disabled");

        paymentForm.requestCardNonce();

});

function doCheckout(card_data) {

    var data = {
        'dealer': {'id': dealer_id },
        'billingData': {
                'nonce': $("#card-nonce").val(), 'breakfast': $("#asstbreakfast").is(':checked'),
        'cc_firstname': $("#fname").val(), 'cc_lastname': $("#lname").val(), 'email': $("#email").val(),
                'address1': $("#add1").val(), 'address2': $("#add2").val(), 'city': $("#city").val(),
                'state': $("#state").val(), 'country': $("#country").val(), 'postal': $("#zip").val(),
                'card_data': card_data,
        },
                'assistants': getAssistants()
    };

    $.ajax({
        "type": "POST",
        "dataType": "json",
        "url": URL_ADD_ASSISTANTS_CHECKOUT,
        "data": JSON.stringify(data),
        "beforeSend": function(xhr, settings) {
            console.log("Before Send");
            $.ajaxSettings.beforeSend(xhr, settings);
        },
        "error": function(result, status, error) {
                alert("An error has occurred. If this error continues, please contact " + DEALER_EMAIL + " for assistance.")
            $("#checkout").removeAttr("disabled");
        },
        "success": function (result, status) {
            if (result.success) {
                window.location = URL_DONE_AST_DEALER;
            } else {
                alert("An error has occurred: " + result.message + " If this error continues, please contact " + DEALER_EMAIL + " for assistance.");
            $("#checkout").removeAttr("disabled");
    }
        }
});

}


function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie != '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) == (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
$.ajaxSetup({
    beforeSend: function(xhr, settings) {
        if (!(/^http:.*/.test(settings.url) || /^https:.*/.test(settings.url))) {
            // Only send the token to relative URLs i.e. locally.
            xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
        }
    }
});
