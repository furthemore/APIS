async function formatError(response) {
    try {
        const r = await response.json();
        return r.reason;
    } catch (e) {
        return "Unknown"
    }
}

function showAlert(html) {
    const alertDiv = document.getElementById('alert-bar');
    alertDiv.innerHTML = html;
    alertDiv.classList.remove('alert-hidden');
}

function hideAlert() {
    const alertDiv = document.getElementById('alert-bar');
    alertDiv.classList.add('alert-hidden');
}

let addresses = [];
$("body").ready(function () {
    if (EVENT_COLLECT_ADDRESS) {
        $.getJSON(URL_REGISTRATION_ADDRESSES, function (data) {
            addresses = data;
        });

        $("#useFrom").on("change", function (e) {
            const userId = $(this).val();
            if (userId == "") {
                $("#fname").val("");
                $("#lname").val("");
                $("#email").val("");
                $("#add1").val("");
                $("#add2").val("");
                $("#city").val("");
                $("#state").val("");
                $("#country").val("");
                return;
            }

            const address = addresses[userId];
            $("#fname").val(address.fname);
            $("#lname").val(address.lname);
            $("#email").val(address.email);
            $("#add1").val(address.address1);
            $("#add2").val(address.address2);
            $("#city").val(address.city);
            $("#state").val(address.state);
            $("#postal").val(address.postalCode);
            $("#country").val(address.country);
        });
    }
});