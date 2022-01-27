// ==== forms ====
function getAge(birthdate) {
    if (typeof event_start_date !== 'undefined') {
        var diff = event_start_date.getTime() - birthdate.getTime();
        return Math.floor(diff / (1000 * 60 * 60 * 24 * 365.25));
    }
    throw TypeError("event_start_date is undefined (perhaps event was not passed to your template)");
}
function toDateFormat(birthdate){
    var month = birthdate.getMonth();
    month = month + 1;
    return month + "/" + birthdate.getDate() + "/" + birthdate.getFullYear();
}
function parseDate(input) {
    // parse an ISO formatted date as localtime
    var parts = input.split('-');
    return new Date(parts[0], parts[1]-1, parts[2]);
}

function setTwoNumberDecimal(e) {
    this.value = parseFloat(this.value).toFixed(2);
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

$("body").ready(function (e) {
    $.ajaxSetup({
        beforeSend: function(xhr, settings) {
            if (!(/^http:.*/.test(settings.url) || /^https:.*/.test(settings.url))) {
                // Only send the token to relative URLs i.e. locally.
                xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
                xhr.setRequestHeader("IDEMPOTENCY-KEY", IDEMPOTENCY_KEY);
            }
        }
    });
});
