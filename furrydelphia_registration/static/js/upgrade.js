$(document).ready(function () {
    $("#cancel").click(function (e) {
          $.getJSON(URL_REGISTRATION_FLUSH, function (data) {
              window.location.reload();
          });
    });
});