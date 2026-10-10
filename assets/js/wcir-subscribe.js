// Subscribe box on the WCIR report pages (/wcir/*), built by _scripts/import_wcir.py,
// and the email gate on /wineries. A form with data-next opens that page once the
// Zoho write has landed (the gate to the free summary); without it, the box confirms
// in place.
//
// THE SWITCH. While false, the page shows the mailto line and the form stays
// hidden, which is also what a visitor without JavaScript sees. Set it to true
// only after the infra/msiq-stripe-webhook session confirms the newsletter
// endpoint accepts list=wcir and reports failures honestly. Flipping it changes
// this one file; no report page needs rebuilding.
var WCIR_FORM_LIVE = true;

(function () {
  if (!WCIR_FORM_LIVE) return;
  var form = document.getElementById('wcirSubscribeForm');
  var fallback = document.getElementById('wcirSubscribeFallback');
  if (!form) return;
  form.hidden = false;
  if (fallback) fallback.hidden = true;

  var msg = document.getElementById('wcirSubscribeMsg');
  var email = document.getElementById('wcirEmail');
  var winery = document.getElementById('wcirWinery');
  var name = document.getElementById('wcirName'); // optional: only the report page's box has it
  var btn = form.querySelector('button[type="submit"]');
  var label = btn.textContent;
  var FAIL = 'That didn\u2019t go through. Email wci@mainstreetiq.com and we\u2019ll add you.';
  var endpoint = 'https://msiq-stripe-webhook.vercel.app/api/newsletter_signup';
  // Contract (msiq-stripe-webhook, 2026-10-08): {email, list, source, winery?, first_name?, honeypot}.
  // 200 {ok:true} is success; 502 {ok:false, code} is failure. Only r.ok shows success.
  var path = ((window.location && window.location.pathname) || '/wcir/').replace(/\.html$/, '');

  function setMsg(text, kind) {
    msg.textContent = text;
    msg.className = 'wcir-subscribe-msg' + (kind ? ' ' + kind : '');
  }

  form.addEventListener('submit', function (e) {
    e.preventDefault();
    setMsg('');
    var value = (email.value || '').trim();
    var firstName = name ? (name.value || '').trim() : '';
    if (name && !firstName) {
      setMsg('Please enter your name.', 'err');
      return;
    }
    if (!value || value.indexOf('@') < 1) {
      setMsg('Please enter a valid email.', 'err');
      return;
    }
    btn.disabled = true;
    btn.textContent = 'Sending…';
    var honeypot = form.elements && form.elements['honeypot'];
    fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email: value,
        winery: (winery.value || '').trim(),
        first_name: firstName,
        list: form.getAttribute('data-list') || 'wcir',
        source: path,
        honeypot: honeypot ? honeypot.value : ''
      })
    }).then(function (r) {
      if (r.ok) {
        var next = form.getAttribute('data-next');
        if (next) {
          setMsg('Thanks. Opening the summary\u2026', 'ok');
          window.location.assign(next);
          return;
        }
        setMsg('Thanks. The next edition will come to ' + value + '.', 'ok');
        email.value = '';
        winery.value = '';
        if (name) name.value = '';
      } else {
        setMsg(FAIL, 'err');
      }
    }).catch(function () {
      setMsg(FAIL, 'err');
    }).then(function () {
      btn.disabled = false;
      btn.textContent = label;
    });
  });
})();
