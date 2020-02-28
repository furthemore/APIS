// ==== forms ====
function getAge(birthdate) {
    if (typeof event_start_date !== 'undefined') {
        var diff = event_start_date.getTime() - birthdate.getTime();
        return Math.floor(diff / (1000 * 60 * 60 * 24 * 365.25));
    }
    throw TypeError("event_start_date is undefined (perhaps event was not passed to your template)");
}
function toDateFormat(birthdate){
    var month = birthdate.getMonth();
    month = month + 1;
    return month + "/" + birthdate.getDate() + "/" + birthdate.getFullYear();
}
function parseDate(input) {
    // parse an ISO formatted date as localtime
    var parts = input.split('-');
    return new Date(parts[0], parts[1]-1, parts[2]);
}

function setTwoNumberDecimal(e) {
    this.value = parseFloat(this.value).toFixed(2);
}
