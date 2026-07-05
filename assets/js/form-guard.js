/**
 * MSIQ Web-to-Lead anti-spam guard
 * --------------------------------
 * Self-installing. Attaches to every form that POSTs to Zoho Web-to-Lead and
 * blocks the two bot signatures the markup honeypot alone never enforced:
 *   1. Honeypot filled  - any .msiq-form__honeypot with a value.
 *   2. Too-fast submit  - submitted < MIN_FILL_MS after the page armed the form.
 *
 * Both fail silently (preventDefault + stopImmediatePropagation): the bot sees
 * nothing submit, a human never trips it. No server round-trip, so it stays safe
 * for the captcha-OFF direct-to-Zoho forms (turning Zoho captcha ON would
 * quarantine every legit post as webform_invalid; see ops memory 2026-06-05).
 *
 * Auto-detects forms by action + honeypot class, so it covers both the
 * MSIQForm-driven pages and the plain native-submit pages.
 *
 * Added 2026-06-15 after form-spam bots passed the unenforced honeypot
 * (two dotted-Gmail bursts, 7 junk Leads across Partner / Intro Call / WCIR forms).
 */
(function () {
  'use strict';

  var MIN_FILL_MS = 3000; // humans take far longer; bots submit near-instantly

  function arm(form) {
    var armedAt = Date.now();
    form.addEventListener(
      'submit',
      function (e) {
        // 1. Honeypot: any decoy field carrying a value means a bot filled it.
        var pots = form.querySelectorAll('.msiq-form__honeypot');
        for (var i = 0; i < pots.length; i++) {
          if ((pots[i].value || '').trim() !== '') {
            e.preventDefault();
            e.stopImmediatePropagation();
            return;
          }
        }
        // 2. Time-trap: a real fill of a required-field form takes seconds.
        if (Date.now() - armedAt < MIN_FILL_MS) {
          e.preventDefault();
          e.stopImmediatePropagation();
          return;
        }
      },
      true // capture phase: run before per-page submit listeners
    );
  }

  function init() {
    var forms = document.querySelectorAll('form[action*="WebToLeadForm"]');
    Array.prototype.forEach.call(forms, arm);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
