"""Browser-side character filtering for the demo checkout's numeric fields."""


def numeric_payment_input_guard() -> str:
    """Return a scoped script that restricts active payment inputs as entered.

    Streamlit's ``text_input`` has no keypress callback. This listener blocks
    non-digits before insertion, sanitizes paste/input fallbacks, and notifies
    Streamlit's controlled input state after applying display formatting.
    """
    return r"""<script>
(() => {
  const rules = {
    'Cardholder name (test)': { name: true },
    'Test card number': { max: 16, grouping: 4 },
    'Expiry (MM/YY)': { max: 4, slash: 2 },
    'Test CVV': { max: 3 },
    'DuitNow mobile number': { max: 11, phone: true },
    'Mobile number': { max: 11, phone: true },
  };

  function digitsOnly(value, rule) {
    let digits = Array.from(String(value || ''))
      .filter((character) => character >= '0' && character <= '9')
      .join('');
    if (rule.phone && digits.startsWith('60')) digits = `0${digits.slice(2)}`;
    return digits.slice(0, rule.max);
  }

  function format(digits, rule) {
    if (rule.slash && digits.length > rule.slash) {
      return `${digits.slice(0, rule.slash)}/${digits.slice(rule.slash)}`;
    }
    if (rule.grouping) {
      return digits.match(new RegExp(`.{1,${rule.grouping}}`, 'g'))?.join(' ') || '';
    }
    return digits;
  }

  function digitOffset(value, cursor, rule) {
    return digitsOnly(value.slice(0, cursor), rule).length;
  }

  function cursorForOffset(value, offset, rule) {
    if (offset <= 0) return 0;
    let seen = 0;
    for (let index = 0; index < value.length; index += 1) {
      if (value[index] >= '0' && value[index] <= '9') seen += 1;
      if (seen >= offset) return index + 1;
      if (rule.slash && value[index] === '/' && seen === offset) return index + 1;
    }
    return value.length;
  }

  function setReactAwareValue(input, value) {
    const view = input.ownerDocument.defaultView;
    const setter = Object.getOwnPropertyDescriptor(view.HTMLInputElement.prototype, 'value')?.set;
    if (setter) setter.call(input, value);
    else input.value = value;
    input.dispatchEvent(new view.Event('input', { bubbles: true }));
  }

  function install(input, rule) {
    if (input.dataset.aqNumericGuard === 'on') return;
    input.dataset.aqNumericGuard = 'on';
    if (rule.name) {
      const stripDigits = (value) => String(value || '').replace(/[^A-Za-z ]/g, '');
      input.addEventListener('beforeinput', (event) => {
        if (event.inputType?.startsWith('insert') && event.data && /[^A-Za-z ]/.test(event.data)) event.preventDefault();
      });
      input.addEventListener('keydown', (event) => {
        if (!event.ctrlKey && !event.metaKey && !event.altKey && event.key.length === 1 && /[^A-Za-z ]/.test(event.key)) event.preventDefault();
      });
      input.addEventListener('paste', (event) => {
        event.preventDefault();
        const value = input.value;
        const start = input.selectionStart ?? value.length;
        const end = input.selectionEnd ?? start;
        const inserted = stripDigits(event.clipboardData?.getData('text') || '');
        const next = `${value.slice(0, start)}${inserted}${value.slice(end)}`;
        setReactAwareValue(input, stripDigits(next));
        const removedBeforeCaret = value.slice(0, start).length - stripDigits(value.slice(0, start)).length;
        const caret = Math.max(0, start - removedBeforeCaret) + inserted.length;
        input.setSelectionRange(caret, caret);
      });
      input.addEventListener('input', () => {
        const current = input.value;
        const cursor = input.selectionStart ?? current.length;
        const cleaned = stripDigits(current);
        if (cleaned === current) return;
        const removedBeforeCaret = current.slice(0, cursor).length - stripDigits(current.slice(0, cursor)).length;
        setReactAwareValue(input, cleaned);
        const caret = Math.max(0, cursor - removedBeforeCaret);
        input.setSelectionRange(caret, caret);
      });
      const cleaned = stripDigits(input.value);
      if (cleaned !== input.value) setReactAwareValue(input, cleaned);
      return;
    }
    input.setAttribute('inputmode', 'numeric');
    input.setAttribute('pattern', '[0-9]*');
    input.setAttribute('autocomplete', 'off');
    input.setAttribute('maxlength', String(rule.max + (rule.grouping ? Math.floor((rule.max - 1) / rule.grouping) : rule.slash ? 1 : 0)));

    let digitCounter;
    if (rule.slash) {
      const widget = input.closest('[data-testid="stTextInput"]');
      const label = widget?.querySelector('label');
      if (label) {
        digitCounter = document.createElement('span');
        digitCounter.className = 'aq-payment-digit-counter';
        digitCounter.setAttribute('aria-live', 'polite');
        digitCounter.style.cssText = 'margin-left:auto;padding-left:12px;font-size:.75rem;font-weight:400;color:var(--aq-muted,#8295a5);white-space:nowrap';
        label.style.display = 'flex';
        label.style.alignItems = 'center';
        label.appendChild(digitCounter);
      }
    }
    const updateDigitCounter = () => {
      if (digitCounter) digitCounter.textContent = `${digitsOnly(input.value, rule).length}/${rule.max}`;
    };
    updateDigitCounter();

    input.addEventListener('beforeinput', (event) => {
      if (!event.inputType || !event.inputType.startsWith('insert') || event.inputType === 'insertFromPaste') return;
      if (event.data && /[^0-9]/.test(event.data)) event.preventDefault();
    });

    input.addEventListener('keydown', (event) => {
      if (event.ctrlKey || event.metaKey || event.altKey) return;
      if (event.key.length === 1 && !/^[0-9]$/.test(event.key)) event.preventDefault();
      if (/^[0-9]$/.test(event.key)) {
        const selectionLength = Math.abs((input.selectionEnd || 0) - (input.selectionStart || 0));
        const count = digitsOnly(input.value, rule).length;
        if (count - selectionLength >= rule.max) event.preventDefault();
      }
    });

    input.addEventListener('paste', (event) => {
      event.preventDefault();
      const view = input.ownerDocument.defaultView;
      const pasted = event.clipboardData?.getData('text') || '';
      const start = input.selectionStart ?? input.value.length;
      const end = input.selectionEnd ?? start;
      const before = digitsOnly(input.value.slice(0, start), rule);
      const selected = digitsOnly(input.value.slice(start, end), rule).length;
      const current = digitsOnly(input.value, rule);
      const remaining = rule.max - before.length - (current.length - before.length - selected);
      const insertion = digitsOnly(pasted, rule).slice(0, Math.max(0, remaining));
      const nextDigits = `${before}${insertion}${current.slice(before.length + selected)}`.slice(0, rule.max);
      const nextValue = format(nextDigits, rule);
      setReactAwareValue(input, nextValue);
      const cursor = cursorForOffset(nextValue, before.length + insertion.length, rule);
      input.setSelectionRange(cursor, cursor);
    });

    input.addEventListener('input', () => {
      updateDigitCounter();
      const oldValue = input.value;
      const oldCursor = input.selectionStart ?? oldValue.length;
      const offset = digitOffset(oldValue, oldCursor, rule);
      const nextValue = format(digitsOnly(oldValue, rule), rule);
      if (nextValue === oldValue) return;
      setReactAwareValue(input, nextValue);
      const cursor = cursorForOffset(nextValue, offset, rule);
      input.setSelectionRange(cursor, cursor);
    });
  }

  function scan(document) {
    document.querySelectorAll('input[aria-label]').forEach((input) => {
      const rule = rules[input.getAttribute('aria-label')];
      if (rule) install(input, rule);
    });
  }

  // st.html runs in a same-origin frame. Use its parent document so the guard
  // attaches directly to Streamlit's real text inputs, not a separate widget.
  let document;
  try { document = window.parent.document; } catch (_) { return; }
  scan(document);
  new MutationObserver(() => scan(document)).observe(document.body, { childList: true, subtree: true });
})();
</script>"""
