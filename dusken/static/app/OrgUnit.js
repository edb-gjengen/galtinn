import $ from "jquery";

$(document).ready(function() {
    /* Orgunit: Add member */
    $('.js-orgunit-add-member').on('click', (e) => {
        const $el = $(e.target);
        const orgunit = $el.data('orgunitSlug');
        const type = $el.data('orgunitAction');
        let user = $el.data('userId');

        console.log(orgunit, type, user);
        if (!user) {
            try {
                user = $('#id_user').select2('data')[0].id;
            } catch (err) {
                return
            }
        }

        $.ajax({
            url: '/api/orgunit/add/user/',
            data: {
                'user': user,
                'orgunit': orgunit,
                'type': type
            },
            dataType: 'json',
            success: function (response) {
                if (response.success) {
                    location.reload()
                } else {
                    alert(response.error);
                }
            },
            error: function () {
                alert('Failed to contact server');
            }
        });
    });

    /* Orgunit: Remove member */
    $('.js-orgunit-remove-user').on('click', (e) => {
        const $el = $(e.target);
        const orgunit = $el.data('orgunitSlug');
        const type = $el.data('orgunitAction');
        const user = $el.data('userId');
        const confirmText = $el.data('textRemoveUser');

        if (type === 'member' && !confirm(confirmText)) {
            return;
        }

        $.ajax({
            url: '/api/orgunit/remove/user/',
            data: {
                'user': user,
                'orgunit': orgunit,
                'type': type
            },
            dataType: 'json',
            success: function (response) {
                if (response.success) {
                    if (type === 'admin') {
                        location.reload();
                    } else {
                        $('#user_remove_' + user).parent().parent().parent().slideUp();
                    }
                } else {
                    alert(response.error);
                }
            },
            error: function () {
                alert('Failed to contact server');
            }
        });
    });
});
