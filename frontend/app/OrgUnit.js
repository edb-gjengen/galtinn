function getCSRFToken() {
    const meta = document.querySelector('meta[name="x-csrf-token"]');
    return meta ? meta.getAttribute('content') : '';
}

document.addEventListener('DOMContentLoaded', () => {
    /* Orgunit: Add member */
    document.querySelectorAll('.js-orgunit-add-member').forEach((btn) => {
        btn.addEventListener('click', (e) => {
            const el = e.target;
            const orgunit = el.dataset.orgunitSlug;
            const type = el.dataset.orgunitAction;
            let user = el.dataset.userId;

            if (!user) {
                const userSelect = document.getElementById('id_user');
                user = userSelect ? userSelect.value : null;
                if (!user) return;
            }

            fetch('/api/orgunit/add/user/?' + new URLSearchParams({ user, orgunit, type }), {
                headers: { 'X-CSRFToken': getCSRFToken() },
            })
                .then((response) => response.json())
                .then((data) => {
                    if (data.success) {
                        location.reload();
                    } else {
                        alert(data.error);
                    }
                })
                .catch(() => {
                    alert('Failed to contact server');
                });
        });
    });

    /* Orgunit: Remove member */
    document.querySelectorAll('.js-orgunit-remove-user').forEach((btn) => {
        btn.addEventListener('click', (e) => {
            const el = e.target;
            const orgunit = el.dataset.orgunitSlug;
            const type = el.dataset.orgunitAction;
            const user = el.dataset.userId;
            const confirmText = el.dataset.textRemoveUser;

            if (type === 'member' && !confirm(confirmText)) {
                return;
            }

            fetch('/api/orgunit/remove/user/?' + new URLSearchParams({ user, orgunit, type }), {
                headers: { 'X-CSRFToken': getCSRFToken() },
            })
                .then((response) => response.json())
                .then((data) => {
                    if (data.success) {
                        if (type === 'admin') {
                            location.reload();
                        } else {
                            const row = document.getElementById('user_remove_' + user);
                            if (row) {
                                const li = row.closest('li');
                                if (li) {
                                    li.classList.add('removing');
                                    li.addEventListener('transitionend', () => li.remove());
                                }
                            }
                        }
                    } else {
                        alert(data.error);
                    }
                })
                .catch(() => {
                    alert('Failed to contact server');
                });
        });
    });
});
