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

function isFormValid() {
    // TODO: Feedback to the user
    var formData = getFormData($('#user-form'));
    var isNotValid = _.any(_.values(formData), function(value) {
        /* empty? */
        return $.trim(value) === '';
    });

    return !isNotValid;
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
        $('.js-validation-errors').html('<div class="alert-danger">'+ JSON.stringify(data) +'</div>')
    });
}

var emailError = '';
var phoneNumberError = '';
function validationErrorHandler() {
    var message = emailError;
    if (phoneNumberError.length && emailError.length) {
        message += '<br>';
    }
    message += phoneNumberError;
    $('.js-validation-errors').html(message);
    if (message.length) {
        $('.js-validation-errors').addClass('alert alert-danger');
        $('#purchase-button').attr('disabled', true);
    } else {
        $('.js-validation-errors').removeClass('alert alert-danger');
        $('#purchase-button').removeAttr('disabled');
    }
}

function emailValidation() {
    var email = $('#id_email').val();
    if (email === '') {
        return;
    }

    $.ajax({
        url: '/validate/email/',
        data: {
            'email': email
        },
        dataType: 'json',
        success: function (data) {
            if (data.message) {
                $('#id_email').parent().addClass('has-danger');
                emailError = data.message;
            } else {
                $('#id_email').parent().removeClass('has-danger');
                emailError = '';
            }
            validationErrorHandler();
        }
    });
}

function phoneNumberValidation() {
    var phone_number = $('#id_phone_number').val();

    $.ajax({
        url: '/validate/phone_number/',
        data: {
            'phone_number': phone_number
        },
        dataType: 'json',
        success: function (data) {
            if (data.message) {
                $('#id_phone_number').parent().addClass('has-danger');
                phoneNumberError = data.message;
            } else {
                $('#id_phone_number').parent().removeClass('has-danger');
                phoneNumberError = '';
            }
            validationErrorHandler();
        }
    });
}

$(document).ready(function() {
    if($('.membership-purchase').length) {

        /* Membership purchase */
        urls = {
            charge: config.charge_url,
            profile: '/home/'
        };

        var stripeHandler = StripeCheckout.configure({
            key: config.stripe_pub_key,
            image: config.image,
            locale: 'auto',
            token: onStripeToken,
            allowRememberMe: false  // Disallow the remember me function for new users
        });

        $('#purchase-button').on('click', function(e) {
            e.preventDefault();

            if( !isFormValid() ) {
                console.log('not valid!');
            } else {
                // Open Checkout with further options
                stripeHandler.open({
                    name: 'Det Norske Studentersamfund',
                    description: config.membership_name,
                    currency: 'NOK',
                    amount: config.membership_price,
                    email: $('#id_email').val()
                });
            }
        });

        // Close Checkout on page navigation
        $(window).on('popstate', function() {
            stripeHandler.close();
        });

        $('#id_email').change(emailValidation);
        $('#id_phone_number').change(phoneNumberValidation);
        emailValidation();
        phoneNumberValidation();
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
