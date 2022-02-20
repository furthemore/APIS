
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

if (MQTT_ENABLED) {
    let notification_promise = Notification.requestPermission();

    const client = mqtt.connect(MQTT_BROKER, MQTT_OPTIONS);

    console.log(client);

    client.on('connect', function () {
        let topic = get_topic("#");
        console.log("MQTT subscribe to", topic);
        client.subscribe(topic, function(err) {
            if (!err) {
              client.publish(get_topic("admin_presence"), "Hello! :3");
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

        if (topic === get_topic("refresh")) {
            refresh_cart();
        }

        if (topic == get_topic("navigate")) {
            window.open(message.url);
        }

        if (topic == get_topic("notification")) {

        }
    });
}