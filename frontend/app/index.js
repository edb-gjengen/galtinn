import $ from 'jquery';
window.$ = window.jQuery = $;

import 'select2';

import 'bootstrap/js/dist/collapse';
import 'bootstrap/js/dist/dropdown';

import './OrgUnit';

import './styles/app.scss';

let urls;

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === name + '=') {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function csrfSafeMethod(method) {
    // these HTTP methods do not require CSRF protection
    return /^(GET|HEAD|OPTIONS|TRACE)$/.test(method);
}

$.ajaxSetup({
    beforeSend: function (xhr, settings) {
        if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
            xhr.setRequestHeader('X-CSRFToken', getCookie('csrftoken'));
        }
    },
});

function openStripe(email) {
    const stripeHandler = StripeCheckout.configure({
        key: stripe_config.stripe_pub_key,
        image: stripe_config.image,
        locale: 'auto',
        token: onStripeToken,
        allowRememberMe: false, // Disallow the remember me function for new users
    });

    // Open Checkout with further options
    stripeHandler.open({
        name: 'Det Norske Studentersamfund',
        description: stripe_config.membership_name,
        currency: 'NOK',
        amount: stripe_config.membership_price,
        email: email,
    });

    // Close Checkout on page navigation
    $(window).on('popstate', function () {
        stripeHandler.close();
    });
}

function onStripeToken(token) {
    // Use the token to create the charge with a server-side script.
    // You can access the token ID with `token.id` and user email with `token.email`
    const postData = {
        stripe_token: token,
        membership_type: stripe_config.membership_type,
    };
    $.ajax(urls.charge, {
        data: JSON.stringify(postData),
        contentType: 'application/json',
        dataType: 'json',
        type: 'post',
    })
        .done(function (data) {
            console.log(data);

            // redirect to profile
            location.href = urls.profile + '?payment_success=✔';
        })
        .fail(function (data) {
            console.log('failed', data);
            $('.js-validation-errors').addClass('alert alert-danger');
            $('.js-validation-errors').html(JSON.parse(data.responseText).detail);
        });
}

function formatMessage(message, alert) {
    return (
        '<div class="alert alert-' +
        alert +
        ' alert-dismissible fade show" role="alert">' +
        '<button type="button" class="close" data-dismiss="alert" aria-label="Close"><span aria-hidden="true">&times;</span></button>' +
        message +
        '</div>'
    );
}

$(document).ready(function () {
    const $membershipPurchase = $('#membership-purchase-form');
    const $messages = $('.messages');

    if ($membershipPurchase.length) {
        /* Membership purchase */
        urls = {
            charge: stripe_config.charge_url,
            profile: '/home/',
        };

        const email = $membershipPurchase.find('input[name="email"]').val();

        $('#purchase-button').on('click', function (e) {
            e.preventDefault();
            openStripe(email);
        });
    }
    /* Send validation email */
    const $validationEmailBtn = $('.js-send-validation-email');
    $validationEmailBtn.on('click', function (e) {
        e.preventDefault();
        $.post(config.validateEmail, function (data) {
            $validationEmailBtn.text('Sent.');
        });
    });

    /* Hidden language select */
    const $languageToggle = $('.js-language-select-toggle');
    const $languageSelect = $('.language-select');
    $languageToggle.on('click', function (e) {
        e.preventDefault();
        $languageSelect.toggleClass('hidden');
        if (!$languageSelect.hasClass('hidden')) {
            $languageSelect.focus();
        }
    });

    /* View user (from select2 dropdown) */
    $('.js-view-user').on('click', () => {
        let user = null;
        try {
            user = $('#id_user').select2('data')[0].id;
        } catch (err) {
            return;
        }
        $.ajax({
            url: '/api/user/pk/to/uuid/',
            data: {
                user: user,
            },
            dataType: 'json',
            success: function (response) {
                window.location.href = '/users/' + response.uuid;
            },
            error: function () {
                alert('Failed view user');
            },
        });
    });
});
