
const shc_source = $("#shc-template").html();
const shc_template = Handlebars.compile(shc_source);

function get_topic(topic) {
    return MQTT_BASE_TOPIC + "/" + topic;
}

function send_notification(message) {
    if (!("Notification" in window)) {
        alert(message);
    } else if (Notification.permission === "granted") {
        var notification = new Notification(message);
    }
}

function isExpired(datetime) {
    return (new Date().getTime() > datetime.getTime());
}

function bind_close_panel() {
    $(".close-panel").click(function (evt) {
        $(this).parent().parent().parent().remove();
        localStorage.removeItem($(this).data("item"));
    });
}

function load_id_scan() {
    let parsed = JSON.parse(localStorage.getItem("id_scan"));
    if (parsed == null) {
        return;
    }

    parsed.age = getAge(parseDate(parsed.dob));
    parsed.expired = isExpired(parseDate(parsed.expiry));

    let node = document.createElement("div");
    let source = $("#scan-template").html();
    let template = Handlebars.compile(source);

    node.innerHTML = template(parsed);
    $("#scan_log").append(node);

    bind_close_panel();
}

function load_shc_scan() {
    let parsed = JSON.parse(localStorage.getItem("shc_scan"))
    if (parsed == null) {
        return;
    }

    // verified, and not trusted: warning
    parsed.verification.class = "warning";
    parsed.verification.status = "Partially Verified";
    // Trusted and verified: success
    if (parsed.verification.trusted) {
        parsed.verification.class = "success";
        parsed.verification.status = "Verified";
    }
    // not verified: danger
    if (!parsed.verification.verified) {
        parsed.verification.class = "danger";
        parsed.verification.status = "Not Verified";
    }

    let node = document.createElement("div");
    node.innerHTML = shc_template(parsed);
    $("#scan_log").append(node);
    bind_close_panel();
}

$(document).ready(function () {
    load_id_scan();
    load_shc_scan();
})

if (MQTT_ENABLED) {
    let notification_promise = Notification.requestPermission();

    const client = mqtt.connect(MQTT_BROKER, MQTT_OPTIONS);

    console.log(client);

    client.on('connect', function () {
        let topic = get_topic("#");
        console.log("MQTT subscribe to", topic);
        client.subscribe(topic, function(err) {
            if (!err) {
              client.publish(get_topic("admin_presence"), '"Hello! :3"');
            }
        });
    })

    client.on('error', function (error) {
        console.log("MQTT error: ", error);
        $("#client-error").fadeIn();
    });

    client.on('reconnect', function(error) {
        console.log("MQTT reconnecting:", error);
        $("#client-error").fadeOut();
    });

    client.on('message', function(topic, message) {
        console.log("MQTT message:", topic, message.toString());

        let payload = null;
        try {
            payload = JSON.parse(message.toString());
        } catch (SyntaxError) {
        }

        if (topic === get_topic("refresh")) {
            refresh_cart();
        }

        if (topic == get_topic("open")) {
            window.open(payload.url);
        }

        if (topic == get_topic("notification")) {
            send_notification(payload.text);
        }

        if (topic == get_topic("alert")) {
            alert(payload.text);
        }

        if (topic == get_topic("scan/id")) {
            // Cache the scan in local storage, so it survives page refreshes
            localStorage.setItem('id_scan', message.toString());
            $("input[name=search]").val(payload.last);
            $("#search_form").submit();
        }

        if (topic == get_topic("scan/shc")) {
            // SmartHealthCard vaccine QR code scanned
            localStorage.setItem('shc_scan', message.toString());
            load_shc_scan();
        }
    });
}