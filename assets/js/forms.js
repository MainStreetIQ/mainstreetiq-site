/**
 * MSIQ Form Component Library — JavaScript Controller
 * ----------------------------------------------------
 * Vanilla JS multi-step form controller. Pairs with assets/css/forms.css.
 *
 * Supports:
 *   - Single-step and multi-step forms
 *   - Per-step validation (required fields, email format, custom validators)
 *   - Conditional branching (skip steps based on prior answers)
 *   - Progress indicator updates
 *   - gtag analytics events on start, step-advance, complete, abandon
 *   - Submit to Zoho Web-to-Lead (or any POST endpoint) with hidden fields
 *   - Honeypot anti-spam
 *   - Success state rendering
 *
 * Usage:
 *
 *   const form = new MSIQForm({
 *     formElement: document.getElementById('myForm'),
 *     onSubmit: async (data) => { ... },   // optional; defaults to native form submit
 *     onStepChange: (newStep) => { ... },  // optional callback
 *     conditionalLogic: {                  // optional
 *       'step-2': (data) => data.vertical === 'wine',
 *     },
 *     analytics: {
 *       category: 'intro_call',              // gtag event category
 *     },
 *   });
 *   form.init();
 *
 * Form markup conventions (see _examples/form-pattern-demo.html for the canonical example):
 *
 *   <form class="msiq-form msiq-form--multi-step" id="myForm" action="..." method="POST">
 *     <div class="msiq-form__progress">
 *       <div class="msiq-form__progress-bar"><div class="msiq-form__progress-fill"></div></div>
 *       <span class="msiq-form__progress-label">Step 1 of 4</span>
 *     </div>
 *     <div class="msiq-form__step msiq-form__step--active" data-step="1">...</div>
 *     <div class="msiq-form__step" data-step="2">...</div>
 *     <div class="msiq-form__buttons">
 *       <button type="button" class="msiq-form__btn msiq-form__btn--secondary" data-action="back">Back</button>
 *       <button type="button" class="msiq-form__btn msiq-form__btn--primary" data-action="next">Continue</button>
 *       <button type="submit" class="msiq-form__btn msiq-form__btn--primary" data-action="submit" style="display:none;">Submit</button>
 *     </div>
 *     <div class="msiq-form__success">...</div>
 *   </form>
 *
 * Last reviewed: 2026-05-21
 */

(function (global) {
  'use strict';

  function MSIQForm(options) {
    this.formEl = options.formElement;
    if (!this.formEl) {
      throw new Error('MSIQForm: formElement is required');
    }
    this.onSubmit = options.onSubmit || null;
    this.onStepChange = options.onStepChange || null;
    this.conditionalLogic = options.conditionalLogic || {};
    this.analytics = options.analytics || {};
    this.customValidators = options.customValidators || {};

    this.currentStep = 1;
    this.totalSteps = 1;
    this.stepEls = [];
    this.progressFillEl = null;
    this.progressLabelEl = null;
    this.backBtn = null;
    this.nextBtn = null;
    this.submitBtn = null;
    this.successEl = null;
    this.hasStarted = false;
    this._initialized = false;
  }

  MSIQForm.prototype.init = function () {
    if (this._initialized) return;
    this._initialized = true;

    this.stepEls = Array.prototype.slice.call(
      this.formEl.querySelectorAll('.msiq-form__step')
    );
    this.totalSteps = this.stepEls.length || 1;
    this.progressFillEl = this.formEl.querySelector('.msiq-form__progress-fill');
    this.progressLabelEl = this.formEl.querySelector('.msiq-form__progress-label');
    this.backBtn = this.formEl.querySelector('[data-action="back"]');
    this.nextBtn = this.formEl.querySelector('[data-action="next"]');
    this.submitBtn = this.formEl.querySelector('[data-action="submit"]');
    this.successEl = this.formEl.querySelector('.msiq-form__success');

    var self = this;

    if (this.backBtn) {
      this.backBtn.addEventListener('click', function (e) {
        e.preventDefault();
        self.back();
      });
    }
    if (this.nextBtn) {
      this.nextBtn.addEventListener('click', function (e) {
        e.preventDefault();
        self.next();
      });
    }

    this.formEl.addEventListener('submit', function (e) {
      if (self.onSubmit) {
        e.preventDefault();
        self._handleSubmit();
      }
    });

    // Fire start event on first user interaction
    var startListeners = ['input', 'change', 'click'];
    startListeners.forEach(function (evt) {
      self.formEl.addEventListener(evt, function () {
        if (!self.hasStarted) {
          self.hasStarted = true;
          self._track('start');
        }
      }, { once: true });
    });

    this._updateProgress();
    this._updateButtons();
  };

  MSIQForm.prototype.next = function () {
    if (!this._validateStep(this.currentStep)) return;
    var targetStep = this.currentStep + 1;
    while (
      targetStep <= this.totalSteps &&
      !this._shouldShowStep(targetStep)
    ) {
      targetStep += 1;
    }
    if (targetStep > this.totalSteps) {
      // No more steps; submit
      this._handleSubmit();
      return;
    }
    this._goToStep(targetStep);
    this._track('step_advance', { step: targetStep });
  };

  MSIQForm.prototype.back = function () {
    var targetStep = this.currentStep - 1;
    while (targetStep >= 1 && !this._shouldShowStep(targetStep)) {
      targetStep -= 1;
    }
    if (targetStep < 1) return;
    this._goToStep(targetStep);
  };

  MSIQForm.prototype._goToStep = function (step) {
    this.stepEls.forEach(function (el) {
      el.classList.remove('msiq-form__step--active');
    });
    var target = this.stepEls.find(function (el) {
      return parseInt(el.getAttribute('data-step'), 10) === step;
    });
    if (target) {
      target.classList.add('msiq-form__step--active');
      // Scroll into view (smooth on supported browsers)
      target.scrollIntoView({ behavior: 'smooth', block: 'start' });
      // Focus first input in the new step for keyboard accessibility
      var firstInput = target.querySelector(
        'input:not([type=hidden]), select, textarea'
      );
      if (firstInput) {
        setTimeout(function () {
          firstInput.focus({ preventScroll: true });
        }, 350);
      }
    }
    this.currentStep = step;
    this._updateProgress();
    this._updateButtons();
    if (this.onStepChange) this.onStepChange(step);
  };

  MSIQForm.prototype._shouldShowStep = function (step) {
    var key = 'step-' + step;
    if (typeof this.conditionalLogic[key] !== 'function') return true;
    return this.conditionalLogic[key](this._collectData());
  };

  MSIQForm.prototype._validateStep = function (step) {
    var stepEl = this.stepEls.find(function (el) {
      return parseInt(el.getAttribute('data-step'), 10) === step;
    });
    if (!stepEl) return true;

    var fields = stepEl.querySelectorAll('.msiq-form__field');
    var valid = true;

    fields.forEach(function (fieldEl) {
      fieldEl.classList.remove('msiq-form__field--invalid');
      var input = fieldEl.querySelector('input, select, textarea');
      if (!input) return;
      // Skip honeypot fields
      if (input.classList.contains('msiq-form__honeypot')) return;
      if (input.type === 'hidden') return;

      var value = (input.value || '').trim();
      var required = input.hasAttribute('required');
      var errorEl = fieldEl.querySelector('.msiq-form__error');

      // Required check
      if (required && !value) {
        valid = false;
        fieldEl.classList.add('msiq-form__field--invalid');
        if (errorEl && !errorEl.textContent) {
          errorEl.textContent = 'This field is required.';
        }
        return;
      }

      // Email format check
      if (input.type === 'email' && value) {
        var emailRe = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRe.test(value)) {
          valid = false;
          fieldEl.classList.add('msiq-form__field--invalid');
          if (errorEl) errorEl.textContent = 'Please enter a valid email address.';
          return;
        }
      }

      // Honeypot check (if filled, treat as spam — fail silently)
      var honeypot = stepEl.querySelector('.msiq-form__honeypot');
      if (honeypot && honeypot.value) {
        valid = false;
      }
    });

    // Radio / checkbox group required check
    var groups = stepEl.querySelectorAll(
      '.msiq-form__choice-group[data-required="true"]'
    );
    groups.forEach(function (group) {
      var checked = group.querySelectorAll('input:checked');
      if (checked.length === 0) {
        valid = false;
        var parentField = group.closest('.msiq-form__field');
        if (parentField) {
          parentField.classList.add('msiq-form__field--invalid');
          var errorEl = parentField.querySelector('.msiq-form__error');
          if (errorEl && !errorEl.textContent) {
            errorEl.textContent = 'Please select an option.';
          }
        }
      }
    });

    // Custom validator for this step (if registered)
    if (typeof this.customValidators[step] === 'function') {
      var customResult = this.customValidators[step](this._collectData(), stepEl);
      if (customResult !== true) valid = false;
    }

    return valid;
  };

  MSIQForm.prototype._collectData = function () {
    var data = {};
    var formData = new FormData(this.formEl);
    formData.forEach(function (value, key) {
      // For multi-value keys (checkboxes), append to array
      if (data.hasOwnProperty(key)) {
        if (!Array.isArray(data[key])) {
          data[key] = [data[key]];
        }
        data[key].push(value);
      } else {
        data[key] = value;
      }
    });
    return data;
  };

  MSIQForm.prototype._updateProgress = function () {
    if (!this.progressFillEl) return;
    var pct = (this.currentStep / this.totalSteps) * 100;
    this.progressFillEl.style.width = pct + '%';
    if (this.progressLabelEl) {
      this.progressLabelEl.textContent =
        'Step ' + this.currentStep + ' of ' + this.totalSteps;
    }
  };

  MSIQForm.prototype._updateButtons = function () {
    if (this.backBtn) {
      this.backBtn.style.display = this.currentStep > 1 ? '' : 'none';
    }
    if (this.nextBtn && this.submitBtn) {
      var isLastStep = this.currentStep >= this.totalSteps;
      this.nextBtn.style.display = isLastStep ? 'none' : '';
      this.submitBtn.style.display = isLastStep ? '' : 'none';
    }
  };

  MSIQForm.prototype._handleSubmit = function () {
    if (!this._validateStep(this.currentStep)) return;

    var data = this._collectData();
    var self = this;

    var submitTarget = this.submitBtn || this.nextBtn;
    if (submitTarget) {
      submitTarget.classList.add('msiq-form__btn--loading');
      submitTarget.disabled = true;
    }

    if (this.onSubmit) {
      Promise.resolve(this.onSubmit(data))
        .then(function (result) {
          self._showSuccess(result);
          self._track('complete');
        })
        .catch(function (err) {
          console.error('MSIQForm submit error:', err);
          if (submitTarget) {
            submitTarget.classList.remove('msiq-form__btn--loading');
            submitTarget.disabled = false;
          }
          alert(
            'Something went wrong submitting the form. Please try again or email scott@mainstreetiq.com.'
          );
        });
    } else {
      // Native form submit (e.g., POST to Zoho Web-to-Lead)
      self._track('complete');
      self.formEl.submit();
    }
  };

  MSIQForm.prototype._showSuccess = function (result) {
    // Hide all steps
    this.stepEls.forEach(function (el) {
      el.classList.remove('msiq-form__step--active');
      el.style.display = 'none';
    });
    // Hide progress + buttons
    var progress = this.formEl.querySelector('.msiq-form__progress');
    var buttons = this.formEl.querySelector('.msiq-form__buttons');
    if (progress) progress.style.display = 'none';
    if (buttons) buttons.style.display = 'none';
    // Show success
    if (this.successEl) {
      this.successEl.classList.add('msiq-form__success--active');
      // Allow result.message to customize the success body
      if (result && result.message) {
        var bodyEl = this.successEl.querySelector('.msiq-form__success-body');
        if (bodyEl) bodyEl.textContent = result.message;
      }
      this.successEl.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  };

  MSIQForm.prototype._track = function (event, extra) {
    if (typeof global.gtag !== 'function') return;
    var category = this.analytics.category || this.formEl.id || 'msiq_form';
    var eventName = category + '_' + event;
    var payload = Object.assign(
      { page_path: global.location ? global.location.pathname : '' },
      extra || {}
    );
    try {
      global.gtag('event', eventName, payload);
    } catch (e) {
      // Silent — analytics failures don't break forms
    }
  };

  // Expose globally
  global.MSIQForm = MSIQForm;
})(typeof window !== 'undefined' ? window : this);
