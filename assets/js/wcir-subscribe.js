// Subscribe box on the WCIR report pages (/wcir/*), built by _scripts/import_wcir.py.
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
        list: form.getAttribute('data-list') || 'wcir',
        source: path,
        honeypot: honeypot ? honeypot.value : ''
      })
    }).then(function (r) {
      if (r.ok) {
        setMsg('Thanks. The next edition will come to ' + value + '.', 'ok');
        email.value = '';
        winery.value = '';
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
