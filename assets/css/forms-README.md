# MSIQ Form Component Library

Modern, design-system-matched forms for Main Street IQ. Three patterns supported. All submit to Zoho Web-to-Lead (or any backend) with zero new SaaS dependency.

## Files

| File | Purpose |
|---|---|
| `assets/css/forms.css` | All form styles. Load AFTER `styles.css`. |
| `assets/js/forms.js` | Multi-step controller + validation + analytics. Vanilla JS, no dependencies. |
| `_examples/form-pattern-demo.html` | Working examples of all three patterns. Reference when building a new form. |

## Three patterns

### 1. Single-step form
Simple lead capture. Contact, WCIR signup, Intro Call free booking, etc. Native form submit (POSTs straight to Zoho Web-to-Lead). Use `MSIQForm` for validation styling without overriding the submit.

### 2. Multi-step form
Assessment quizzes, Strategic Brief intake, multi-stage onboarding. Progressive disclosure, per-step validation, choice-card UX. Use `MSIQForm` with `conditionalLogic` if some steps depend on prior answers.

### 3. Inline form
Horizontal single-input layout. Footer newsletter, hero email capture.

## Building a new form: the 5-minute recipe

1. **Copy the relevant section** from `_examples/form-pattern-demo.html`.
2. **Replace Zoho hidden fields** with your form's actual `xnQsjsdp` token, `actionType`, `returnURL`, and `Lead Source` value.
3. **Update field names** to match your Zoho CRM picklist values (Lead Source, Lead Status, etc. are strict — verify in Zoho before deploying).
4. **Initialize MSIQForm** at the bottom of the page:
   ```html
   <script src="/assets/js/forms.js"></script>
   <script>
     new MSIQForm({
       formElement: document.getElementById('myFormId'),
       analytics: { category: 'my_form_category' },
     }).init();
   </script>
   ```
5. **Test the redirect.** Submit a test entry; verify Zoho creates the Lead with the right Lead Source; verify `returnURL` lands you on the thank-you page.

## Design tokens used

All from `styles.css` (the canonical source):

| Token | Where it's used |
|---|---|
| `--color-midnight` | Field labels, step titles, button text on light bg |
| `--color-navy` | Focus state, primary button background, progress fill |
| `--color-sky` | Accent (used sparingly in card-choice hover) |
| `--color-neutral` | Body text, help text, placeholder |
| `--color-border` | Input borders, divider lines |
| `--color-ice` | Hover state for choice cards |
| `--color-error` | Validation error text + invalid input border |
| `--color-success` | Success state checkmark |
| `--font-body` | All form text (Outfit) |

No off-token colors. No new font weights beyond what `styles.css` already loads (200-700 from Outfit).

## Conditional branching (multi-step only)

If a step should only show for certain prior answers, pass `conditionalLogic` to MSIQForm:

```js
new MSIQForm({
  formElement: document.getElementById('myForm'),
  conditionalLogic: {
    'step-3': function (data) { return data.vertical === 'winery'; },
    'step-4': function (data) { return data.vertical === 'wellness'; },
  },
}).init();
```

A step that returns `false` is skipped on next/back navigation.

## Custom validators

If a step needs validation beyond required + email, pass `customValidators`:

```js
new MSIQForm({
  formElement: document.getElementById('myForm'),
  customValidators: {
    2: function (data, stepEl) {
      // Return true to pass; mark fields invalid + return false to block
      if (!data.url || !data.url.startsWith('https://')) {
        stepEl.querySelector('[name="url"]').closest('.msiq-form__field')
          .classList.add('msiq-form__field--invalid');
        return false;
      }
      return true;
    },
  },
}).init();
```

## Analytics events

If `gtag` is available, MSIQForm fires these events automatically:

| Event | When |
|---|---|
| `{category}_start` | First user interaction with the form |
| `{category}_step_advance` | Each successful step advance (multi-step only) |
| `{category}_complete` | Form submitted successfully |

Set `analytics.category` to namespace these per form.

## Honeypot anti-spam

Every form should include a hidden honeypot field. The library checks it before submit; if filled (by a bot), the submit silently fails:

```html
<input type="text" name="aG9uZXlwb3Q" class="msiq-form__honeypot" tabindex="-1" autocomplete="off" aria-hidden="true">
```

## Async submit (for non-Zoho backends)

If you need to POST to a custom backend (e.g., Vercel serverless function), pass `onSubmit`:

```js
new MSIQForm({
  formElement: document.getElementById('myForm'),
  onSubmit: async function (data) {
    var r = await fetch('/api/leads', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!r.ok) throw new Error('Submit failed');
    return { message: 'Custom success copy here.' };  // optional
  },
}).init();
```

The library handles the loading state on the submit button, swaps in the success state on completion, and shows an error alert on failure.

## What this replaces

The previous pattern was Zoho's embedded widgets + custom inline styling per form (the "looks like an add-on" complaint). With this library, every form on the site uses the same design tokens, the same validation pattern, the same UX conventions. New forms are configuration in HTML, not net-new CSS work.

## Future extensions

- File upload field (for FBD intake when client provides documents)
- Date picker
- Multi-select dropdown
- Auto-save to localStorage (resume long forms)
- Submission to Zoho Bookings (for Intro Call paid landing with calendar selection embedded)

Each is a focused addition to the library, not a rewrite.

Last reviewed: 2026-05-21
