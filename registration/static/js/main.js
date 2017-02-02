// ==== forms ====
function getAge(birthdate) {
    var curr  = new Date(2017, 3, 28); // Note: months are 0-indexed
    var diff = curr.getTime() - birthdate.getTime();
    return Math.floor(diff / (1000 * 60 * 60 * 24 * 365.25));
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
