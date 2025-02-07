function daysInMonth(month, year) {
    return new Date(year, month, 0).getDate();
}

$(document).ready(function (e) {
    $('#byear, #bmonth').change(function () {

        if ($('#byear').val().length > 0 && $('#bmonth').val().length > 0) {
            $('#bday').prop('disabled', false);
            $('#bday').find('option').remove();

            const daysInSelectedMonth = daysInMonth($('#bmonth').val(), $('#byear').val());

            for (let i = 1; i <= daysInSelectedMonth; i++) {
                let day;
                if (i < 10) {
                    day = "0" + i;
                } else {
                    day = i;
                }
                $('#bday').append($("<option></option>").attr("value", day).text(i));
            }

        } else {
            $('#bday').prop('disabled', true);
        }

    });

    $('#byear, #bmonth, #bday').change(function () {
        const bday = $('#byear').val() + "-" + $('#bmonth').val() + "-" + $('#bday').val();
        $('#birthDate').val(bday);
    });

    // Populate from passed in hidden field
    let dob = $("#birthDate").val();
    if (dob === undefined) {
        return;
    }
    let [year, month, day] = dob.split('-');
    if (year && month && day) {
        $("#byear").val(year);
        $("#bmonth").val(month);
        $('#bmonth').change();
        $("#bday").val(day);
        $("#bday").change();
    }
});
