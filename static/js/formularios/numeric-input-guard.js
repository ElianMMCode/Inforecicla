const NumericInputGuard = (() => {
    const INTEGER_SELECTOR = 'input[data-numeric-integer]';
    const DECIMAL_SELECTOR = 'input[data-numeric-decimal]';
    const DIGITS_ONLY_SELECTOR = 'input[data-digits-only]';
    const ALL_SELECTOR = `${INTEGER_SELECTOR}, ${DECIMAL_SELECTOR}, ${DIGITS_ONLY_SELECTOR}`;

    const NAVIGATION_KEYS = new Set([
        'Backspace', 'Delete', 'ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown',
        'Home', 'End', 'Tab', 'Enter', 'Escape',
    ]);

    function isPrintableChar(key) {
        return typeof key === 'string' && key.length === 1 && !NAVIGATION_KEYS.has(key);
    }

    function isDecimalSeparator(key) {
        return key === '.' || key === ',';
    }

    function getInputKind(input) {
        if (input.matches(INTEGER_SELECTOR) || input.matches(DIGITS_ONLY_SELECTOR)) {
            return 'integer';
        }
        if (input.matches(DECIMAL_SELECTOR)) {
            return 'decimal';
        }
        return null;
    }

    function isKeyAllowed(input, key) {
        if (NAVIGATION_KEYS.has(key)) {
            return true;
        }
        if ((key >= '0' && key <= '9')) {
            return true;
        }
        const kind = getInputKind(input);
        if (kind === 'decimal' && isDecimalSeparator(key)) {
            return true;
        }
        return false;
    }

    function sanitizeInteger(value, maxLength) {
        const cleaned = value.replace(/\D+/g, '');
        return Number.isFinite(maxLength) && maxLength > 0
            ? cleaned.slice(0, maxLength)
            : cleaned;
    }

    function sanitizeDecimal(value) {
        const cleaned = value.replace(/[^\d.,]/g, '');
        const firstSepIdx = cleaned.search(/[.,]/);
        if (firstSepIdx < 0) {
            return cleaned;
        }
        const head = cleaned.slice(0, firstSepIdx + 1);
        const tail = cleaned.slice(firstSepIdx + 1).replace(/[.,]/g, '');
        return head + tail;
    }

    function sanitize(input) {
        const kind = getInputKind(input);
        if (!kind) {
            return;
        }
        if (input.readOnly || input.disabled) {
            return;
        }
        if (kind === 'integer') {
            const maxLength = Number.parseInt(input.dataset.digitsOnly || '0', 10);
            input.value = sanitizeInteger(input.value, maxLength);
        } else if (kind === 'decimal') {
            input.value = sanitizeDecimal(input.value);
        }
    }

    function handleKeydown(event) {
        const input = event.target;
        if (!(input instanceof HTMLInputElement)) {
            return;
        }
        if (!input.matches(ALL_SELECTOR)) {
            return;
        }
        if (input.readOnly || input.disabled) {
            return;
        }
        if (event.ctrlKey || event.metaKey || event.altKey) {
            return;
        }
        if (!isPrintableChar(event.key)) {
            return;
        }
        if (!isKeyAllowed(input, event.key)) {
            event.preventDefault();
        }
    }

    function handleInput(event) {
        const input = event.target;
        if (!(input instanceof HTMLInputElement)) {
            return;
        }
        if (!input.matches(ALL_SELECTOR)) {
            return;
        }
        sanitize(input);
    }

    function handlePaste(event) {
        const input = event.target;
        if (!(input instanceof HTMLInputElement)) {
            return;
        }
        if (!input.matches(ALL_SELECTOR)) {
            return;
        }
        globalThis.setTimeout(() => sanitize(input), 0);
    }

    function init() {
        document.addEventListener('keydown', handleKeydown, true);
        document.addEventListener('input', handleInput);
        document.addEventListener('paste', handlePaste);
        document.addEventListener('blur', handleInput, true);
    }

    return { init, sanitize };
})();

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        NumericInputGuard.init();
    }, { once: true });
} else {
    NumericInputGuard.init();
}
