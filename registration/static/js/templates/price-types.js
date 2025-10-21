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
            $.each(data, function (key, val) {
                let price = val.base_price;

                if (discount) {
                    price = Math.max(val.base_price - discount - paid_total, 0);
                }

                if (price >= 0) {
                    levelTemplateData.push({
                        name: val.name,
                        price: "$" + price,
                        levelId: "level_" + val.id,
                        selectText: "Select " + val.name
                    });
                }
            });

            $("#levelContainer").loadTemplate($("#levelTemplate"), levelTemplateData);
            $(".changeLevel").hide();
        });
    }

    updatePriceLevels();

    $("#bday, #bmonth, #byear").on("input", function() {
        updatePriceLevels();
    });

    $.getJSON("/registration/shirts", function (data) {
        shirtSizes = data;
    });

});

$("#levelContainer").on('click', 'a.selectLevel', function () {
    clearLevels();
    const levelId = $(this).attr('id').split('_')[1];
    $.each(levelTemplateData, function (key, val) {
        const id = val.levelId.split('_')[1];
        if (id == levelId) {
            $("#regLevel").val(val.name);
            $("#levelContainer").loadTemplate($("#levelTemplate"), val);
            $(".changeLevel").show();
            $(".selectLevel").text("Selected!");
            generateOptions(id);
            return false;
        }
    });
});
$("#levelContainer").on('click', 'a.changeLevel', function () {
    $("#levelContainer").loadTemplate($("#levelTemplate"), levelTemplateData);
    $("#regLevel").val("");
    $(".changeLevel").hide();
});

const clearLevels = function () {
    $.each(levelTemplateData, function (key, val) {
        $("#" + val.levelId).text("Select " + val.name);
    });
    $("form").validator('update');
};

const generateOptions = function (levelId) {
    let data = [];
    let description = "";
    $.each(levelData, function (key, thing) {
        if (thing.id == levelId) {
            data = thing.options;
            description = thing.description;
            return false;
        }
    });
    const container = $("<div id='optionsContainer' class='col-xs-6 col-sm-6 col-md-6 col-lg-8'><h4>Level Options</h4><hr/><div class='form-group'><div class='col-sm-12'>" + description + "</div></div></div>");
    $("#levelContainer").append(container);
    $.each(data, function (key, val) {
        let price;
        if (val.value == "0.00") {
            price = " (Free) ";
        } else {
            price = " (+$" + val.value + ") ";
        }
        let required = "";
        if (val.required) {
            required = "required";
        }
        let template; switch (val.type) {
            case "plaintext":
                template = $("#optionPlainTextTemplate");
                $("#optionsContainer").loadTemplate(template, {
                    'content': val.description
                }, {append: true});
                break;
            case "bool":
                template = $("#optionBoolTemplate");
                if (val.required) {
                    template = $("#optionBoolReqTemplate");
                }
                $("#optionsContainer").loadTemplate(template, {
                    'name': val.name + " " + price,
                    'id': "option_" + val.id
                }, {append: true});
                break;
            case "int":
                template = $("#optionIntTemplate");
                if (val.required) {
                    template = $("#optionIntReqTemplate");
                }
                $("#optionsContainer").loadTemplate(template, {
                    'name': val.name + " " + price,
                    'id': "option_" + val.id
                }, {append: true});
                break;
            case "string":
                template = $("#optionStringTemplate");
                if (val.required) {
                    template = $("#optionStringReqTemplate");
                }
                const placeholder = val.name;
                $("#optionsContainer").loadTemplate(template, {
                    'name': val.name + " " + price,
                    'id': "option_" + val.id,
                    'placeholder': placeholder,
                }, {append: true});
                break;
            default:
                if (val.list == []) {
                    break;
                }
                let options = [];
                if (!val.required) {
                    options.push({"content": "Select One...", "value": ""});
                }
                $.each(val.list, function (key, item) {
                    options.push({"content": item.name, "value": item.id})
                });
                $("#optionsContainer").loadTemplate($("#optionListTemplate"), {
                    'name': val.name + " " + price,
                    'id': "option_" + val.id,
                    'options': options
                }, {append: true});
                break;
        }
    });

    $("form").validator('update');
};

const getOptions = function () {
    const options = $(".levelOptions");
    let data = [];
    $.each(options, function (key, option) {
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
};
