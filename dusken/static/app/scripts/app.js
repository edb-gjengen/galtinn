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
        key: stripe_config.stripe_pub_key,
        image: stripe_config.image,
        locale: 'auto',
        token: onStripeToken,
        allowRememberMe: false  // Disallow the remember me function for new users
    });

    // Open Checkout with further options
    stripeHandler.open({
        name: 'Det Norske Studentersamfund',
        description: stripe_config.membership_name,
        currency: 'NOK',
        amount: stripe_config.membership_price,
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
        'membership_type': stripe_config.membership_type
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

function formatMessage(message, alert) {
    return '<div class="alert alert-' + alert + ' alert-dismissible fade show" role="alert">'+
       '<button type="button" class="close" data-dismiss="alert" aria-label="Close"><span aria-hidden="true">&times;</span></button>' +
        message +
        '</div>';
}

function remove_user(user, orgunit) {
    $.ajax({
        url: '/api/orgunit/remove/user/',
        data: {
            'user': user,
            'orgunit': orgunit
        },
        dataType: 'json',
        success: function (response) {
            if (response.success) {
                $('#user_remove_'+user).parent().parent().slideUp();
            } else {
                alert('Failed to remove user');
            }
        },
        error: function() {
            alert('Failed to remove user');
        }
    });
}

function add_user(orgunit, type) {
    const user = $('#id_user').select2('data')[0].id;
    $.ajax({
        url: '/api/orgunit/add/user/',
        data: {
            'user': user,
            'orgunit': orgunit,
            'type': type
        },
        dataType: 'json',
        success: function (response) {
            if (response.success) { // FIXME: get something better from the server instead of recreating... (this causes dual maintenance)
                $('#user_remove_'+response.user_uuid).parent().parent().slideUp();
                var icon = '<svg class="linearicon icon-user" xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 20 20"><path d="M9.5 11C6.467 11 4 8.533 4 5.5S6.467 0 9.5 0 15 2.467 15 5.5 12.533 11 9.5 11zm0-10C7.019 1 5 3.019 5 5.5S7.019 10 9.5 10 14 7.981 14 5.5 11.981 1 9.5 1zm8 19h-16C.673 20 0 19.327 0 18.5c0-.068.014-1.685 1.225-3.3.705-.94 1.67-1.687 2.869-2.219C5.558 12.33 7.377 12 9.5 12s3.942.33 5.406.981c1.199.533 2.164 1.279 2.869 2.219C18.986 16.815 19 18.432 19 18.5c0 .827-.673 1.5-1.5 1.5zm-8-7c-3.487 0-6.06.953-7.441 2.756C1.024 17.107 1.001 18.488 1 18.502a.5.5 0 0 0 .5.498h16a.5.5 0 0 0 .5-.5c0-.012-.023-1.393-1.059-2.744C15.559 13.953 12.986 13 9.5 13z"></path></svg>'
                var admin = '';
                if (type === 'admin') {
                    icon = '<svg class="linearicon icon-star" xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 20 20"><path d="M15.5 19a.497.497 0 0 1-.239-.061L10 16.07l-5.261 2.869a.499.499 0 0 1-.732-.522l.958-5.746-3.818-3.818a.501.501 0 0 1 .271-.847l5.749-.958 2.386-4.772a.5.5 0 0 1 .894 0l2.386 4.772 5.749.958a.5.5 0 0 1 .271.847l-3.818 3.818.958 5.746A.503.503 0 0 1 15.5 19zM10 15c.082 0 .165.02.239.061l4.599 2.508-.831-4.987a.497.497 0 0 1 .14-.436l3.313-3.313-5.042-.84a.5.5 0 0 1-.365-.27L10 3.617 7.947 7.723a.503.503 0 0 1-.365.27l-5.042.84 3.313 3.313a.502.502 0 0 1 .14.436l-.831 4.987 4.599-2.508A.497.497 0 0 1 10 15z"></path></svg>'
                    admin = '(' + response.admin + ')'
                }
                var li ='<li class="list-group-item justify-content-between"><span>' + icon +
                '<a href="/users/' + response.user_uuid + '/"> ' + response.user_name + '</a> - ' +
                    '<a href="mailto:' + response.user_email + '">' + response.user_email + '</a> ' + admin + '</span><span>' +
                '<button  class="btn btn-outline-primary btn-block p-1" id="user_remove_' + response.user_uuid + '"' +
                'onclick="remove_user(\'' + response.user_uuid + '\', \'' + orgunit + '\');">' + response.remove + '</button></span></li>';
                $(li).prependTo('#user_list').hide().slideDown();
            } else {
                alert('Failed to add user');
            }
        },
        error: function() {
            alert('Failed to add user');
        }
    });
}

function view_user() {
    const user = $('#id_user').select2('data')[0].id;
    $.ajax({
        url: '/api/user/pk/to/uuid/',
        data: {
            'user': user,
        },
        dataType: 'json',
        success: function (response) {
            window.location.href = '/users/' + response.uuid;
        },
        error: function() {
            alert('Failed view user');
        }
    });
}

$(document).ready(function() {
    const $membershipPurchase = $('#membership-purchase-form');
    const $mailchimpSub = $('.js-toggle-mailchimp-subscription');
    const $mailmanSub = $('.js-toggle-mailman-subscription');
    const $messages = $('.messages');

    if ($membershipPurchase.length) {
        /* Membership purchase */
        urls = {
            charge: stripe_config.charge_url,
            profile: '/home/'
        };

        $('#purchase-button').on('click', function (e) {
            e.preventDefault();
            openStripe(getFormData($('#membership-purchase-form')).email);
        });
    }
    /* Send validation email */
    const $validationEmailBtn = $('.js-send-validation-email');
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

    /* Page: Newsletter and mailing lists */
    if( $mailchimpSub.length ) {
        const $subStatus = $('.js-mailchimp-status');

        let url = config.mailChimpSubscriptionListURL;
        let method = 'POST';
        const sub = config.mailChimpSubscription;
        if( sub ) {
            url = config.mailChimpSubscriptionDetailURL;
            method = 'PATCH';
        }
        $mailchimpSub.on('click', (e) => {
            e.preventDefault();

            const shouldSubscribe = !$mailchimpSub.hasClass('active');
            const data = {
                status: shouldSubscribe ? 'subscribed' : 'unsubscribed',
                email: config.userEmail
            };
            const newButtonText = shouldSubscribe ? $mailchimpSub.attr('data-text-unsubscribe') : $mailchimpSub.attr('data-text-subscribe');
            const newStatusText = shouldSubscribe ? $subStatus.attr('data-text-subscribed') + ' ✅' : $subStatus.attr('data-text-unsubscribed') + ' ❌';

             $.ajax({
                 url: url,
                 data: JSON.stringify(data),
                 method: method,
                 contentType: 'application/json',
                 dataType: 'json'
             })
             .done(function() {
                 $mailchimpSub.text(newButtonText);
                 $subStatus.text(newStatusText);

                 if(shouldSubscribe) {
                     $mailchimpSub.addClass('active');
                 } else {
                     $mailchimpSub.removeClass('active');
                 }
             })
             .fail(function() {
                 $messages.html(formatMessage('Could not change newsletter subscription status, please try again later...', 'danger'));
             });
        });
    }

    if( $mailmanSub.length ) {

        $mailmanSub.on('click', (e) => {
            e.preventDefault();
            const $thisList = $(e.target);
            const $thisStatus = $('.js-mailman-status[data-list-name="'+ $thisList.attr('data-list-name') +'"]');

            const shouldSubscribe = !$thisList.hasClass('active');
            const url = $thisList.attr('data-url');
            const method = shouldSubscribe ? 'PUT' : 'DELETE';

            const newButtonText = shouldSubscribe ? $thisList.attr('data-text-unsubscribe') : $thisList.attr('data-text-subscribe');
            const newStatusText = shouldSubscribe ? '✅' : '❌';

             $.ajax({
                 url: url,
                 method: method,
                 contentType: 'application/json',
                 dataType: 'json'
             })
             .done(function() {
                 $thisList.text(newButtonText);
                 $thisStatus.text(newStatusText);

                  if(shouldSubscribe) {
                     $thisList.addClass('active');
                  } else {
                      $thisList.removeClass('active');
                  }
             })
             .fail(function() {
                 $thisList.prop('checked', !shouldSubscribe);
                 $messages.html(formatMessage('Could not change subscription status, please try again later...', 'danger'));
             });
        })
    }

});
