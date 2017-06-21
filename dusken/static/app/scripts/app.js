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
        url: '/validate/',
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
        'user': getFormData($('#user-form')),
        'product': config.membership_type
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
        // TODO: Format error as HTML
        $('.js-validation-errors').html('<div class="alert-danger">'+ data.responseText +'</div>')
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
    if($('.membership-purchase').length) {

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
    })

});
