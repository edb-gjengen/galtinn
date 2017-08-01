'use strict';
var urls, csrfToken;

function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function csrfSafeMethod(method) {
    // these HTTP methods do not require CSRF protection
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}

$.ajaxSetup({
    beforeSend: function(xhr, settings) {
        if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
            xhr.setRequestHeader('X-CSRFToken', getCookie('csrftoken'));
        }
    }
});

function getFormData(formElement) {
    var formData = formElement.serializeArray();
    formData = _.object(_.map(formData, function (x) {
        return [x.name, x.value];
    }));

    return formData;
}

function serverValidation(formData) {
    $.ajax({
        url: '/api/validate/',
        data: {
            'email': formData.email,
            'number': formData.phone_number
        },
        dataType: 'json',
        formData: formData,
        success: function (serverData) {
            validate(this.formData, serverData);
        }
    });
}

function validate(formData, serverData) {
    clearError();
    var errors = [];
    if ($.trim(formData.first_name) === '') {
        $('#id_first_name').parent().addClass('has-danger');
        errors.push(serverData.missing_first_name);
    }
    if ($.trim(formData.last_name) === '') {
        $('#id_last_name').parent().addClass('has-danger');
        errors.push(serverData.missing_last_name);
    }
    if (serverData.email_message) {
        $('#id_email').parent().addClass('has-danger');
        errors.push(serverData.email_message);
    }
    if (serverData.number_message) {
        $('#id_phone_number').parent().addClass('has-danger');
        errors.push(serverData.number_message);
    }
    if (errors.length) {
        displayError(errors.join('<br>'));
    } else {
        openStripe(formData.email);
    }
}

function openStripe(email) {
    var stripeHandler = StripeCheckout.configure({
        key: config.stripe_pub_key,
        image: config.image,
        locale: 'auto',
        token: onStripeToken,
        allowRememberMe: false  // Disallow the remember me function for new users
    });

    // Open Checkout with further options
    stripeHandler.open({
        name: 'Det Norske Studentersamfund',
        description: config.membership_name,
        currency: 'NOK',
        amount: config.membership_price,
        email: email
    });

    // Close Checkout on page navigation
    $(window).on('popstate', function() {
        stripeHandler.close();
    });
}

function onStripeToken(token) {
    // Use the token to create the charge with a server-side script.
    // You can access the token ID with `token.id` and user email with `token.email`
    var postData = {
        'stripe_token': token,
        'membership_type': config.membership_type
    };
    $.ajax(urls.charge, {
        data: JSON.stringify(postData),
        contentType: 'application/json',
        dataType: 'json',
        type: 'post'
    }).done(function(data) {
        // TODO: with success message
        console.log(data);

        // redirect to profile
        location.href = urls.profile;
    }).fail(function(data) {
        console.log('failed', data);
        $('.js-validation-errors').addClass('alert alert-danger');
        $('.js-validation-errors').html(JSON.parse(data.responseText).error)
    });
}

function displayError(message) {
    $('.js-validation-errors').html(message);
    $('.js-validation-errors').addClass('alert alert-danger');
}

function clearError() {
    $('.js-validation-errors').html('');
    $('.js-validation-errors').removeClass('alert alert-danger');
    $('#id_first_name').parent().removeClass('has-danger');
    $('#id_last_name').parent().removeClass('has-danger');
    $('#id_email').parent().removeClass('has-danger');
    $('#id_phone_number').parent().removeClass('has-danger');
}

$(document).ready(function() {
    const $membershipPurchase = $('.membership-purchase');
    const $mailchimpSub = $('.js-toggle-mailchimp-subscription');
    const $mailmanSub = $('.js-toggle-mailman-subscription');

    if( $membershipPurchase.length ) {

        /* Membership purchase */
        urls = {
            charge: config.charge_url,
            profile: '/home/'
        };

        $('#purchase-button').on('click', function(e) {
            e.preventDefault();
            serverValidation(getFormData($('#user-form')));
        });

        $('#renew-button').on('click', function(e) {
            e.preventDefault();
            openStripe(getFormData($('#user-form')).email);
        });

    }
    /* Send validation email */
    var $validationEmailBtn = $('.js-send-validation-email');
    $validationEmailBtn.on('click', function (e) {
        e.preventDefault();
        $.post(config.validateEmail, function(data) {
            $validationEmailBtn.text('Sent.')
        })
    });

    /* Hidden language select */
    const $languageToggle = $('.js-language-select-toggle');
    const $languageSelect = $('.language-select');
    $languageToggle.on('click', function (e) {
       e.preventDefault();
       $languageSelect.toggleClass('hidden');
       if( !$languageSelect.hasClass('hidden') ) {
           $languageSelect.focus();
       }
    });

    /* Page: Newsletter and mailing list */
    if( $mailchimpSub.length ) {
        const $subLabel = $('[for=id_mailchimp_subscription]');

        let url = config.mailChimpSubscriptionListURL;
        let method = 'POST';
        const sub = config.mailChimpSubscription;
        if( sub ) {
            url = config.mailChimpSubscriptionDetailURL;
            method = 'PATCH';
        }
        $mailchimpSub.on('change', (e) => {
            const shouldSubscribe = $mailchimpSub.prop('checked');
            const data = {
                status: shouldSubscribe ? 'subscribed' : 'unsubscribed',
                email: config.userEmail
            };
            const newLabel = shouldSubscribe ? $subLabel.attr('data-text-unsubscribe') : $subLabel.attr('data-text-subscribe');

             $.ajax( {url: url, data: JSON.stringify(data), method: method, contentType: 'application/json', dataType: 'json'})
              .done(function() {
                  $subLabel.find('span').text(newLabel);
                  if(shouldSubscribe) {
                      $subLabel.addClass('active');
                  } else {
                      $subLabel.removeClass('active')
                  }
                  // TODO: Add sucess message
              })
              .fail(function() {
                  $mailchimpSub.prop('checked', !shouldSubscribe);
                  // TODO: Add failed message
              })
        })
    }

    if( $mailmanSub.length ) {
        // TODO: Add toggle subscritions
    }

});
