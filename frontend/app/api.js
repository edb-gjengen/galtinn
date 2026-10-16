export function getCSRFToken() {
    const meta = document.querySelector('meta[name="x-csrf-token"]');
    return meta ? meta.getAttribute('content') : '';
}

export class ApiError extends Error {
    constructor(message, status, data) {
        super(message);
        this.status = status;
        this.data = data;
    }
}

/* Find the first human readable message in a DRF error response */
function firstErrorMessage(data) {
    if (typeof data === 'string') return data;
    if (Array.isArray(data)) return firstErrorMessage(data[0]);
    if (data && typeof data === 'object') {
        return firstErrorMessage(data.detail ?? Object.values(data)[0]);
    }
    return null;
}

export async function apiFetch(url, { method = 'GET', body } = {}) {
    const headers = { Accept: 'application/json', 'X-CSRFToken': getCSRFToken() };
    if (body !== undefined) {
        headers['Content-Type'] = 'application/json';
    }

    const response = await fetch(url, {
        method,
        headers,
        credentials: 'same-origin',
        body: body === undefined ? undefined : JSON.stringify(body),
    });
    const data = response.status === 204 ? null : await response.json().catch(() => null);

    if (!response.ok) {
        throw new ApiError(firstErrorMessage(data) || response.statusText, response.status, data);
    }
    return data;
}
