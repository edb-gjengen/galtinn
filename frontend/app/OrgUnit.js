import { ApiError, apiFetch } from './api';

function initOrgUnitMembers(root) {
    const config = JSON.parse(document.getElementById('orgunit-members-config').textContent);
    const { membersUrl, orgunitUrl, userUrl, currentUserId, isSuperuser, language, strings } = config;
    const rowTemplate = document.getElementById('orgunit-member-template');
    const list = root.querySelector('.js-member-list');
    const errorBox = root.querySelector('.js-error');
    const userSelect = document.getElementById('id_user');
    const dateFormat = new Intl.DateTimeFormat(language, { dateStyle: 'long' });
    const collator = new Intl.Collator(language);

    let members = [];

    const memberUrl = (member) => `${membersUrl}${member.id}/`;

    function sortMembers() {
        members.sort((a, b) => {
            if (a.role !== b.role) return a.role === 'admin' ? -1 : 1;
            return collator.compare(a.full_name, b.full_name);
        });
    }

    function showError(error) {
        errorBox.textContent = error instanceof ApiError ? error.message : strings.networkError;
        errorBox.hidden = false;
    }

    function clearError() {
        errorBox.hidden = true;
        errorBox.textContent = '';
    }

    function formatDate(isoDate) {
        const [year, month, day] = isoDate.split('-').map(Number);
        return dateFormat.format(new Date(year, month - 1, day));
    }

    function renderMembership(badge, membership) {
        if (!membership) {
            badge.classList.add('bg-danger');
            badge.textContent = strings.none;
        } else if (membership.is_valid) {
            badge.classList.add('bg-success');
            badge.textContent = membership.is_lifelong ? strings.lifelong : formatDate(membership.end_date);
        } else {
            badge.classList.add('bg-danger');
            badge.textContent = formatDate(membership.end_date);
        }
    }

    function renderMember(member) {
        const row = rowTemplate.content.firstElementChild.cloneNode(true);
        const isAdmin = member.role === 'admin';

        row.dataset.memberId = member.id;
        row.querySelector('.js-icon-admin').hidden = !isAdmin;
        row.querySelector('.js-icon-member').hidden = isAdmin;
        row.querySelector('.js-you').hidden = member.id !== currentUserId;

        const name = row.querySelector('.js-name');
        name.textContent = member.full_name;
        name.href = userUrl.replace('__uuid__', member.uuid);

        const email = row.querySelector('.js-email');
        email.textContent = member.email;
        email.href = `mailto:${member.email}`;

        renderMembership(row.querySelector('.js-membership'), member.membership);

        const roleSelect = row.querySelector('.js-role');
        if (roleSelect) {
            roleSelect.value = member.role;
            roleSelect.addEventListener('change', () => setRole(member, roleSelect));
        }
        row.querySelector('.js-remove').addEventListener('click', (e) => removeMember(member, row, e.target));

        return row;
    }

    function render() {
        if (members.length === 0) {
            list.replaceChildren(strings.noMembers);
            return;
        }
        list.replaceChildren(...members.map(renderMember));
    }

    function replaceMember(updated) {
        members = members.filter((member) => member.id !== updated.id).concat(updated);
        sortMembers();
        render();
    }

    /* Run an API call with the control disabled, showing any error */
    async function withControl(control, action) {
        clearError();
        control.disabled = true;
        try {
            await action();
        } catch (error) {
            showError(error);
        } finally {
            control.disabled = false;
        }
    }

    function addMember(role, button) {
        const user = userSelect ? userSelect.value : null;
        if (!user) return;

        withControl(button, async () => {
            const member = await apiFetch(membersUrl, { method: 'POST', body: { user: Number(user), role } });
            userSelect.tomselect?.clear();
            replaceMember(member);
        });
    }

    /* Admins who demote or remove themselves lose access to this page */
    const losesAccess = (member) => member.id === currentUserId && !isSuperuser;

    function setRole(member, select) {
        const role = select.value;
        if (role === 'member') {
            const message = losesAccess(member)
                ? strings.confirmDemoteSelf
                : strings.confirmDemote.replace('{name}', member.full_name);
            if (!confirm(message)) {
                select.value = member.role;
                return;
            }
        }

        withControl(select, async () => {
            try {
                const updated = await apiFetch(memberUrl(member), { method: 'PATCH', body: { role } });
                if (losesAccess(member) && role === 'member') {
                    window.location.href = orgunitUrl;
                    return;
                }
                replaceMember(updated);
            } catch (error) {
                select.value = member.role;
                throw error;
            }
        });
    }

    function removeMember(member, row, button) {
        const message = losesAccess(member)
            ? strings.confirmRemoveSelf
            : strings.confirmRemove.replace('{name}', member.full_name);
        if (!confirm(message)) return;

        withControl(button, async () => {
            await apiFetch(memberUrl(member), { method: 'DELETE' });
            if (losesAccess(member)) {
                window.location.href = orgunitUrl;
                return;
            }
            row.addEventListener(
                'transitionend',
                () => {
                    members = members.filter((m) => m.id !== member.id);
                    render();
                },
                { once: true },
            );
            row.classList.add('removing');
        });
    }

    root.querySelectorAll('.js-add-member').forEach((button) => {
        button.addEventListener('click', () => addMember(button.dataset.role, button));
    });

    apiFetch(membersUrl)
        .then((data) => {
            members = data;
            render();
        })
        .catch(showError);
}

document.addEventListener('DOMContentLoaded', () => {
    const root = document.querySelector('.js-orgunit-members');
    if (root) initOrgUnitMembers(root);
});
