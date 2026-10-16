import 'bootstrap/js/dist/collapse';
import 'bootstrap/js/dist/dropdown';

import './OrgUnit';
import { apiFetch } from './api';

import './styles/app.scss';

document.addEventListener('DOMContentLoaded', () => {
    /* Send validation email */
    const validationEmailBtn = document.querySelector('.js-send-validation-email');
    if (validationEmailBtn) {
        validationEmailBtn.addEventListener('click', (e) => {
            e.preventDefault();
            apiFetch(config.validateEmail, { method: 'POST' })
                .then(() => {
                    validationEmailBtn.textContent = 'Sent.';
                })
                .catch((error) => {
                    alert(error.message);
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

            apiFetch('/api/user/pk/to/uuid/?' + new URLSearchParams({ user }))
                .then((data) => {
                    window.location.href = '/users/' + data.uuid;
                })
                .catch(() => {
                    alert('Failed view user');
                });
        });
    }
});
