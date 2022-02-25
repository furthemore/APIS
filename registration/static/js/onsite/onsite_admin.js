
var refresh_cart;
var cartData = [];
var cartTemplateData = [];

var get_printable = function () {
    // Anything in the cart marked as paid is eligible for printing
    var printQueue = [];
    var skipped = [];
    $.each(cartData.result, function(key, value) {
      if (value.printed) {
          skipped.push(value);
      }

      if (((value.abandoned.toUpperCase() == "PAID") || (value.abandoned.toUpperCase() == "COMP")) &&
         (value.holdType === null) &&
         (value.printed === false)) {
          printQueue.push(value);
      }
    });

    if (printQueue.length > 0) {
        $("#print_button").removeAttr("disabled");
    } else {
        $("#print_button").attr("disabled", "disabled");
    }

    return printQueue;
};

var print_badges = function(e) {
    var printQueue = get_printable();
    var badge_preview = "";
    var stop = false;

    // assign badge numbers
    $.ajax(URL_REGISTRATION_ASSIGN_BADGE_NUMBER, {
      data : JSON.stringify(printQueue),
      contentType : 'application/json',
      type : 'POST'
    })
    .done(function(data) {
        console.log(data.success);
    }).success(function (data) {
       var printIDs = [];
       $.each(printQueue, function(idx, badge) {
          printIDs.push(badge.id);
       });
       // print badges

      $.getJSON(URL_REGISTRATION_ONSITE_PRINT_BADGES + "?id=" + printIDs.join("&id="), function (data) {
          if (!data.success) {
              alert("Error while printing badges");
          }
          window.open(data.url);
      }).fail(function (data) {
        $("#cart-error").html("Server error while assigning badge numbers:<br>"+data.message).fadeIn();
      });

      // clear cart
      $.getJSON(URL_REGISTRATION_ONSITE_ADMIN_CLEAR_CART);
      refresh_cart();
    });
};

$(document).ready(function () {
    $.addTemplateFormatter("MinorFormFormatter",
        function(value, template) {
          if (parseInt(value) < 18) {
            return '<span style="color: red">MINOR FORM REQUIRED</span>';
          }
          return "18+";
    });

    $.addTemplateFormatter("PaidBadgeFormatter",
        function(value, template) {
            if (value == "Paid") {
                return '<span class="label label-success">Paid</span>';
            } else if (value == "Comp") {
                return '<span class="label label-info">Comp</span>';
            } else {
                return '<span class="label label-warning">' + value + '</span>';
            }
    });

    $.addTemplateFormatter("PrintedBadgeFormatter",
        function(value, template) {
            if (value) {
                return '<span class="label label-danger" title="Already printed"><i class="fas fa-print"></i></span>';
            }
        }
    );

    $.addTemplateFormatter("PrintedBadgeNumberFormatter",
        function(value, template) {
            if (value) {
                return '<span class="label label-info" title="Badge Number">' + value + '</span>';
            }
        }
    );

    $.addTemplateFormatter("BadgeChangeFormatter",
        function(value, template) {
            if (value) {
                return '<a href="/admin/registration/badge/change/' + value.id + '">' + value.name + '</a>';
            }
        }
    );


    /* This should probably be a checkbox instead, so that we can still send to a terminal's associated printer
    if (navigator.userAgent.match(/iPad|iPhone/)) {
        $("#pos").append('<option value="ios">This device (iOS)</option>');
    }
    if (navigator.userAgent.match(/Android/)) {
        $("#pos").append('<option value="android">This device (Android)</option>');
    }
    */

    $.addTemplateFormatter("HoldTypeFormatter",
        function(value, template) {
            if (value === null) {
                return '';
            } else {
                return '<span class="label label-danger">' + value + '</span>';
            }
    });

    $.ajaxSetup({
        beforeSend: function(xhr, settings) {
            if (!(/^http:.*/.test(settings.url) || /^https:.*/.test(settings.url))) {
                // Only send the token to relative URLs i.e. locally.
                xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
            }
        }
    });

    const fadeout_cart = function(callback) {
        $("#cart").fadeOut();
        $("#total").fadeOut(400, callback);
    }

    const fadein_cart = function(callback) {
        $("#cart").fadeIn();
        $("#total").fadeIn(400, callback);
    }

    refresh_cart = function(callback) {
      $("#cart-error").fadeOut();
      $.getJSON(URL_REGISTRATION_ONSITE_ADMIN_CART, function(data) {
        cartData = data;
        var enable_print = false;
        var onHold = false;
        if (data.success) {
          cartTemplateData = [];
          orderItemsData = {};
          $.each( data.result, function( key, val ) {
            var level = "?";
            var price = "?";
            var state = "danger";
            if (val.effectiveLevel != null) {
                    level = val.effectiveLevel.name;
                    price = val.effectiveLevel.price;
                    state = "";
            }

            cartTemplateData.push({
                  name : val.firstName + ' ' + val.lastName,
                  badgeName : val.badgeName,
                  badgeNumber : val.badgeNumber,
                  age : val.age,
                  abandoned : val.abandoned,
                  level : level,
                  price : price,
                  printed : val.printed,
                  delete_id : "delete-" + val.id,
                  items_id: "order-items-" + val.id,
                  state : state,
                  holdType : val.holdType,
                  discount: val.discount,
                  level_discount: val.level_discount,
                  level_subtotal: val.level_subtotal,
                  level_total: val.level_total
            });
            orderItemsData[val.id] = val.attendee_options;

            if (val.discount) {
                orderItemsData[val.id].push({
                    quantity: 1,
                    item: "Discount "+val.discount.name,
                    price: "-"+val.discount.amount_off+" / "+val.discount.percent_off+"%",
                    total: "-$" + val.level_discount
                });
            }

            if (!!val.holdType) {
              onHold = true;
              enable_print = false;
            }
          });
          $("#total").html("");
          $("#cart").html("");
          $("#cart").loadTemplate($("#cartTemplate"), cartTemplateData);
          $(".remove-badge").click(remove_badge);
          $(".link-badge").click(link_badge);

          $.each(orderItemsData, function(key, val) {
              $("#order-items-"+key).loadTemplate($("#itemRowTemplate"), val);
          });

          var price = parseFloat(data.total);
          if (((!isNaN(price))) && (!onHold)) {
              $("#total").loadTemplate($("#totalTemplate"), data);
              $("#cash_button").removeAttr("disabled");
              $("#credit_button").removeAttr("disabled");
          } else {
              $("#cash_button").attr("disabled", "disabled");
              $("#credit_button").attr("disabled", "disabled");
          }

          if (isNaN(price) || (price == 0)) {
              $("#cash_button").attr("disabled", "disabled");
              $("#credit_button").attr("disabled", "disabled");
          }

          get_printable();
        }

        if (typeof(callback) === 'function') {
            callback();
        }

      })
      .fail(function (data) {
          $("#cart-error").html("A server error occurred while refreshing the cart<br>"+data.message).fadeIn();
      });
    };

    refresh_cart();
    $("#refresh_button").click(function (e) {
        e.preventDefault();
        fadeout_cart(function () {
            refresh_cart(function () {
                fadein_cart();
            });

        })
    });

    $(".add-badge").click(function (e) {
        e.preventDefault();
        var id = $(this).data("id");
        $(this).attr("disabled", "disabled");
        $.getJSON(URL_REGISTRATION_ONSITE_ADMIN_ADD_TO_CART, { id : id }, function (data) {
            if (data.success) {
                refresh_cart();
            } else {
                alert("Error while adding to cart");
            }
        });
    });

    $("#open-terminal").click(function (e) {
        e.preventDefault();
        $.getJSON(URL_REGISTRATION_OPEN_TERMINAL, {}, function (data) {
            if (!data.success) {
                alert("Error while opening terminal: " + data.message);
            }
        });
    });

    $("#close-terminal").click(function (e) {
        e.preventDefault();
        $.getJSON(URL_REGISTRATION_CLOSE_TERMINAL, {}, function (data) {
            if (!data.success) {
                alert("Error while closing terminal: " + data.message);
            }
        });
    });
    
    
    $("#open-drawer").click(function (e) {
        e.preventDefault();
        raw_amount = prompt("Enter initial amount in drawer");
        if (raw_amount == null || raw_amount === "") {
            return
        }
        parsed = parseFloat(raw_amount.match(/(\d+).?(\d{0,2})?/));
        if (parsed == 0 || isNaN(parsed)) {
            return
        }
        data = {
            'amount' : parsed
        }
        $.post(URL_REGISTRATION_OPEN_DRAWER, data, function (data) {
            if (!data.success) {
                alert("Error while opening drawer: " + data.message);
            } else {
                alert("Successfully opened drawer!")
            }
        },'json');
    });

    $("#cash-deposit").click(function (e) {
        e.preventDefault();
        raw_amount = prompt("Enter amount added to drawer");
        if (raw_amount == null || raw_amount === "") {
            return
        }
        parsed = parseFloat(raw_amount.match(/(\d+).?(\d{0,2})?/));
        if (parsed == 0) {
            return
        }
        data = {
            'amount' : parsed
        }
        $.post(URL_REGISTRATION_CASH_DEPOSIT, data, function (data) {
            if (!data.success) {
                alert("Error recording cash deposit: " + data.message);
            } else {
                alert("Successfully recorded cash deposit!")
            }
        },'json');
    });

    $("#safe-drop").click(function (e) {
        e.preventDefault();
        raw_amount = prompt("Enter amount dropped into safe");
        if (raw_amount == null || raw_amount === "") {
            return
        }
        parsed = parseFloat(raw_amount.match(/(\d+).?(\d{0,2})?/));
        if (parsed == 0) {
            return
        }
        data = {
            'amount' : parsed,
        }
        $.post(URL_REGISTRATION_SAFE_DROP, data, function (data) {
            if (!data.success) {
                alert("Error while recording safe drop: " + data.message);
            } else {
                alert("Successfully recorded safe drop!")
            }
        },'json');
    });

    $("#cash-pickup").click(function (e) {
        e.preventDefault();
        raw_amount = prompt("Enter amount picked up from drawer");
        if (raw_amount == null || raw_amount === "") {
            return
        }
        parsed = parseFloat(raw_amount.match(/(\d+).?(\d{0,2})?/));
        if (parsed == 0) {
            return
        }
        data = {
            'amount' : parsed
        }
        $.post(URL_REGISTRATION_CASH_PICKUP, data, function (data) {
            if (!data.success) {
                alert("Error recording cash pickup: " + data.message);
            } else {
                alert("Successfully recorded cash pickup!")
            }
        },'json');
    });

    $("#close-drawer").click(function (e) {
        e.preventDefault();
        raw_amount = prompt("Enter final amount in drawer");
        if (raw_amount == null || raw_amount === "") {
            return
        }
        parsed = parseFloat(raw_amount.match(/(\d+).?(\d{0,2})?/));
        if (parsed == 0) {
            return
        }
        data = {
            'amount' : parsed
        }
        $.post(URL_REGISTRATION_CLOSE_DRAWER, data, function (data) {
            if (!data.success) {
                alert("Error while closing drawer: " + data.message);
            } else {
                alert("Successfully closed drawer!")
            }
        },'json');
    });


    $("#credit_button").click(function (e) {
        e.preventDefault();
        $.getJSON(URL_REGISTRATION_ENABLE_PAYMENT, {}, function (data) {
            if (!data.success) {
                alert("Error while closing terminal: " + data.message);
            }
        });
    });

    $("#cash_button").click(function (e) {
        e.preventDefault();
        tendered = prompt("Enter tendered amount");
        parsed = parseFloat(tendered.match(/(\d+).?(\d{0,2})?/));
        total = parseFloat(cartData.total);
        if (parsed < total) {
            alert("Insufficient payment. (Split tender unsupported)");
            return;
        }

        change = parsed - total;

        data = {
            'reference' : cartData.reference,
            'total' : total,
            'tendered' : parsed
        }
        $.getJSON(URL_REGISTRATION_COMPLETE_CASH_TRANSACTION, data, function (data) {
            if (data.success) {
                refresh_cart();
            } else {
                alert("Error while posting transaction to server");
            }
        });

        alert("Change: $" + change);

    });


    var remove_badge = function (e) {
        e.preventDefault();
        var id = $(this).attr("id").split("-")[1];
        $.getJSON(URL_REGISTRATION_ONSITE_REMOVE_FROM_CART, { id : id }, function (data) {
            if (data.success) {
                refresh_cart();
            } else {
                alert("Error while removing from cart");
            }
        }).fail(function() {
            window.reload();
        });
    };

    var link_badge = function (e) {
        e.preventDefault();
        var id = $(this).attr("id").split("-")[1];
        var url = URL_ADMIN_REGISTRATION_BADGE.replace('0', id);
        window.open(url, '_blank');
    };

    var add_discount = function(e) {
    }

    $("#pos").change(function () {
      $("#terminal_form").submit();
    });

    $("#print_button").click(print_badges);



});
