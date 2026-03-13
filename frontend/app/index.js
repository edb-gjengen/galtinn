import 'bootstrap/js/dist/collapse';
import 'bootstrap/js/dist/dropdown';

import './OrgUnit';

import './styles/app.scss';

function getCSRFToken() {
    const meta = document.querySelector('meta[name="x-csrf-token"]');
    return meta ? meta.getAttribute('content') : '';
}

function fetchWithCSRF(url, options = {}) {
    const defaults = {
        headers: {
            'X-CSRFToken': getCSRFToken(),
        },
    };
    return fetch(url, { ...defaults, ...options });
}

document.addEventListener('DOMContentLoaded', () => {
    /* Send validation email */
    const validationEmailBtn = document.querySelector('.js-send-validation-email');
    if (validationEmailBtn) {
        validationEmailBtn.addEventListener('click', (e) => {
            e.preventDefault();
            fetchWithCSRF(config.validateEmail, { method: 'POST' }).then(() => {
                validationEmailBtn.textContent = 'Sent.';
            });
        });
    }

    /* Hidden language select */
    const languageToggle = document.querySelector('.js-language-select-toggle');
    const languageSelect = document.querySelector('.language-select');
    if (languageToggle && languageSelect) {
        languageToggle.addEventListener('click', (e) => {
            e.preventDefault();
            languageSelect.classList.toggle('hidden');
            if (!languageSelect.classList.contains('hidden')) {
                languageSelect.focus();
            }
        });
    }

    /* View user (from tom-select dropdown) */
    const viewUserBtn = document.querySelector('.js-view-user');
    if (viewUserBtn) {
        viewUserBtn.addEventListener('click', () => {
            const userSelect = document.getElementById('id_user');
            const user = userSelect ? userSelect.value : null;
            if (!user) return;

            fetch('/api/user/pk/to/uuid/?' + new URLSearchParams({ user }))
                .then((response) => response.json())
                .then((data) => {
                    window.location.href = '/users/' + data.uuid;
                })
                .catch(() => {
                    alert('Failed view user');
                });
        });
    }
});
