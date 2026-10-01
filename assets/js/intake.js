/**
 * Post-purchase intake form controller.
 * --------------------------------------
 * Drives a thank-you page form (e.g. thank-you-monitor.html) that posts to the
 * msiq-stripe-webhook intake endpoint. The endpoint, not this script, is the
 * gate: it verifies the Stripe Checkout Session is paid before writing
 * anything. This script only collects, validates and reports.
 *
 * Contract (form element attributes):
 *   data-endpoint  intake URL
 *   data-form      form discriminator sent to the endpoint ("monitor")
 *
 * The contract of record is the "Intake endpoint" section of the
 * msiq-stripe-webhook README. In short:
 *
 * GET  <endpoint>?session_id=cs_...
 *      200 {"ok": true, "business_name", "contact_name", "contact_email"}
 *      fills any empty matching control (see PREFILL). 400 invalid_session
 *      swaps the form for the no-order notice; any other failure is silent
 *      and the customer types the answers.
 * POST <endpoint>  flat JSON: form, session_id, company_website (honeypot),
 *      and the client-onboarding-intake keys business_name, domain, industry,
 *      owner_name, owner_email, biggest_goal, brand_posture, competitor_1..4
 *      ("Name, domain").
 *      200 {"ok": true} -> success. 400 invalid_session -> no-order notice.
 *      400 missing_fields / invalid_fields + "fields" -> mark those fields.
 *      Anything else (402 unpaid, 502, network) -> the error state.
 */
(function () {
  var form = document.getElementById('intakeForm');
  if (!form) return;

  var endpoint = form.getAttribute('data-endpoint');
  var formType = form.getAttribute('data-form');
  var success = document.getElementById('intakeSuccess');
  var errorBox = document.getElementById('intakeError');
  var errorMail = document.getElementById('intakeErrorMail');
  var noSession = document.getElementById('intakeNoSession');
  var submitBtn = form.querySelector('[data-action="submit"]');
  var sessionId = new URLSearchParams(window.location.search).get('session_id') || '';

  var EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  var URL_RE = /^(https?:\/\/)?[^\s\/.]+(\.[^\s\/.]+)+(\/\S*)?$/i;
  // GET response key -> form control name.
  var PREFILL = { business_name: 'business_name', contact_name: 'owner_name', contact_email: 'owner_email' };

  // ---- No order reference: nothing this page can submit will be accepted.
  if (!/^cs_/.test(sessionId)) {
    noSession.hidden = false;
    form.hidden = true;
    return;
  }

  // ---- Prefill from the verified session (best effort).
  // A 400 invalid_session means the POST will be refused too, so say so now
  // rather than after the customer fills in every field. Any other failure
  // (402 unpaid, network) leaves the form up; the POST reports the outcome.
  fetch(endpoint + '?session_id=' + encodeURIComponent(sessionId), { method: 'GET' })
    .then(function (r) {
      if (r.ok) return r.json();
      if (r.status === 400) {
        return r.json().then(function (body) {
          if (body && body.error === 'invalid_session') {
            noSession.hidden = false;
            form.hidden = true;
          }
          return null;
        });
      }
      return null;
    })
    .then(function (data) {
      if (!data || !data.ok) return;
      Object.keys(PREFILL).forEach(function (key) {
        var value = data[key];
        var el = form.elements[PREFILL[key]];
        if (!value || !el) return;
        if (el instanceof RadioNodeList) {
          if (!el.value) el.value = value;
        } else if (!el.value) {
          el.value = value;
        }
      });
      updateCount();
    })
    .catch(function () {});

  // ---- Goal character counter.
  var goal = form.elements['biggest_goal'];
  var goalCount = document.getElementById('biggest_goal_count');
  function updateCount() {
    goalCount.textContent = 'Aim for 100 to 300 characters. ' + goal.value.length + ' / 300';
  }
  goal.addEventListener('input', updateCount);

  // ---- Validation.
  function fieldOf(el) {
    return el.closest('.msiq-form__field');
  }

  function isValid(el) {
    if (el.type === 'radio') return !!form.elements[el.name].value;
    var v = el.value.trim();
    if (!v) return false;
    var kind = el.getAttribute('data-kind');
    if (kind === 'email') return EMAIL_RE.test(v);
    if (kind === 'url') return URL_RE.test(v);
    return true;
  }

  function requiredControls() {
    var seen = {};
    return Array.prototype.filter.call(form.querySelectorAll('[required]'), function (el) {
      if (el.type !== 'radio') return true;
      if (seen[el.name]) return false;
      seen[el.name] = true;
      return true;
    });
  }

  function validate() {
    var firstBad = null;
    requiredControls().forEach(function (el) {
      var ok = isValid(el);
      fieldOf(el).classList.toggle('msiq-form__field--invalid', !ok);
      el.setAttribute('aria-invalid', ok ? 'false' : 'true');
      if (!ok && !firstBad) firstBad = el;
    });
    return firstBad;
  }

  form.addEventListener('input', function (e) {
    var field = fieldOf(e.target);
    if (field && field.classList.contains('msiq-form__field--invalid') && isValid(e.target)) {
      field.classList.remove('msiq-form__field--invalid');
      e.target.setAttribute('aria-invalid', 'false');
    }
  });
  form.addEventListener('change', function (e) {
    if (e.target.type === 'radio') {
      fieldOf(e.target).classList.remove('msiq-form__field--invalid');
    }
  });

  // ---- Payload.
  function bareDomain(raw) {
    return raw.trim().replace(/^https?:\/\//i, '').replace(/^www\./i, '').split('/')[0].toLowerCase();
  }

  function collect() {
    var val = function (name) { return (form.elements[name].value || '').trim(); };
    var site = val('domain');
    var fields = {
      business_name: val('business_name'),
      domain: /^https?:\/\//i.test(site) ? site : 'https://' + site,
      industry: val('industry'),
      owner_name: val('owner_name'),
      owner_email: val('owner_email'),
      biggest_goal: val('biggest_goal'),
      brand_posture: val('brand_posture')
    };
    for (var i = 1; i <= 4; i++) {
      // Downstream splits "Name, domain" on the FIRST comma, so a comma in the
      // name would move part of it into the domain.
      var name = document.getElementById('competitor_' + i + '_name').value.replace(/,/g, ' ').replace(/\s+/g, ' ').trim();
      var dom = bareDomain(document.getElementById('competitor_' + i + '_site').value);
      fields['competitor_' + i] = name + ', ' + dom;
    }
    return fields;
  }

  function mailtoWithAnswers(fields) {
    var body = 'Order reference: ' + sessionId + '\n\n' + Object.keys(fields).map(function (k) {
      return k + ': ' + fields[k];
    }).join('\n');
    return 'mailto:scott@mainstreetiq.com?subject=' + encodeURIComponent('Monitor intake | ' + fields.business_name) +
      '&body=' + encodeURIComponent(body);
  }

  // ---- Server-side field rejections: the endpoint names competitor_N; the
  // page splits each competitor into a name and a site input.
  function markFields(names) {
    var first = null;
    names.forEach(function (name) {
      var els = /^competitor_\d$/.test(name)
        ? [document.getElementById(name + '_name'), document.getElementById(name + '_site')]
        : [form.elements[name] instanceof RadioNodeList ? form.elements[name][0] : form.elements[name]];
      els.forEach(function (el) {
        if (!el) return;
        fieldOf(el).classList.add('msiq-form__field--invalid');
        el.setAttribute('aria-invalid', 'true');
        if (!first) first = el;
      });
    });
    if (first) first.focus();
  }

  // ---- Submit.
  var busy = false;
  form.addEventListener('submit', function (e) {
    e.preventDefault();
    if (busy) return;
    errorBox.hidden = true;

    var firstBad = validate();
    if (firstBad) {
      firstBad.focus();
      return;
    }

    var fields = collect();
    errorMail.href = mailtoWithAnswers(fields);
    busy = true;
    submitBtn.disabled = true;
    submitBtn.classList.add('msiq-form__btn--loading');

    var controller = window.AbortController ? new AbortController() : null;
    var timer = controller ? setTimeout(function () { controller.abort(); }, 20000) : null;

    fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(Object.assign({
        form: formType,
        session_id: sessionId,
        company_website: form.elements['company_website'].value
      }, fields)),
      signal: controller ? controller.signal : undefined
    }).then(function (r) {
      return r.json().catch(function () { return {}; }).then(function (data) {
        if (r.status === 400 && data.error === 'invalid_session') {
          noSession.hidden = false;
          form.hidden = true;
          noSession.scrollIntoView({ behavior: 'smooth', block: 'center' });
          return;
        }
        if (r.status === 400 && Array.isArray(data.fields) && data.fields.length) {
          markFields(data.fields);
          return;
        }
        if (!r.ok || data.ok === false) throw new Error('intake rejected');
        form.hidden = true;
        success.classList.add('msiq-form__success--active');
        success.focus();
        success.scrollIntoView({ behavior: 'smooth', block: 'center' });
        if (typeof gtag !== 'undefined') {
          gtag('event', 'intake_submitted', { form: formType });
        }
      });
    }).catch(function () {
      errorBox.hidden = false;
      errorBox.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }).then(function () {
      if (timer) clearTimeout(timer);
      busy = false;
      submitBtn.disabled = false;
      submitBtn.classList.remove('msiq-form__btn--loading');
    });
  });
})();
