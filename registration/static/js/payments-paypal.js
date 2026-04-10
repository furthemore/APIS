if (window.paypal) {
    const paypalButtons = window.paypal.Buttons({
        style: {
            shape: "rect",
            layout: "vertical",
            color: "gold",
            label: "paypal",
        },
        async createOrder() {
            try {
                const response = await postJSON(
                    URL_REGISTRATION_CREATEORDER,
                    JSON.stringify({
                        charityDonation: $("#donateCharity").val(),
                        orgDonation: $("#donateOrg").val()
                    })
                );

                const orderResponse = await response.json();

                if (orderResponse?.success && orderResponse?.reason?.id) {
                    return orderResponse.reason.id;
                }
                
                const errorDetail = orderResponse?.reason.details?.[0];
                const errorMessage = errorDetail
                    ? `${errorDetail.issue} ${errorDetail.description} (${orderResponse.debug_id})`
                    : orderResponse.reason

                throw new Error(errorMessage);
            } catch (error) {
                console.error(error);
                displayPaymentResults(
                    `Could not initiate PayPal Checkout:<br>${error}`, true
                );
            }
        },
        async onApprove(data, actions) {
            hidePaymentResults();
            try {
                const response = await postJSON(
                    URL_REGISTRATION_CHECKOUT,
                    JSON.stringify({
                        orderID: data.orderID,
                        onsite: false,
                        billingData: {
                            cc_firstname: $("#fname").val(),
                            cc_lastname: $("#lname").val(),
                            email: $("#email").val(),
                            address1: $("#add1").val(),
                            address2: $("#add2").val(),
                            city: $("#city").val(),
                            state: $("#state").val(),
                            country: $("#country").val(),
                            postal: $("#postal").val(),
                        },
                        charityDonation: $("#donateCharity").val(),
                        orgDonation: $("#donateOrg").val()
                    })
                );

                const paymentResults = await response.json();
                // Three cases to handle:
                //   (1) Recoverable INSTRUMENT_DECLINED -> call actions.restart()
                //   (2) Other non-recoverable errors -> Show a failure message
                //   (3) Successful transaction -> Show confirmation or thank you message

                if (paymentResults.success) {
                    // (3) Successful transaction -> Show confirmation or thank you message
                    // Or go to another URL:  actions.redirect('thank_you.html');
                    console.log(
                        "Capture result",
                        paymentResults,
                        JSON.stringify(paymentResults, null, 2)
                    );
                    displayPaymentResults('');
                    window.location = URL_REGISTRATION_DONE;
                } else {
                    const errorDetail = paymentResults.reason.details?.[0];

                    if (errorDetail?.issue === "INSTRUMENT_DECLINED") {
                        // (1) Recoverable INSTRUMENT_DECLINED -> call actions.restart()
                        // recoverable state, per
                        // https://developer.paypal.com/docs/checkout/standard/customize/handle-funding-failures/
                        throw new Error(`
                            Sorry, your payment failed for a mysterious reason 
                            (${errorDetail.description} [${orderData.debug_id}]).
                            If the problem persists, please contact
                            <a href="mailto:${EVENT_REGISTRATION_EMAIL}">${EVENT_REGISTRATION_EMAIL}</a>
                            for assistance.</p>
                        `);
                    } else if (errorDetail) {
                        // (2) Other non-recoverable errors -> Show a failure message
                        throw new Error(`
                            Sorry, your payment failed for the following reason:<br>
                            ${errorDetail.description} (${paymentResults.debug_id}).<br>
                            If the problem persists, please contact
                            <a href="mailto:${EVENT_REGISTRATION_EMAIL}">${EVENT_REGISTRATION_EMAIL}</a>
                            for assistance.</p>
                        `);
                    } else {
                        // APIS error - likely a failure to send mail.
                        throw new Error(paymentResults.reason);
                    }
                }
            } catch (error) {
                displayPaymentResults(error, true);
            }
        },
    });
    paypalButtons.render("#card-container");
}


// Helper method for displaying the Payment Status on the screen.
function displayPaymentResults(message, isError) {
    const statusContainer = document.getElementById('payment-status-container');
    statusContainer.innerHTML = message;

    if (!isError) {
        statusContainer.classList.remove('is-failure');
        statusContainer.classList.add('is-success');
    } else {
        statusContainer.classList.remove('is-success');
        statusContainer.classList.add('is-failure');
    }

    statusContainer.style.visibility = 'visible';
}

function hidePaymentResults() {
    const statusContainer = document.getElementById('payment-status-container');
    statusContainer.style.visibility = 'hidden';
}
