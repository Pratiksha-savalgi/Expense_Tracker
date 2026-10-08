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

const registrationForm = document.querySelector("[data-registration-form]");
if (registrationForm) {
  const usernameInput = registrationForm.querySelector("#username");
  const roleSelect = registrationForm.querySelector("#role");
  const passwordInput = registrationForm.querySelector("#password");
  const confirmationInput = registrationForm.querySelector("#confirm_password");
  const feedback = registrationForm.querySelector("[data-registration-feedback]");
  const submitButton = registrationForm.querySelector('button[type="submit"]');
  const errorElements = Object.fromEntries(
    [...registrationForm.querySelectorAll("[data-registration-error]")].map((element) => [
      element.dataset.registrationError,
      element,
    ]),
  );
  const touchedFields = new Set();
  const usernamePattern = /^(?=.*[A-Za-z])(?=.*[0-9])(?=.*[_@])[A-Za-z0-9_@]{3,15}$/;
  const passwordPattern = /^(?=.*[A-Z])(?=.*[a-z])(?=.*[0-9])(?=.*[^A-Za-z0-9\s])\S{8,36}$/;
  const commonPasswords = new Set([
    "password123!",
    "password1!",
    "qwerty123!",
    "letmein123!",
    "welcome123!",
    "admin123!",
    "iloveyou1!",
    "changeme123!",
    "p@ssw0rd123!",
    "qwertyuiop1!",
  ]);

  const validateRegistration = () => {
    const username = usernameInput.value;
    const password = passwordInput.value;
    const confirmation = confirmationInput.value;
    const errors = {
      username: "",
      role: "",
      password: "",
      confirm_password: "",
    };

    if (!username) {
      errors.username = "Enter a username.";
    } else if (!usernamePattern.test(username)) {
      errors.username = "Use 3–15 letters, numbers, underscores, or @, including at least one letter, one number, and one underscore or @.";
    }

    if (!roleSelect.value) {
      errors.role = "Choose your role.";
    }

    if (!password) {
      errors.password = "Enter a password.";
    } else if (!passwordPattern.test(password)) {
      errors.password = "Use 8–36 characters with uppercase and lowercase letters, a number, and a symbol. Spaces are not allowed.";
    } else if (commonPasswords.has(password.toLowerCase())) {
      errors.password = "Choose a less common password.";
    }

    if (!confirmation) {
      errors.confirm_password = "Confirm your password.";
    } else if (password !== confirmation) {
      errors.confirm_password = "Passwords do not match.";
    }

    const fields = {
      username: usernameInput,
      role: roleSelect,
      password: passwordInput,
      confirm_password: confirmationInput,
    };
    Object.entries(fields).forEach(([name, field]) => {
      const errorElement = errorElements[name];
      const submittedValue = errorElement.dataset.serverValue;
      const serverError = errorElement.dataset.serverError;
      const currentValue = field.value;
      if (!errors[name] && serverError && currentValue === submittedValue) {
        errors[name] = serverError;
      } else if (currentValue !== submittedValue) {
        errorElement.dataset.serverError = "";
      }

      const shouldShowError = Boolean(errors[name]) && (
        touchedFields.has(name) || Boolean(errorElement.dataset.serverError)
      );
      errorElement.textContent = shouldShowError ? errors[name] : "";
      errorElement.hidden = !shouldShowError;
      field.setAttribute("aria-invalid", String(shouldShowError));
    });

    const hasErrors = Object.values(errors).some(Boolean);
    submitButton.disabled = hasErrors;
    feedback.classList.toggle("has-errors", hasErrors);
    feedback.textContent = hasErrors
      ? "Complete the highlighted fields to enable account creation."
      : "All set. You can create your account.";
  };

  [
    ["username", usernameInput],
    ["role", roleSelect],
    ["password", passwordInput],
    ["confirm_password", confirmationInput],
  ].forEach(([name, input]) => {
    input.addEventListener("input", () => {
      touchedFields.add(name);
      validateRegistration();
    });
    input.addEventListener("change", () => {
      touchedFields.add(name);
      validateRegistration();
    });
    input.addEventListener("blur", () => {
      touchedFields.add(name);
      validateRegistration();
    });
  });
  [passwordInput, confirmationInput].forEach((input) => {
    input.addEventListener("paste", (event) => event.preventDefault());
  });
  registrationForm.addEventListener("submit", (event) => {
    touchedFields.add("username");
    touchedFields.add("role");
    touchedFields.add("password");
    touchedFields.add("confirm_password");
    validateRegistration();
    if (submitButton.disabled) event.preventDefault();
  });
  validateRegistration();
}

const loginForm = document.querySelector("[data-login-form]");
if (loginForm) {
  const usernameInput = loginForm.querySelector("#username");
  const passwordInput = loginForm.querySelector("#password");
  const submitButton = loginForm.querySelector('button[type="submit"]');
  const fields = { username: usernameInput, password: passwordInput };
  const errorElements = Object.fromEntries(
    [...loginForm.querySelectorAll("[data-login-error]")].map((element) => [
      element.dataset.loginError,
      element,
    ]),
  );
  const touchedFields = new Set(
    Object.entries(errorElements)
      .filter(([, element]) => !element.hidden)
      .map(([name]) => name),
  );

  const validateLogin = () => {
    Object.entries(fields).forEach(([name, field]) => {
      const errorElement = errorElements[name];
      const message = field.value ? "" : `Enter your ${name === "username" ? "username" : "password"}.`;
      const showError = !field.value && touchedFields.has(name);
      errorElement.textContent = showError ? message : "";
      errorElement.hidden = !showError;
      field.setAttribute("aria-invalid", String(showError));
    });

    submitButton.disabled = !usernameInput.value || !passwordInput.value;
  };

  Object.entries(fields).forEach(([name, field]) => {
    ["input", "change", "blur"].forEach((eventName) => {
      field.addEventListener(eventName, () => {
        if (eventName === "blur" || field.value) touchedFields.add(name);
        validateLogin();
      });
    });
  });
  loginForm.addEventListener("submit", (event) => {
    touchedFields.add("username");
    touchedFields.add("password");
    validateLogin();
    if (submitButton.disabled) event.preventDefault();
  });
  validateLogin();
}

const expenseModal = document.querySelector("[data-expense-modal]");
if (expenseModal) {
  const modalForm = expenseModal.querySelector("[data-modal-expense-form]");
  const modalDatePicker = expenseModal.querySelector("[data-modal-date-picker]");
  const modalPeriodInput = expenseModal.querySelector("[data-modal-date-period-value]");
  const modalDatePeriodButtons = expenseModal.querySelectorAll("[data-modal-date-period]");
  const successMessage = expenseModal.querySelector("[data-expense-save-success]");
  const saveConfirmation = expenseModal.querySelector("[data-confirm-expense-save]");

  const todayIso = () => expenseModal.dataset.today;
  const yesterdayIso = () => expenseModal.dataset.yesterday;
  const setActiveDatePeriod = (period) => {
    modalPeriodInput.value = period;
    modalDatePeriodButtons.forEach((button) => {
      const isActive = button.dataset.modalDatePeriod === period;
      button.classList.toggle("is-active", isActive);
      button.setAttribute("aria-pressed", String(isActive));
    });
    modalDatePicker.closest(".date-picker-option").classList.toggle("is-active", period === "custom");
  };

  modalDatePicker.max = todayIso();
  modalDatePeriodButtons.forEach((button) => {
    button.addEventListener("click", () => {
      const period = button.dataset.modalDatePeriod;
      modalDatePicker.value = period === "yesterday" ? yesterdayIso() : todayIso();
      setActiveDatePeriod(period);
    });
  });
  modalDatePicker.addEventListener("click", () => {
    setActiveDatePeriod("custom");
  });
  modalDatePicker.addEventListener("change", () => {
    if (modalDatePicker.value) setActiveDatePeriod("custom");
  });

  modalForm.addEventListener("submit", (event) => {
    const amountInput = modalForm.querySelector("#modal-amount");
    if (!amountInput.value) {
      amountInput.setCustomValidity("Enter an amount.");
    } else if (Number(amountInput.value) <= 0) {
      amountInput.setCustomValidity("Amount must be greater than zero.");
    } else if (amountInput.validity.stepMismatch) {
      amountInput.setCustomValidity("Amount must use no more than two decimal places.");
    } else {
      amountInput.setCustomValidity("");
    }

    if (!modalDatePicker.value || modalDatePicker.value > todayIso()) {
      modalDatePicker.setCustomValidity("Choose a valid date no later than today.");
    } else {
      modalDatePicker.setCustomValidity("");
    }

    if (!modalForm.reportValidity()) event.preventDefault();
  });

  expenseModal.addEventListener("cancel", (event) => event.preventDefault());
  if (expenseModal.dataset.autoOpen === "true" && !expenseModal.open) expenseModal.showModal();

  if (successMessage) {
    saveConfirmation.focus();
    saveConfirmation.addEventListener("click", () => {
      successMessage.hidden = true;
      modalForm.reset();
      modalForm.querySelector("#modal-amount").setCustomValidity("");
      modalDatePicker.setCustomValidity("");
      modalDatePicker.max = todayIso();
      modalDatePicker.value = todayIso();
      setActiveDatePeriod("today");
      modalForm.querySelector("#modal-amount").focus();
    });
  } else if (modalForm.querySelector("#modal-amount").value) {
    modalForm.querySelector("#modal-amount").focus();
  }
}

document.querySelectorAll("[data-open-expense-modal]").forEach((button) => {
  button.addEventListener("click", () => {
    if (expenseModal && !expenseModal.open) expenseModal.showModal();
  });
});

const expenseForm = document.querySelector("[data-expense-form]");
if (expenseForm) {
  const categorySelect = expenseForm.querySelector("#category");
  const newCategoryField = expenseForm.querySelector("#new-category-field");
  const newCategoryInput = expenseForm.querySelector("#new_category");
  const amountInput = expenseForm.querySelector("#amount");
  const datePicker = expenseForm.querySelector("[data-custom-date-picker]");
  const periodInput = expenseForm.querySelector("[data-expense-period]");
  const dateValue = expenseForm.querySelector("[data-custom-date-value]");
  const transactionDate = expenseForm.querySelector("[data-transaction-date]");
  const intentInput = expenseForm.querySelector("[data-expense-intent]");

  const toIsoDate = (value) => {
    const localDate = new Date(value.getTime() - (value.getTimezoneOffset() * 60000));
    return localDate.toISOString().split("T")[0];
  };
  const todayIso = () => toIsoDate(new Date());
  const yesterdayIso = () => {
    const yesterday = new Date();
    yesterday.setDate(yesterday.getDate() - 1);
    return toIsoDate(yesterday);
  };
  const submitFilter = () => {
    intentInput.value = "filter";
    expenseForm.noValidate = true;
    expenseForm.requestSubmit();
  };

  const updateNewCategoryField = () => {
    const addingCategory = categorySelect.value === "__new__";
    newCategoryField.hidden = !addingCategory;
    newCategoryInput.required = addingCategory;
    if (!addingCategory) newCategoryInput.value = "";
  };

  datePicker.max = todayIso();
  datePicker.addEventListener("change", () => {
    if (!datePicker.value) return;
    periodInput.value = "custom";
    dateValue.value = datePicker.value;
    transactionDate.value = datePicker.value;
    submitFilter();
  });

  expenseForm.addEventListener("click", (event) => {
    const quickFilter = event.target.closest("[data-date-period]");
    if (!quickFilter) return;

    const selectedPeriod = quickFilter.dataset.datePeriod;
    periodInput.value = selectedPeriod;
    dateValue.value = "";
    datePicker.value = todayIso();
    transactionDate.value = selectedPeriod === "yesterday" ? yesterdayIso() : todayIso();
    submitFilter();
  });

  categorySelect.addEventListener("change", () => {
    updateNewCategoryField();
    submitFilter();
  });
  updateNewCategoryField();

  amountInput.addEventListener("input", () => {
    if (!amountInput.value) {
      amountInput.setCustomValidity("Enter an amount.");
    } else if (Number(amountInput.value) <= 0) {
      amountInput.setCustomValidity("Amount must be greater than zero.");
    } else if (amountInput.validity.stepMismatch) {
      amountInput.setCustomValidity("Amount must use no more than two decimal places.");
    } else {
      amountInput.setCustomValidity("");
    }
  });
  expenseForm.addEventListener("submit", (event) => {
    if (intentInput.value === "filter") {
      expenseForm.noValidate = false;
      return;
    }
    intentInput.value = "save";
    expenseForm.noValidate = false;
    if (!expenseForm.reportValidity()) event.preventDefault();
  });
}

const expenseCategoryFilter = document.querySelector("#category-filter");
if (expenseCategoryFilter) {
  expenseCategoryFilter.addEventListener("change", () => expenseCategoryFilter.form.requestSubmit());
}

const analyticsFilters = document.querySelector(".analytics-filters");
if (analyticsFilters) {
  const today = new Date();
  const currentYear = today.getFullYear();
  const currentMonth = today.getMonth() + 1;
  const yearSelect = analyticsFilters.querySelector('[name="year"]');
  const monthSelect = analyticsFilters.querySelector('[name="month"]');
  const daySelect = analyticsFilters.querySelector('[name="day"]');

  const datePeriod = new URLSearchParams(window.location.search).get("date_period");
  const dateValue = new URLSearchParams(window.location.search).get("date");
  if (datePeriod) {
    const periodInput = document.createElement("input");
    periodInput.type = "hidden";
    periodInput.name = "date_period";
    periodInput.value = datePeriod;
    analyticsFilters.append(periodInput);
  }
  if (dateValue) {
    const dateInput = document.createElement("input");
    dateInput.type = "hidden";
    dateInput.name = "date";
    dateInput.value = dateValue;
    analyticsFilters.append(dateInput);
  }

  const syncMonthOptions = () => {
    const selectedYear = Number(yearSelect.value || currentYear);
    const maxMonth = selectedYear === currentYear ? currentMonth : 12;
    const previousMonth = Number(monthSelect.value || currentMonth);

    [...monthSelect.options].forEach((option) => {
      const monthValue = Number(option.value);
      option.disabled = selectedYear === currentYear && monthValue > maxMonth;
    });

    if (previousMonth > maxMonth) {
      monthSelect.value = String(maxMonth);
    }
  };

  const updateDays = (preserveSelection) => {
    const previousDay = preserveSelection ? daySelect.value : "";
    const dayCount = new Date(Number(yearSelect.value), Number(monthSelect.value), 0).getDate();
    daySelect.replaceChildren(new Option("All days", ""));
    for (let day = 1; day <= dayCount; day += 1) {
      daySelect.add(new Option(String(day), String(day)));
    }
    if (Number(previousDay) <= dayCount) daySelect.value = previousDay;
  };

  yearSelect.addEventListener("change", () => {
    syncMonthOptions();
    updateDays(true);
  });
  monthSelect.addEventListener("change", () => updateDays(true));
  syncMonthOptions();
  updateDays(true);
}
