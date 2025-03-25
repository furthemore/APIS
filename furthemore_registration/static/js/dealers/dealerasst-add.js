function getAssistants() {
    let partners = [];
    const partnerList = $(".partnerGroup");
    $.each(partnerList, function (key, item) {
        let partner = {};
        const itemList = $(item).find("input")
        let hasValues = false;
        $.each(itemList, function (key2, item2) {
            const id = item2.id.split('_')[0];
            if (($(item2).val() != "") && ($(item2).is(":enabled"))) {
                hasValues = true;
            }
            // partner['existing'] = item2.id.split('_')[1];
            partner[id] = $(item2).val();
        });
        if (hasValues) {
            partner['license'] = 'NA';
            partners.push(partner);
        }
    });
    return partners;
}

$(document).ready(function () {
    let on_partner_keyup = function (e) {
        let partners = getAssistants();
        $("#total").text("$" + 55 * partners.length + ".00");
    };

    $(".partnerGroup input").keyup(on_partner_keyup);
    on_partner_keyup();
});