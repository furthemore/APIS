# MQTT broker

MQTT provides some of the real-time features used in APIS, notably push notifications for the on-site flow,  updating
information customer-facing square payment kiosks, and controlling position stack lights.

Authentication for these uses happen on-the-fly by issuing JWTs, so an MQTT broker must be configured to accept JWT
authentication.

The components APIS recommends for this purpose are:
* [Mosquitto MQTT broker](https://mosquitto.org/)
* [JWT authentication plugin](https://github.com/wiomoc/mosquitto-jwt-auth)
* [Lego ACME client for TLS certificates](https://github.com/go-acme/lego)

An example Mosquitto configuration is included in this directory.
We operate our broker on a dedicated subdomain (`mqtt.example.com`).

## Setup

1. Compile and install the [JWT authentication plugin](https://github.com/wiomoc/mosquitto-jwt-auth?tab=readme-ov-file#building)
1. Copy `mosquitto/apis.conf` to `/etc/mosquitto/conf.d/apis/conf` and:
  1. Generate a strong JWT signing secret: `openssl rand -base64 32`
    1. Populate this value in the mosquitto configuration in the `auth_opt_jwt_sec_base64` option.
    1. Set the same value in the APIS configuration as `MQTT_JWT_SECRET`
1. Configure TLS and Websockets.  You have a few options:
  1. Caddy webserver, by making your issued cert for `mqtt.example.com` available to be read by Mosquitto.
  1. External ACME certificate with Lego + Nginx - get your cert issued by Lego and configure Nginx to use that.


Example nginx configuration:

```nginx
upstream mqtt.example.com {
    server localhost:1884;
}

map $http_upgrade $connection_upgrade {
    default upgrade;
    ''      close;
}

server {
    server_name mqtt.example.com;
    access_log /var/log/nginx/mqtt.example.com-access.log;
    error_log /var/log/nginx/mqtt.example.com-error.log;

    location / {
        proxy_http_version 1.1;
        proxy_pass http://localhost:1884;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_read_timeout 1800;
        proxy_send_timeout 1800;
    }


    listen 443 ssl;
    ssl_certificate /datadrive/tls/lego/certificates/_.mqtt.example.com.crt;
    ssl_certificate_key /datadrive/tls/lego/certificates/_.mqtt.example.com.key;

    include /etc/letsencrypt/options-ssl-nginx.conf; # managed by Certbot
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem; # managed by Certbot


    add_header Strict-Transport-Security "max-age=31536000" always; # managed by Certbot

}
server {
    if ($host = mqtt.example.com) {
        return 301 https://$host$request_uri;
    } # managed by Certbot


    listen 80;
    server_name mqtt.example.com;
    access_log /var/log/nginx/mqtt.example.com-access.log;
    error_log /var/log/nginx/mqtt.example.com-error.log;

}

```
