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
    const $messages = $('.messages');

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
