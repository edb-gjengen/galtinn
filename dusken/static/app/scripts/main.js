'use strict';
var urls, csrfToken;

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

function onToken(token) {
    // Use the token to create the charge with a server-side script.
    // You can access the token ID with `token.id` and user email with `token.email`
    var postData = {
        'stripe_token': token,
        'user': getFormData($('#user-form'))
    };
    $.ajax(urls.charge, {
        data: JSON.stringify(postData),
        contentType: 'application/json',
        dataType: 'json',
        type: 'post',
        headers: {'X-CSRFToken': csrfToken}
    }).success(function(data) {
        // TODO: with success message
        console.log(data);

        // redirect to profile
        location.href = urls.profile;
    }).fail(function(data) {
        console.log('failed', data);
    });
}


$(document).ready(function() {
    if($('.membership-purchase').length) {

        /* Membership purchase */
        urls = {
            charge: '/membership/charge/',
            profile: '/home/'
        };
        csrfToken = $('[name="x-csrf-token"]').attr('content');

        var stripeHandler = StripeCheckout.configure({
            key: config.stripe_pub_key,
            image: config.logo,
            locale: 'auto',
            token: onToken,
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

    }
});
