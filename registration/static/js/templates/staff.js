var shirtSizes = [];

    $( "body" ).ready(function() {
        // only init the javascript datepicker if none is provided by the browser natively
        if (!Modernizr.inputtypes.date) {
            $("#birthDate").datepicker({
                format: 'yyyy-mm-dd',
                changeMonth: true,
                changeYear: true
            });
        }
        $.getJSON("/apis/registration/shirts", function(data) {
            $.each(data, function(key, val) {
                $("#shirt").append("<option value='" + val.id + "'>" + val.name + "</option>");
            });
            shirtSizes = data;
        });
    });

    $("#country").on("change", function() {
        if ($(this).val() == "US"){
            $("#state").val("VA").removeAttr("disabled").attr("required", "required");
            $("#zip").val("").removeAttr("disabled").attr("required", "required");
        } else {
            $("#state").val("").attr("disabled", "disabled").removeAttr("required");
            $("#zip").val("").attr("disabled", "disabled").removeAttr("required");
        }
    });
