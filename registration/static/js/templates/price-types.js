let levelTemplateData = [];
let levelData = [];
let shirtSizes = [];


$("body").ready(function () {
    let levelTemplate = document.getElementById('levelTemplate');
    if (levelTemplate === null) {
        return;
    }

    function updatePriceLevels() {
        levelTemplateData = [];

        const [year, month, day] = [
            $("#byear").val(),
            $("#bmonth").val(),
            $("#bday").val()
        ];

        if (!year || !month || !day) return;

        $.post("/registration/pricelevels/", JSON.stringify({
            year,
            month,
            day,
            form_type: FORM_TYPE,
        }), function (data) {
            levelData = data;
            $.each(data, function (_, val) {
                let priceCents = Math.round(parseFloat(val.base_price) * 100);

                if (discount) {
                    priceCents = Math.max(priceCents - Math.round(discount * 100) - Math.round(paid_total * 100), 0);
                }

                if (priceCents >= 0) {
                    levelTemplateData.push({
                        name: val.name,
                        price: priceCents === 0 ? "FREE" : "$" + (priceCents / 100).toFixed(2),
                        levelId: "level_" + val.id,
                        selectText: "Select " + val.name
                    });
                }
            });

            if (levelTemplateData.length == 0) {
                $("#levelContainerAlert").removeClass("d-none");
            } else {
                $("#levelsNoBirthday").hide();
                animateLevelSelect($("#levelContainer"), function () {
                    $("#levelContainer").loadTemplate($("#levelTemplate"), levelTemplateData);
                    revealLevelCards($("#levelContainer"));
                    if (levelTemplateData.length == 1) {
                        select_level(1);
                    }
                });
            }
            $(".changeLevel").hide();
        });
    }

    updatePriceLevels();

    let updateTimer = null;
    $("#bday, #bmonth, #byear").on("input", function() {
        clearTimeout(updateTimer);
        updateTimer = setTimeout(updatePriceLevels, 300);
    });

    $.getJSON(SHIRT_SIZES_URL, function (data) {
        shirtSizes = data;
    });

});

function select_level(levelId, startRect) {
    $.each(levelTemplateData, function (_, val) {
        let id = val.levelId.split('_')[1];
        if (id == levelId) {
            animateLevelSelect($("#levelContainer"), function () {
                $("#regLevel").val(val.name);
                $("#levelContainer").loadTemplate($("#levelTemplate"), val);
                $(".changeLevel").show();
                $(".selectLevel").text("Selected!");
                $("#levelTemplateColumn").removeClass("col-6").addClass("col-12");
                generateOptions(id);
                flipCardToPosition($("#levelContainer .card").first(), startRect);
            });
            return false;
        }
    });
}

$("#levelContainer").on('click', 'a.selectLevel', function () {
    clearLevels();
    let levelId = $(this).attr('id').split('_')[1];
    let startRect = $(this).closest('[class*="col-"]')[0].getBoundingClientRect();
    select_level(levelId, startRect);
});

$("#levelContainer").on('click', 'a.changeLevel', function () {
    animateLevelSelect($("#levelContainer"), function () {
        $("#levelContainer").loadTemplate($("#levelTemplate"), levelTemplateData);
        $("#regLevel").val("");
        $(".changeLevel").hide();
        revealLevelCards($("#levelContainer"));
    });
});

function clearLevels() {
    $.each(levelTemplateData, function (_, val) {
        $("#" + val.levelId).text("Select " + val.name);
    });
    resetFormValidation();
}

function generateOptions(levelId) {
    let data = [];
    let description = "";
    $.each(levelData, function (_, thing) {
        if (thing.id == levelId) {
            data = thing.options;
            description = thing.description;
            return false;
        }
    });
    let container = $("<div id='optionsContainer' class='col-12 col-sm-6 col-md-8'><h4>Level Options</h4><hr/><div class='row mb-3'><div class='col-sm-12'>" + description + "</div></div></div>");
    $("#levelContainer").append(container);
    $.each(data, function (_, val) {
        let price = val.value == "0.00" ? " (Free) " : " (+$" + val.value + ") ";
        let imageHtml = val.image ? "<br><a href='javascript:;' data-image='" + val.image + "' class='open-image btn btn-sm btn-link btn-block'>(View Image)</a>" : "";
        if (val.active) {
            let template;
            switch (val.type) {
                case "plaintext":
                    template = $("#optionPlainTextTemplate");
                    $("#optionsContainer").loadTemplate(template, {
                        'content': val.description
                    }, {append: true});
                    break;
                case "bool":
                    template = val.required ? $("#optionBoolReqTemplate") : $("#optionBoolTemplate");
                    $("#optionsContainer").loadTemplate(template, {
                        'name': val.name + " " + price + imageHtml,
                        'id': "option_" + val.id
                    }, {append: true});
                    if (val.value == "0.00") {
                        $("#option_" + val.id).prop('checked', true);
                    }
                    break;
                case "int":
                    template = val.required ? $("#optionIntReqTemplate") : $("#optionIntTemplate");
                    $("#optionsContainer").loadTemplate(template, {
                        'name': val.name + " " + price + imageHtml,
                        'id': "option_" + val.id
                    }, {append: true});
                    break;
                case "string":
                    template = val.required ? $("#optionStringReqTemplate") : $("#optionStringTemplate");
                    $("#optionsContainer").loadTemplate(template, {
                        'name': val.name + " " + price + imageHtml,
                        'id': "option_" + val.id,
                        'placeholder': val.name,
                    }, {append: true});
                    break;
                default:
                    if (val.list == []) break;
                    let options = [];
                    if (!val.required) {
                        options.push({"content": "Select One...", "value": ""});
                    }
                    $.each(val.list, function (_, item) {
                        options.push({"content": item.name, "value": item.id});
                    });
                    $("#optionsContainer").loadTemplate($("#optionListTemplate"), {
                        'name': val.name + " " + price + imageHtml,
                        'id': "option_" + val.id,
                        'options': options
                    }, {append: true});
                    break;
            }
        }
    });
    resetFormValidation();
}

function getOptions() {
    let data = [];
    $.each($(".levelOptions"), function (_, option) {
        if ($(option).is(':checkbox')) {
            if ($(option).is(':checked')) {
                data.push({'id': option.id.split('_')[1], 'value': $(option).is(':checked')});
            }
        } else {
            if ($(option).val() != "") {
                data.push({'id': option.id.split('_')[1], 'value': $(option).val()});
            }
        }
    });
    return data;
}
