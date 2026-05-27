// Client-side contact form validation and UX
document.addEventListener('DOMContentLoaded', () => {
  const form = document.querySelector('#contact-form form') || document.querySelector('form');
  if (!form) return;

  form.addEventListener('submit', (e) => {
    // basic HTML5 validation will run; enhance UX
    if (!form.checkValidity()) {
      e.preventDefault();
      e.stopPropagation();
      form.classList.add('was-validated');
      return;
    }

    // show simple feedback while backend handles submission
    const submit = form.querySelector('[type=submit]');
    if (submit) {
      submit.disabled = true;
      const old = submit.innerHTML;
      submit.innerHTML = 'Sending…';
      // allow default submit to proceed; if you use AJAX, handle fetch here
      setTimeout(() => {
        submit.disabled = false;
        submit.innerHTML = old;
      }, 3000);
    }
  });
});
