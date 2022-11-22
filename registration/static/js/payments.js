async function initializeCard(payments) {
    const card = await payments.card();
    await card.attach('#card-container');
    return card;
}

// This function tokenizes a payment method.
// The ‘error’ thrown from this async function denotes a failed tokenization,
// which is due to buyer error (such as an expired card). It is up to the
// developer to handle the error and provide the buyer the chance to fix
// their mistakes.
async function tokenize(paymentMethod) {
    const tokenResult = await paymentMethod.tokenize();
    if (tokenResult.status === 'OK') {
        return tokenResult.token;
    } else {
        let errorMessage = `Tokenization failed-status: ${tokenResult.status}`;
        if (tokenResult.errors) {
            errorMessage += ` and errors: ${JSON.stringify(
                tokenResult.errors
            )}`;
        }
        throw new Error(errorMessage);
    }
}

// Helper method for displaying the Payment Status on the screen.
// status is either SUCCESS or FAILURE;
function displayPaymentResults(status, message) {
    const statusContainer = document.getElementById('payment-status-container');
    statusContainer.innerHTML = message;

    if (status === 'SUCCESS') {
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

class PaymentError extends Error {
    constructor(message, response) {
        super(message);
        this.response = response;
        this.name = "PaymentError";
    }
}

async function createPayment(token, url) {
    const body = JSON.stringify({
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
            source_id: token,
        },
        charityDonation: $("#donateCharity").val(),
        orgDonation: $("#donateOrg").val()
    });

    const response = await postJSON(URL_REGISTRATION_CHECKOUT, body);
    if (response.ok) {
        return response.json();
    } else if (response.status == 409) {
        // Probably actually an idempotent success
        return response.json();
    }

    const paymentResponseText = await response.text();

    try {
        return JSON.parse(paymentResponseText);
    } catch (e) {
        throw new PaymentError(`Payment failed: ${response.status} ${response.statusText} while making request`, response);
    }
}

document.addEventListener('DOMContentLoaded', async function () {
    if (!window.Square) {
        throw new Error('Square.js failed to load properly');
    }
    const payments = window.Square.payments(APPLICATION_ID, LOCATION_ID);
    let card;
    try {
        card = await initializeCard(payments);
    } catch (e) {
        console.error('Initializing Card failed', e);
        return;
    }

    function formatSquareErrors(errors) {
        const errorCodes = errors.map((obj) => obj.code);
        return errorCodes.join(', ')
    }

    async function handlePaymentMethodSubmission(event, paymentMethod) {
        event.preventDefault();
        hidePaymentResults();

        try {
            // disable the submit button as we await tokenization and make a
            // payment request.
            cardButton.disabled = true;

            $("form").validator('validate');
            const errorCount = $(".has-error").length;
            if (errorCount > 0) {
                cardButton.disabled = false;
                return;
            }

            const token = await tokenize(paymentMethod);
            const paymentResults = await createPayment(token);
            // Subsequent requests will need a new idempotency key
            IDEMPOTENCY_KEY = crypto.randomUUID();
            if (paymentResults.success) {
                displayPaymentResults('SUCCESS', '');
                window.location = URL_REGISTRATION_DONE;
            } else {
                let message;
                try {
                    const errorCodes = formatSquareErrors(paymentResults.reason.errors);
                    message = `<p>Payment error: payment failed for the following reasons:` +
                        `<br><span class="error-code">${errorCodes}</span>.<br>  Please check your payment details `+
                        `carefully and try again.</p>`;

                } catch (e) {
                    message = `<p>Sorry, your payment failed for a mysterious reason. If the problem persists, please ` +
                        `contact <a href="mailto:${EVENT_REGISTRATION_EMAIL}">${EVENT_REGISTRATION_EMAIL}</a> for assistance.</p>`;
                }

                displayPaymentResults('FAILURE', message);
                console.log(paymentResults.reason);
            }

            console.debug('Payment result:', paymentResults);
            cardButton.disabled = false;
        } catch (err) {
            if (err instanceof PaymentError) {
                IDEMPOTENCY_KEY = crypto.randomUUID();
            }
            cardButton.disabled = false;
            displayPaymentResults('FAILURE', err.message);
            console.error(err.message);
        }
    }

    const cardButton = document.getElementById('checkout');
    cardButton.addEventListener('click', async function (event) {
        await handlePaymentMethodSubmission(event, card);
    });

    const postal_callback = async (cardInputEvent) => {
        const postal_input = document.getElementById('postal');
        postal_input.value = cardInputEvent.detail.postalCodeValue;
    };
    card.addEventListener("postalCodeChanged", postal_callback);
});