import $ from 'jquery';
window.$ = window.jQuery = $;

import 'select2';

import 'bootstrap/js/dist/collapse';
import 'bootstrap/js/dist/dropdown';

import './OrgUnit';

import './styles/app.scss';

let urls, csrfToken;

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
    const $mailchimpSub = $('.js-toggle-mailchimp-subscription');
    const $mailmanSub = $('.js-toggle-mailman-subscription');
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

    /* Page: Newsletter and mailing lists */
    if ($mailchimpSub.length) {
        const $subStatus = $('.js-mailchimp-status');

        let url = config.mailChimpSubscriptionListURL;
        let method = 'POST';
        const sub = config.mailChimpSubscription;
        if (sub) {
            url = config.mailChimpSubscriptionDetailURL;
            method = 'PATCH';
        }
        $mailchimpSub.on('click', (e) => {
            e.preventDefault();

            const shouldSubscribe = !$mailchimpSub.hasClass('subscribed');
            const data = {
                status: shouldSubscribe ? 'subscribed' : 'unsubscribed',
                email: config.userEmail,
            };
            const newButtonText = shouldSubscribe
                ? $mailchimpSub.attr('data-text-unsubscribe')
                : $mailchimpSub.attr('data-text-subscribe');
            const newStatusText = shouldSubscribe
                ? $subStatus.attr('data-text-subscribed') + ' ✅'
                : $subStatus.attr('data-text-unsubscribed') + ' ❌';

            $.ajax({
                url: url,
                data: JSON.stringify(data),
                method: method,
                contentType: 'application/json',
                dataType: 'json',
            })
                .done(function () {
                    $mailchimpSub.text(newButtonText);
                    $subStatus.text(newStatusText);

                    if (shouldSubscribe) {
                        $mailchimpSub.addClass('subscribed');
                    } else {
                        $mailchimpSub.removeClass('subscribed');
                    }
                })
                .fail(function () {
                    $messages.html(
                        formatMessage(
                            'Could not change newsletter subscription status, please try again later...',
                            'danger'
                        )
                    );
                });
        });
    }

    if ($mailmanSub.length) {
        $mailmanSub.on('click', (e) => {
            e.preventDefault();
            const $thisList = $(e.target);
            const $thisStatus = $('.js-mailman-status[data-list-name="' + $thisList.attr('data-list-name') + '"]');

            const shouldSubscribe = !$thisList.hasClass('subscribed');
            const url = $thisList.attr('data-url');
            const method = shouldSubscribe ? 'PUT' : 'DELETE';

            const newButtonText = shouldSubscribe
                ? $thisList.attr('data-text-unsubscribe')
                : $thisList.attr('data-text-subscribe');
            const newStatusText = shouldSubscribe ? '✅' : '❌';

            $.ajax({
                url: url,
                method: method,
                contentType: 'application/json',
                dataType: 'json',
            })
                .done(function () {
                    $thisList.text(newButtonText);
                    $thisStatus.text(newStatusText);

                    if (shouldSubscribe) {
                        $thisList.addClass('subscribed');
                    } else {
                        $thisList.removeClass('subscribed');
                    }
                })
                .fail(function () {
                    $thisList.prop('checked', !shouldSubscribe);
                    $messages.html(
                        formatMessage('Could not change subscription status, please try again later...', 'danger')
                    );
                });
        });
    }

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
