document.addEventListener("submit", (event) => {
  const message = event.target.dataset.confirm;
  if (message && !window.confirm(message)) {
    event.preventDefault();
  }
});

document.addEventListener("click", (event) => {
  const point = event.target.closest("[data-month-point]");
  const points = document.querySelectorAll("[data-month-point]");
  if (point) {
    const wasActive = point.classList.contains("is-active");
    points.forEach((item) => item.classList.remove("is-active"));
    if (!wasActive) {
      point.classList.add("is-active");
    } else {
      point.blur();
    }
    return;
  }
  points.forEach((item) => item.classList.remove("is-active"));
});

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape") {
    document.querySelectorAll("[data-month-point].is-active").forEach((point) => {
      point.classList.remove("is-active");
      point.blur();
    });
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
    } else if (
      !/^(?:\d+(?:\.\d{1,2})?|\.\d{1,2})$/.test(amountInput.value) ||
      amountInput.validity.stepMismatch
    ) {
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
  if (expenseModal.dataset.autoOpen === "true" && !expenseModal.open) {
    const openExpenseModal = () => {
      requestAnimationFrame(() => {
        requestAnimationFrame(() => {
          if (!expenseModal.isConnected || expenseModal.open) return;
          expenseModal.showModal();
          if (successMessage) {
            saveConfirmation.focus();
          } else if (modalForm.querySelector("#modal-amount").value) {
            modalForm.querySelector("#modal-amount").focus();
          }
        });
      });
    };

    if (document.readyState === "complete") {
      openExpenseModal();
    } else {
      window.addEventListener("load", openExpenseModal, { once: true });
    }
  }

  if (successMessage) {
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
  }
}

document.addEventListener("click", (event) => {
  if (!event.target.closest("[data-open-expense-modal]")) return;
  if (expenseModal && !expenseModal.open) expenseModal.showModal();
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
    } else if (
      !/^(?:\d+(?:\.\d{1,2})?|\.\d{1,2})$/.test(amountInput.value) ||
      amountInput.validity.stepMismatch
    ) {
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

const dashboardFilters = document.querySelector("[data-dashboard-filters]");
if (dashboardFilters) {
  const monthInput = dashboardFilters.querySelector('[name="month"]');
  const yearInput = dashboardFilters.querySelector('[name="year"]');
  const dayInput = dashboardFilters.querySelector('[name="day"]');
  const calendar = dashboardFilters.querySelector("[data-dashboard-calendar]");
  const todayIso = dashboardFilters.dataset.today;
  const [todayYear, todayMonth] = todayIso.split("-").map(Number);
  const allowedYears = new Set(dashboardFilters.dataset.years.split(",").map(Number));
  const toIso = (year, month, day) => (
    `${year}-${String(month).padStart(2, "0")}-${String(day).padStart(2, "0")}`
  );

  const syncDashboardOptions = () => {
    calendar.max = todayIso;
    calendar.min = `${Math.min(...allowedYears)}-01-01`;
    if (!dayInput.value) {
      calendar.value = "";
      return;
    }
    const iso = toIso(yearInput.value, monthInput.value, dayInput.value);
    if (iso > todayIso || !allowedYears.has(Number(yearInput.value))) {
      dayInput.value = "";
      yearInput.value = String(todayYear);
      monthInput.value = String(todayMonth);
      calendar.value = "";
      return;
    }
    calendar.value = iso;
  };

  const pageInput = dashboardFilters.querySelector('[name="page"]');
  const resetPage = () => {
    if (pageInput) pageInput.value = "1";
  };
  const results = document.querySelector("[data-expense-results]");
  const expenseSection = results.closest(".dashboard-recent-card");
  let expenseRequest = 0;

  const refreshExpenseList = async () => {
    const requestId = expenseRequest + 1;
    expenseRequest = requestId;
    const params = new URLSearchParams(new FormData(dashboardFilters));
    const url = `${dashboardFilters.action}?${params.toString()}`;
    expenseSection.setAttribute("aria-busy", "true");
    try {
      const response = await fetch(url, {
        headers: { "X-Dashboard-Fragment": "expenses" },
        credentials: "same-origin",
      });
      if (!response.ok || requestId !== expenseRequest) return;
      results.innerHTML = await response.text();
      const fragment = results.querySelector("[data-expense-fragment]");
      if (fragment) {
        if (fragment.dataset.year) yearInput.value = fragment.dataset.year;
        if (fragment.dataset.month) monthInput.value = fragment.dataset.month;
        dayInput.value = fragment.dataset.day || "";
        syncDashboardOptions();
        if (pageInput) pageInput.value = fragment.dataset.page || "1";
      }
      if (requestId === expenseRequest) window.history.replaceState(null, "", url);
    } catch (error) {
      dashboardFilters.submit();
    } finally {
      if (requestId === expenseRequest) expenseSection.removeAttribute("aria-busy");
    }
  };

  calendar.addEventListener("change", () => {
    if (!calendar.value || calendar.value > todayIso) {
      dayInput.value = "";
      yearInput.value = String(todayYear);
      monthInput.value = String(todayMonth);
      calendar.value = "";
    } else {
      const [year, month, day] = calendar.value.split("-").map(Number);
      if (!allowedYears.has(year)) {
        dayInput.value = "";
        yearInput.value = String(todayYear);
        monthInput.value = String(todayMonth);
        calendar.value = "";
      } else {
        yearInput.value = String(year);
        monthInput.value = String(month);
        dayInput.value = String(day);
      }
    }
    syncDashboardOptions();
    resetPage();
    refreshExpenseList();
  });
  dashboardFilters.addEventListener("submit", (event) => {
    event.preventDefault();
    yearInput.value = String(todayYear);
    monthInput.value = String(todayMonth);
    dayInput.value = "";
    calendar.value = "";
    syncDashboardOptions();
    resetPage();
    refreshExpenseList();
  });
  document.addEventListener("click", (event) => {
    const pageLink = event.target.closest("[data-expense-page]");
    if (!pageLink || !results.contains(pageLink)) return;
    event.preventDefault();
    if (pageInput) pageInput.value = pageLink.dataset.expensePage;
    refreshExpenseList();
  });
  syncDashboardOptions();
}

const analyticsFilters = document.querySelector(".analytics-filters");
if (analyticsFilters) {
  const today = new Date();
  const currentYear = today.getFullYear();
  const currentMonth = today.getMonth() + 1;
  const yearSelect = analyticsFilters.querySelector('[name="year"]');
  const monthSelect = analyticsFilters.querySelector('[name="month"]');
  const daySelect = analyticsFilters.querySelector('[name="day"]');

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
    const maxDay = Number(yearSelect.value) === currentYear
      && Number(monthSelect.value) === currentMonth
      ? Math.min(dayCount, today.getDate())
      : dayCount;
    daySelect.replaceChildren(new Option("All days", ""));
    for (let day = 1; day <= maxDay; day += 1) {
      daySelect.add(new Option(String(day), String(day)));
    }
    if (Number(previousDay) <= maxDay) daySelect.value = previousDay;
  };

  yearSelect.addEventListener("change", () => {
    syncMonthOptions();
    updateDays(true);
  });
  monthSelect.addEventListener("change", () => updateDays(true));
  syncMonthOptions();
  updateDays(true);
}

const closeExpenseMenus = () => {
  document.querySelectorAll("[data-expense-row].is-selected").forEach((row) => {
    row.classList.remove("is-selected");
    row.setAttribute("aria-expanded", "false");
    const popover = row.querySelector(".expense-action-popover");
    if (popover) popover.hidden = true;
  });
};

const openExpenseMenu = (row) => {
  closeExpenseMenus();
  const popover = row.querySelector(".expense-action-popover");
  if (!popover) return;
  popover.hidden = false;
  row.classList.add("is-selected");
  row.setAttribute("aria-expanded", "true");
  const rect = row.getBoundingClientRect();
  const anchor = (row.querySelector(".dashboard-expense-amount") || row).getBoundingClientRect();
  const width = popover.offsetWidth;
  const top = Math.min(rect.top + rect.height / 2, window.innerHeight - popover.offsetHeight - 12);
  const left = Math.max(12, Math.min(anchor.right - width + 8, window.innerWidth - width - 12));
  popover.style.position = "fixed";
  popover.style.top = `${Math.max(12, top)}px`;
  popover.style.left = `${left}px`;
};

document.addEventListener("click", (event) => {
  if (event.target.closest(".expense-action-popover")) return;
  const row = event.target.closest("[data-expense-row]");
  if (!row) {
    closeExpenseMenus();
    return;
  }
  if (row.classList.contains("is-selected")) closeExpenseMenus();
  else openExpenseMenu(row);
});

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape") {
    closeExpenseMenus();
    return;
  }
  if (event.target.closest(".expense-action-popover")) return;
  const row = event.target.closest("[data-expense-row]");
  if (!row || (event.key !== "Enter" && event.key !== " ")) return;
  event.preventDefault();
  if (row.classList.contains("is-selected")) closeExpenseMenus();
  else openExpenseMenu(row);
});

window.addEventListener("resize", closeExpenseMenus);
window.addEventListener("scroll", closeExpenseMenus, true);

const budgetModal = document.querySelector("[data-budget-modal]");
if (budgetModal) {
  const amountInput = budgetModal.querySelector("#dashboard-budget-amount");
  const monthSelect = budgetModal.querySelector("[data-budget-month]");
  const openBudgetModal = () => {
    if (!budgetModal.open) budgetModal.showModal();
    amountInput.focus();
  };
  document.querySelectorAll("[data-open-budget-modal]").forEach((button) => {
    button.addEventListener("click", openBudgetModal);
  });
  budgetModal.querySelector("[data-close-budget-modal]").addEventListener("click", () => budgetModal.close());
  monthSelect.addEventListener("change", () => {
    amountInput.value = monthSelect.selectedOptions[0].dataset.budgetAmount || "";
    amountInput.setCustomValidity("");
  });
  budgetModal.querySelector("[data-budget-form]").addEventListener("submit", (event) => {
    if (!amountInput.value) {
      amountInput.setCustomValidity("Enter a budget amount.");
    } else if (Number(amountInput.value) <= 0) {
      amountInput.setCustomValidity("Budget amount must be greater than zero.");
    } else if (!/^(?:\d+(?:\.\d{1,2})?|\.\d{1,2})$/.test(amountInput.value)) {
      amountInput.setCustomValidity("Use no more than two decimal places.");
    } else {
      amountInput.setCustomValidity("");
    }
    if (!budgetModal.querySelector("[data-budget-form]").reportValidity()) event.preventDefault();
  });
  amountInput.addEventListener("input", () => amountInput.setCustomValidity(""));
  if (budgetModal.dataset.autoOpen === "true") openBudgetModal();
}

const swipeTrack = document.querySelector("[data-expense-swipe]");
if (swipeTrack) {
  const dots = [...swipeTrack.parentElement.querySelectorAll("[data-swipe-dot]")];
  const pages = [...swipeTrack.children];
  const markActiveDot = () => {
    if (!dots.length || !swipeTrack.clientWidth) return;
    const index = Math.max(0, Math.min(dots.length - 1, Math.round(swipeTrack.scrollLeft / swipeTrack.clientWidth)));
    dots.forEach((dot, dotIndex) => {
      const isActive = dotIndex === index;
      dot.classList.toggle("is-active", isActive);
      dot.setAttribute("aria-current", isActive ? "true" : "false");
    });
  };
  swipeTrack.addEventListener("scroll", markActiveDot, { passive: true });
  dots.forEach((dot) => {
    dot.addEventListener("click", () => {
      pages[Number(dot.dataset.swipeDot)]?.scrollIntoView({ behavior: "smooth", inline: "start", block: "nearest" });
    });
  });
  markActiveDot();
}

const aiDialog = document.querySelector("[data-ai-dialog]");
if (aiDialog) {
  const openButton = document.querySelector("[data-ai-open]");
  const closeButton = aiDialog.querySelector("[data-ai-close]");
  const messages = aiDialog.querySelector("[data-ai-messages]");
  const status = aiDialog.querySelector("[data-ai-status]");
  const form = aiDialog.querySelector("[data-ai-form]");
  const input = form.querySelector('[name="message"]');
  const submitButton = form.querySelector("[data-ai-submit]");
  const historyKey = `spendwise-ai-${aiDialog.dataset.userId}-${aiDialog.dataset.csrfToken}`;
  let history = [];

  const renderMessage = (role, content) => {
    const message = document.createElement("article");
    message.className = `ai-message ai-message-${role}`;
    message.setAttribute("aria-label", role === "user" ? "Your message" : "SpendWise AI response");
    const text = document.createElement("p");
    text.textContent = content;
    message.append(text);
    messages.append(message);
  };

  try {
    const savedHistory = sessionStorage.getItem(historyKey);
    const parsedHistory = savedHistory ? JSON.parse(savedHistory) : [];
    if (
      Array.isArray(parsedHistory)
      && parsedHistory.every((item) => (
        item
        && (item.role === "user" || item.role === "assistant")
        && typeof item.content === "string"
      ))
    ) {
      history = parsedHistory;
      history.forEach((item) => renderMessage(item.role, item.content));
      messages.scrollTop = messages.scrollHeight;
    }
  } catch (error) {
    status.textContent = "Your previous chat history could not be loaded.";
  }

  openButton.addEventListener("click", () => {
    aiDialog.showModal();
    input.focus();
  });
  closeButton.addEventListener("click", () => aiDialog.close());
  aiDialog.addEventListener("click", (event) => {
    if (event.target === aiDialog) aiDialog.close();
  });
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const message = input.value.trim();
    if (!message || submitButton.disabled) return;

    history.push({ role: "user", content: message });
    renderMessage("user", message);
    input.value = "";
    status.textContent = "SpendWise AI is preparing your answer…";
    submitButton.disabled = true;
    input.disabled = true;
    try {
      const response = await fetch(aiDialog.dataset.apiUrl, {
        method: "POST",
        credentials: "same-origin",
        headers: {
          "Content-Type": "application/json",
          "X-CSRF-Token": aiDialog.dataset.csrfToken,
        },
        body: JSON.stringify({ message }),
      });
      const result = await response.json();
      if (!response.ok) throw new Error(result.error || "SpendWise AI could not respond.");

      history.push({ role: "assistant", content: result.response });
      renderMessage("assistant", result.response);
      status.textContent = "";
      try {
        sessionStorage.setItem(historyKey, JSON.stringify(history));
      } catch (error) {
        status.textContent = "This conversation will not be saved for this browser session.";
      }
      messages.scrollTop = messages.scrollHeight;
    } catch (error) {
      status.textContent = error instanceof Error
        ? error.message
        : "SpendWise AI could not respond right now. Please try again.";
    } finally {
      submitButton.disabled = false;
      input.disabled = false;
      input.focus();
    }
  });
  document.querySelectorAll('form[action="/logout"]').forEach((logoutForm) => {
    logoutForm.addEventListener("submit", () => {
      try {
        sessionStorage.removeItem(historyKey);
      } catch (error) {
        status.textContent = "Chat history could not be cleared from this browser session.";
      }
    });
  });
}
