document.addEventListener("submit", (event) => {
  const message = event.target.dataset.confirm;
  if (message && !window.confirm(message)) {
    event.preventDefault();
  }
});

document.addEventListener("click", (event) => {
  const toggle = event.target.closest("[data-password-toggle]");
  if (!toggle) return;

  const passwordInput = document.getElementById(toggle.dataset.passwordToggle);
  if (!passwordInput) return;

  const isVisible = passwordInput.type === "password";
  const label = isVisible ? "Hide password" : "Show password";
  passwordInput.type = isVisible ? "text" : "password";
  toggle.setAttribute("aria-label", label);
  toggle.setAttribute("aria-pressed", String(isVisible));
  toggle.title = label;
});

const registrationForm = document.querySelector("[data-password-confirm]");
if (registrationForm) {
  const passwordInput = registrationForm.querySelector("#password");
  const confirmationInput = registrationForm.querySelector("#confirm_password");
  const validatePasswordMatch = () => {
    const mismatch = confirmationInput.value && passwordInput.value !== confirmationInput.value;
    confirmationInput.setCustomValidity(mismatch ? "Passwords do not match." : "");
  };

  passwordInput.addEventListener("input", validatePasswordMatch);
  confirmationInput.addEventListener("input", validatePasswordMatch);
}