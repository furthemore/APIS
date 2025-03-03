shirtSizes = [];

$("body").ready(function () {
    $.getJSON("/registration/shirts", function (data) {
        $.each(data, function (key, val) {
            $("#shirt").append("<option value='" + val.id + "'>" + val.name + "</option>");
        });
        shirtSizes = data;
    });
});

$("#country").on("change", function () {
    if ($(this).val() == "US") {
        $("#state").val("VA").removeAttr("disabled").attr("required", "required");
        $("#zip").val("").removeAttr("disabled").attr("required", "required");
    } else {
        $("#state").val("").attr("disabled", "disabled").removeAttr("required");
        $("#zip").val("").attr("disabled", "disabled").removeAttr("required");
    }
});
