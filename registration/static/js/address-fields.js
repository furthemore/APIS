/**
 * address-fields.js
 * Replacement for bootstrap-formhelpers country/state cascade.
 *
 * Usage in templates:
 *   Country select: class="addr-countries" data-default="US"
 *   State select:   class="addr-states"    data-default="VA" data-country-id="country"
 *
 * The state field becomes a <select> for countries that have subdivision data,
 * or a plain text <input> for those that don't.
 */
(function () {
  'use strict';

  const STATIC_BASE = (function () {
    const scripts = document.querySelectorAll('script[src]');
    for (const s of scripts) {
      const m = s.src.match(/^(.*\/static\/)/);
      if (m) return m[1];
    }
    // fallback: look for a meta tag set by the template
    const meta = document.querySelector('meta[name="static-url"]');
    return meta ? meta.content : '/static/';
  })();

  let countriesData = null;
  let statesData = null;

  function loadJSON(url) {
    return fetch(url).then(function (r) { return r.json(); });
  }

  function populateCountries(select, defaultCode) {
    // Clear and add placeholder
    select.innerHTML = '';
    const placeholder = document.createElement('option');
    placeholder.value = '';
    placeholder.textContent = 'Select Country...';
    select.appendChild(placeholder);

    const sorted = Object.entries(countriesData).sort(function (a, b) {
      return a[1].localeCompare(b[1]);
    });
    for (const [code, name] of sorted) {
      const opt = document.createElement('option');
      opt.value = code;
      opt.textContent = name;
      if (code === defaultCode) opt.selected = true;
      select.appendChild(opt);
    }
  }

  function populateStates(stateEl, countryCode, defaultState) {
    const subdivisions = statesData[countryCode];
    const parent = stateEl.parentNode;

    if (!subdivisions || subdivisions.length === 0) {
      // Replace select with text input if not already done
      if (stateEl.tagName === 'SELECT') {
        const input = document.createElement('input');
        input.type = 'text';
        input.id = stateEl.id;
        input.name = stateEl.name;
        input.className = stateEl.className;
        input.placeholder = 'State / Province / Region';
        if (stateEl.required) input.required = true;
        const autoComplete = stateEl.getAttribute('autocomplete');
        if (autoComplete) input.setAttribute('autocomplete', autoComplete);
        parent.replaceChild(input, stateEl);
      } else {
        stateEl.value = defaultState || '';
      }
      return;
    }

    // Ensure element is a select (convert back from input if previously switched)
    let select = stateEl;
    if (stateEl.tagName === 'INPUT') {
      select = document.createElement('select');
      select.id = stateEl.id;
      select.name = stateEl.name;
      select.className = stateEl.className;
      if (stateEl.required) select.required = true;
      const autoComplete = stateEl.getAttribute('autocomplete');
      if (autoComplete) select.setAttribute('autocomplete', autoComplete);
      // Copy data attributes for future cascade calls
      for (const attr of stateEl.attributes) {
        if (attr.name.startsWith('data-')) select.setAttribute(attr.name, attr.value);
      }
      parent.replaceChild(select, stateEl);
    }

    select.innerHTML = '';
    for (const sub of subdivisions) {
      const opt = document.createElement('option');
      opt.value = sub.c;
      opt.textContent = sub.n;
      if (sub.c === defaultState) opt.selected = true;
      select.appendChild(opt);
    }
  }

  function initAddressFields() {
    const countrySelects = document.querySelectorAll('.addr-countries');
    const stateEls = document.querySelectorAll('.addr-states');
    if (countrySelects.length === 0 && stateEls.length === 0) return;

    Promise.all([
      loadJSON(STATIC_BASE + 'js/countries.json'),
      loadJSON(STATIC_BASE + 'js/states.json'),
    ]).then(function (results) {
      countriesData = results[0];
      statesData = results[1];

      countrySelects.forEach(function (select) {
        const defaultCode = select.dataset.default || '';
        populateCountries(select, defaultCode);

        // Wire up any linked state fields
        stateEls.forEach(function (stateEl) {
          if (stateEl.dataset.countryId === select.id) {
            const defaultState = stateEl.dataset.default || '';
            populateStates(stateEl, defaultCode, defaultState);

            select.addEventListener('change', function () {
              // stateEl may have been replaced; re-query by id
              const current = document.getElementById(stateEl.id) || stateEl;
              populateStates(current, select.value, '');
            });
          }
        });
      });
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initAddressFields);
  } else {
    initAddressFields();
  }
})();
