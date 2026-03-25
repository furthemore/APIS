// ==== forms ====
function getAgeByEventStart(birthdate) {
    if (typeof event_start_date !== 'undefined') {
        const diff = event_start_date.getTime() - birthdate.getTime();
        return Math.floor(diff / (1000 * 60 * 60 * 24 * 365.25));
    }
    throw TypeError("event_start_date is undefined (perhaps event was not passed to your template)");
}

function getAge(birthdate) {
    let diff = new Date().getTime() - birthdate.getTime();
    return Math.floor(diff / (1000 * 60 * 60 * 24 * 365.25));
}

function toDateFormat(birthdate){
    let month = birthdate.getMonth();
    month = month + 1;
    return month + "/" + birthdate.getDate() + "/" + birthdate.getFullYear();
}

function parseDate(input) {
    // parse an ISO formatted date as localtime
    const parts = input.split('-');
    return new Date(parts[0], parts[1]-1, parts[2]);
}

function setTwoNumberDecimal(e) {
    this.value = parseFloat(this.value).toFixed(2);
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie != '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) == (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

async function postJSON(url, body) {
    let headers = {
        'Content-Type': 'application/json',
    };
    if (!(/^http:.*/.test(url) || /^https:.*/.test(url))) {
        headers['X-CSRFToken'] = getCookie('csrftoken');
        headers['IDEMPOTENCY-KEY'] = IDEMPOTENCY_KEY;
    }

    return fetch(URL_REGISTRATION_CHECKOUT, {
        method: 'POST',
        headers: headers,
        body,
    })
}

// ==== price level card animations ====
function animateLevelSelect(container, afterFade) {
    var cards = container.find('.card');
    if (cards.length === 0) {
        afterFade();
        return;
    }
    cards.addClass('level-card-exit');
    setTimeout(afterFade, 200);
}

function revealLevelCards(container) {
    container.find('[class*="col-"]').each(function (i) {
        $(this).find('.card')
            .css('animation-delay', (i * 70) + 'ms')
            .addClass('level-card-enter');
    });
}

// FLIP: animate the newly placed card from startRect (where it was) to its natural position.
function flipCardToPosition($card, startRect) {
    if (!startRect || !$card.length) {
        $card.closest('#levelContainer').length && revealLevelCards($card.closest('#levelContainer'));
        return;
    }
    var endRect = $card[0].getBoundingClientRect();
    var dx = startRect.left - endRect.left;
    var dy = startRect.top - endRect.top;

    $card.css({ transform: 'translate(' + dx + 'px, ' + dy + 'px) scale(0.88)', opacity: 0, transition: 'none' });
    void $card[0].offsetHeight; // force reflow
    $card.css({
        transition: 'transform 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94), opacity 0.22s ease-out',
        transform: 'translate(0, 0) scale(1)',
        opacity: 1,
    });
    setTimeout(function () { $card.css({ transition: '', transform: '', opacity: '' }); }, 350);
}

// ==== form validation ====
function formIsValid(form) {
    form = form || document.querySelector('form');
    form.classList.add('was-validated');
    return form.checkValidity();
}

function resetFormValidation(form) {
    (form || document.querySelector('form')).classList.remove('was-validated');
}

// ==== color scheme / dark mode ====
function setColorScheme(scheme) {
    if (scheme === 'dark') {
        document.documentElement.setAttribute('data-bs-theme', 'dark');
    } else {
        document.documentElement.removeAttribute('data-bs-theme');
    }
    localStorage.setItem('color-scheme', scheme);
    var sun = document.getElementById('theme-icon-sun');
    var moon = document.getElementById('theme-icon-moon');
    if (sun)  sun.style.display  = scheme === 'dark'  ? 'block' : 'none';
    if (moon) moon.style.display = scheme === 'light' ? 'block' : 'none';
}

function toggleColorScheme() {
    var isDark = document.documentElement.getAttribute('data-bs-theme') === 'dark';
    setColorScheme(isDark ? 'light' : 'dark');
}

$(document).ready(function (e) {
    // Sync icon to current scheme on load
    var isDark = document.documentElement.getAttribute('data-bs-theme') === 'dark';
    setColorScheme(isDark ? 'dark' : 'light');

    // Follow OS preference changes only when user hasn't set a manual override
    if (window.matchMedia) {
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', function (e) {
            if (!localStorage.getItem('color-scheme')) {
                setColorScheme(e.matches ? 'dark' : 'light');
            }
        });
    }
});

$(document).ready(function (e) {
    $.ajaxSetup({
        beforeSend: function(xhr, settings) {
            if (!(/^http:.*/.test(settings.url) || /^https:.*/.test(settings.url))) {
                // Only send the token to relative URLs i.e. locally.
                xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
                xhr.setRequestHeader("IDEMPOTENCY-KEY", IDEMPOTENCY_KEY);
            }
        }
    });
});
