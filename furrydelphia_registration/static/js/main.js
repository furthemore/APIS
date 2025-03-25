// ==== forms ====
function getAgeByEventStart(birthdate) {
    if (typeof event_start_date !== 'undefined') {
        const diff = event_start_date.getTime() - birthdate.getTime();
        return Math.floor(diff / (1000 * 60 * 60 * 24 * 365.25));
    }
    throw TypeError("event_start_date is undefined (perhaps event was not passed to your template)");
}

function getAge(birthdate) {
    let diff = new Date().getTime() - birthdate.getTime();
    return Math.floor(diff / (1000 * 60 * 60 * 24 * 365.25));
}

function toDateFormat(birthdate){
    let month = birthdate.getMonth();
    month = month + 1;
    return month + "/" + birthdate.getDate() + "/" + birthdate.getFullYear();
}

function parseDate(input) {
    // parse an ISO formatted date as localtime
    const parts = input.split('-');
    return new Date(parts[0], parts[1]-1, parts[2]);
}

function setTwoNumberDecimal(e) {
    this.value = parseFloat(this.value).toFixed(2);
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie != '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) == (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

async function postJSON(url, body) {
    let headers = {
        'Content-Type': 'application/json',
    };
    if (!(/^http:.*/.test(url) || /^https:.*/.test(url))) {
        headers['X-CSRFToken'] = getCookie('csrftoken');
        headers['IDEMPOTENCY-KEY'] = IDEMPOTENCY_KEY;
    }

    return fetch(URL_REGISTRATION_CHECKOUT, {
        method: 'POST',
        headers: headers,
        body,
    })
}

$(document).ready(function (e) {
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
