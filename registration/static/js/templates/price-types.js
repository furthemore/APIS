var levelTemplateData = [];
var levelData = [];
var shirtSizes = [];


$( "body" ).ready(function() {
        var url = "/apis/registration/pricelevels";
        if(adult){
            url = "/apis/registration/adultpricelevels";
        }

        $.getJSON(url, function(data) {
            levelData = data;
            $.each( data, function( key, val ) {
                var price = val.base_price;
                if (discount) { price = val.base_price - discount; }
                levelTemplateData.push({
                    name: val.name,
                    price: "$" + price,
                    levelId: "level_" + val.id,
                    selectText: "Select " + val.name
                });
            });
            $("#levelContainer").loadTemplate($("#levelTemplate"), levelTemplateData);
            $(".changeLevel").hide();
            
        });

        $.getJSON("/apis/registration/shirts", function(data) {
            shirtSizes = data;
        });

});

    $("#levelContainer").on('click', 'a.selectLevel', function(){
        clearLevels();
        var levelId = $(this).attr('id').split('_')[1];
        $.each( levelTemplateData, function( key, val ) {
            var id = val.levelId.split('_')[1];
            if (id == levelId){
                $("#regLevel").val(val.name);
                $("#levelContainer").loadTemplate($("#levelTemplate"), val);
                $(".changeLevel").show();
                $(".selectLevel").text("Selected!");
                generateOptions(id);
                return false;
            }
        });
    });
    $("#levelContainer").on('click', 'a.changeLevel', function() {
        $("#levelContainer").loadTemplate($("#levelTemplate"), levelTemplateData);      
        $("#regLevel").val("");
        $(".changeLevel").hide();
    });
    var clearLevels = function(){
        $.each( levelTemplateData, function( key, val ) {
            $("#"+val.levelId).text("Select " + val.name);
        });
        $("form").validator('update');
    };

    var generateOptions = function(levelId){
        var data = [];
        var description = "";
        $.each(levelData, function(key, thing){
            if (thing.id == levelId){
                data = thing.options;
                description = thing.description;
                return false;
            }
        });
        var container = $("<div id='optionsContainer' class='col-xs-6 col-sm-6 col-md-6 col-lg-8'><h4>Level Options</h4><hr/><div class='form-group'><div class='col-sm-12'>" + description + "</div></div></div>");
        $("#levelContainer").append(container);
        $.each( data, function(key, val) {
            if (val.value == "0.00"){
                var price = " (Free) ";
            } else {
                var price = " (+$" + val.value + ") "
            }
            var required = "";
            if (val.required) {required = "required";}
            switch (val.type){
                case "plaintext":
                    var template = $("#optionPlainTextTemplate");
                    $("#optionsContainer").loadTemplate(template, {
                        'content': val.description
                    }, {append: true});
                    break;  
                case "bool":
                    var template = $("#optionBoolTemplate");
                    if (val.required) {template = $("#optionBoolReqTemplate");}
                    $("#optionsContainer").loadTemplate(template, {
                        'name': val.name + " " + price,
                        'id': "option_" + val.id
                    }, {append: true});
                    break;
                case "int":
                    var template = $("#optionIntTemplate");
                    if (val.required) {template = $("#optionIntReqTemplate");}
                    $("#optionsContainer").loadTemplate(template, {
                        'name': val.name + " " + price,
                        'id': "option_" + val.id
                    }, {append: true});
                    break;
                case "string":
                    var template = $("#optionStringTemplate");
                    if (val.required) {template = $("#optionStringReqTemplate");}
                    var placeholder = val.name;
                    $("#optionsContainer").loadTemplate(template, {
                        'name': val.name + " " + price,
                        'id': "option_" + val.id,
                        'placeholder': placeholder,
                    }, {append: true});
                    break;
                default:
                    if (val.list == []){break;}
                    var options = [];
                    if (!val.required) {options.push({"content": "Select One...", "value": ""});}
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

   var getOptions = function() {
        var options = $(".levelOptions");
                var data = [];
        $.each(options, function(key, option) {
            if ($(option).is(':checkbox')) {
                if ($(option).is(':checked')) {
                    data.push({'id': option.id.split('_')[1], 'value': $(option).is(':checked')});
                }
            } else if ($(option).is('select')) {
                if ($(option).val() != "") {
                    data.push({'id': option.id.split('_')[1], 'value': $(option).val()});
                }            
            } else {
                data.push({'id': option.id.split('_')[1], 'value': $(option).val()});
            }
        });
        return data;
    };

