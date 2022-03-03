function daysInMonth(month, year) {
  return new Date(year, month, 0).getDate();
}

$(document).ready(function (e) {
  $('#byear, #bmonth').change(function() {

    if ($('#byear').val().length > 0 && $('#bmonth').val().length > 0) {
      $('#bday').prop('disabled', false);
      $('#bday').find('option').remove();

      var daysInSelectedMonth = daysInMonth($('#bmonth').val(), $('#byear').val());

      for (var i = 1; i <= daysInSelectedMonth; i++) {
        if (i < 10) {
          var day = "0" + i;
        } else {
          var day = i;
        }
        $('#bday').append($("<option></option>").attr("value", day).text(i));
      }

    } else {
      $('#bday').prop('disabled', true);
    }

  });

  $('#byear, #bmonth, #bday').change(function() {
    var bday = $('#byear').val() + "-" + $('#bmonth').val() + "-" + $('#bday').val();
    $('#birthDate').val(bday);
  });

  // Populate from passed in hidden field
  let dob = $("#birthDate").val();
  let [year, month, day] = dob.split('-');
  if (year) {
    $("#byear").val(year);
    $("#bmonth").val(month);
    $('#bmonth').change();
    $("#bday").val(day);
  } else {
    day = $('#bday').val();
    $('#bmonth').change();
    $('#bday').val(day);
  }
});
