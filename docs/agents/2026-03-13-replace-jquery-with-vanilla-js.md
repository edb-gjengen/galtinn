# Replace jQuery with Vanilla JavaScript

## Goal

Reduce bundle size by removing jQuery and select2 from the frontend bundle, replacing all usage with vanilla JavaScript and django-tomselect.

## Bundle Size Results

| File    | Before  | After  | Reduction       |
| ------- | ------- | ------ | --------------- |
| app.js  | 194 KB  | 43 KB  | -151 KB (78%)   |
| app.css | 293 KB  | 253 KB | -40 KB (14%)    |
| stats.js| 536 KB  | 536 KB | ~0 (not bundled) |

## Changes

### Phase 1: Convert stats.js to vanilla JS

Replaced all jQuery in `frontend/app/stats.js`:

- `$.getJSON()` → `fetch().then(r => r.json())`
- `$('.class').html(val)` → `document.querySelector().innerHTML`
- `$('.class').text(val)` → `document.querySelector().textContent`
- `$('#id').val()` → `document.getElementById().value`
- `$(e.target).val()` → `e.target.value`
- `$('.class').on('event', cb)` → `addEventListener()`
- `$.extend(true, ...)` → plain object assignment (lodash `_.merge` not needed for this case)
- `$(() => {...})` → `document.addEventListener('DOMContentLoaded', ...)`

### Phase 2: Convert index.js and OrgUnit.js to vanilla JS

**index.js:**

- Removed `import $ from 'jquery'` and `window.$ = window.jQuery = $`
- Removed `import 'select2'`
- Replaced `jQuery.trim()` → `.trim()` (removed entirely with CSRF approach change)
- Replaced `$.ajaxSetup()` CSRF cookie logic → `fetchWithCSRF()` helper reading from `<meta name="x-csrf-token">` in base.html
- Replaced `$.post()` → `fetchWithCSRF(url, { method: 'POST' })`
- Replaced `$.ajax()` → `fetch()` with `URLSearchParams`
- Replaced `$('#id_user').select2('data')[0].id` → `document.getElementById('id_user').value`
- All selectors/events/class manipulation → vanilla DOM APIs

**OrgUnit.js:**

- Removed `import $ from 'jquery'`
- Replaced `$(e.target)` / `$el.data('...')` → `e.target` / `el.dataset.*`
- Replaced `$.ajax()` → `fetch()` with CSRF header
- Replaced `$('#user_remove_...').parent().parent().parent().slideUp()` → `.closest('li')` + CSS transition class `.removing`
- `$(() => {...})` → `document.addEventListener('DOMContentLoaded', ...)`

### Phase 3: Replace django-select2 with django-tomselect

**Backend:**

- Replaced `django-select2` with `django-tomselect` in `pyproject.toml`
- Updated `dusken/settings/base.py`: swapped `INSTALLED_APPS`, added `TomSelectMiddleware`, added `tomselect` context processor
- Created `dusken/autocompletes.py` with `UserAutocompleteView` (same search_lookups as old `UserSearchWidget`)
- Updated `dusken/urls.py`: removed `select2/` path, added `autocomplete/user/` path
- Updated `dusken/forms.py`: replaced `ModelSelect2Widget` + `UserSearchWidget` with `TomSelectModelChoiceField` + `TomSelectConfig`

**Frontend:**

- Removed `jquery`, `select2`, `select2-bootstrap-5-theme` from `package.json`
- Deleted `frontend/app/styles/_select2.scss` and its import in `app.scss`
- Templates `user_list.html` and `orgunit_edit_users.html`: `{{ user_search.media.js }}` → `{{ user_search.media }}`

### Phase 4: Slide-up CSS transition

Added `.removing` CSS class to `_general.scss` for smooth slide-up animation on `.list-group-item` elements (replaces jQuery `.slideUp()`).

## Files Modified

- `frontend/app/stats.js` — all jQuery → vanilla JS
- `frontend/app/index.js` — removed jQuery/select2 imports, vanilla JS + fetch
- `frontend/app/OrgUnit.js` — vanilla JS + fetch, CSS transition for slide-up
- `frontend/app/styles/_general.scss` — added `.removing` transition
- `frontend/app/styles/app.scss` — removed `_select2` import
- `frontend/app/styles/_select2.scss` — deleted
- `frontend/package.json` — removed jquery, select2, select2-bootstrap-5-theme
- `dusken/autocompletes.py` — new file, `UserAutocompleteView`
- `dusken/forms.py` — `TomSelectModelChoiceField` + `TomSelectConfig`
- `dusken/urls.py` — swapped select2 URL for autocomplete URL
- `dusken/settings/base.py` — INSTALLED_APPS, MIDDLEWARE, context_processors
- `dusken/templates/dusken/user_list.html` — updated media tag
- `dusken/templates/dusken/orgunit_edit_users.html` — updated media tag
- `pyproject.toml` — swapped django-select2 → django-tomselect

## Verification

- Frontend build: `npx rspack build` — succeeds, no jQuery in output
- Django system checks: `uv run python manage.py check` — no issues
- Test suite: `uv run pytest` — 41 tests pass
