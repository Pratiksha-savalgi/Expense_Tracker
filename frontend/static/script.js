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

const expenseModal = document.querySelector("[data-expense-modal]");
if (expenseModal) {
  const modalForm = expenseModal.querySelector("[data-modal-expense-form]");
  const categorySelect = expenseModal.querySelector("[data-modal-category]");
  const newCategoryField = expenseModal.querySelector("[data-modal-new-category-field]");
  const newCategoryInput = newCategoryField.querySelector("input");
  const modalDatePicker = expenseModal.querySelector("[data-modal-date-picker]");
  const modalDatePeriodButtons = expenseModal.querySelectorAll("[data-modal-date-period]");
  const successMessage = expenseModal.querySelector("[data-expense-save-success]");
  const saveConfirmation = expenseModal.querySelector("[data-confirm-expense-save]");

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
  const setActiveDatePeriod = (period) => {
    modalDatePeriodButtons.forEach((button) => {
      const isActive = button.dataset.modalDatePeriod === period;
      button.classList.toggle("is-active", isActive);
      button.setAttribute("aria-pressed", String(isActive));
    });
    modalDatePicker.closest(".date-picker-option").classList.toggle("is-active", period === "custom");
  };
  const syncActiveDatePeriod = () => {
    const selectedDate = modalDatePicker.value;
    const today = todayIso();
    if (selectedDate === today) {
      setActiveDatePeriod("today");
    } else if (selectedDate === yesterdayIso()) {
      setActiveDatePeriod("yesterday");
    } else {
      const lastSevenDays = new Date();
      lastSevenDays.setDate(lastSevenDays.getDate() - 6);
      setActiveDatePeriod(selectedDate >= toIsoDate(lastSevenDays) && selectedDate <= today ? "last7" : "custom");
    }
  };
  const updateNewCategoryField = () => {
    const addingCategory = categorySelect.value === "__new__";
    newCategoryField.hidden = !addingCategory;
    newCategoryInput.required = addingCategory;
    if (!addingCategory) newCategoryInput.value = "";
  };

  categorySelect.addEventListener("change", updateNewCategoryField);
  modalDatePicker.max = todayIso();
  modalDatePeriodButtons.forEach((button) => {
    button.addEventListener("click", () => {
      const period = button.dataset.modalDatePeriod;
      modalDatePicker.value = period === "yesterday" ? yesterdayIso() : todayIso();
      setActiveDatePeriod(period);
    });
  });
  modalDatePicker.addEventListener("change", () => setActiveDatePeriod("custom"));
  setActiveDatePeriod("today");
  updateNewCategoryField();

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
      updateNewCategoryField();
      syncActiveDatePeriod();
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
<<<<<<< HEAD

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
=======
}

const subcategoryDialog = document.querySelector("#subcategory-dialog");
const subcategoryChart = subcategoryDialog?.querySelector("[data-subcategory-chart]");

const formatChartMoney = (value) => new Intl.NumberFormat("en-IN", {
  style: "currency",
  currency: "INR",
  minimumFractionDigits: 2,
}).format(Number(value));

const buildSubcategoryChart = (categoryName, items) => {
  subcategoryChart.replaceChildren();
  const title = subcategoryDialog.querySelector("#subcategory-dialog-title");
  title.textContent = `${categoryName} subcategories`;

  const total = items.reduce((sum, item) => sum + Number(item.total), 0);
  const chart = document.createElement("div");
  chart.className = "vertical-chart modal-vertical-chart";
  chart.setAttribute("role", "img");
  chart.setAttribute("aria-label", `${categoryName} subcategory spending`);

  for (const item of items) {
    const amount = Number(item.total);
    const share = total > 0 ? amount / total * 100 : 0;
    const column = document.createElement("div");
    column.className = "vertical-chart-column modal-chart-column";

    const value = document.createElement("span");
    value.className = "vertical-chart-value";
    value.textContent = formatChartMoney(amount);

    const track = document.createElement("span");
    track.className = "vertical-chart-track";
    const bar = document.createElement("span");
    bar.className = "vertical-chart-fill vertical-chart-fill-secondary";
    bar.style.setProperty("--bar-height", `${share}%`);
    track.append(bar);

    const label = document.createElement("span");
    label.className = "vertical-chart-label";
    label.textContent = item.subcategory;

    column.append(value, track, label);
    chart.append(column);
  }

  const table = document.createElement("table");
  table.className = "dialog-data-table";
  const caption = document.createElement("caption");
  caption.textContent = `${categoryName} subcategory totals`;
  const head = document.createElement("thead");
  head.innerHTML = "<tr><th scope=\"col\">Subcategory</th><th scope=\"col\">Total</th><th scope=\"col\">Share</th></tr>";
  const body = document.createElement("tbody");
  for (const item of items) {
    const row = document.createElement("tr");
    const name = document.createElement("th");
    name.scope = "row";
    name.textContent = item.subcategory;
    const amount = document.createElement("td");
    amount.textContent = formatChartMoney(item.total);
    const share = document.createElement("td");
    share.textContent = `${total > 0 ? (Number(item.total) / total * 100).toFixed(1) : "0.0"}%`;
    row.append(name, amount, share);
    body.append(row);
  }
  table.append(caption, head, body);
  subcategoryChart.append(chart, table);
};

document.addEventListener("click", (event) => {
  const categoryButton = event.target.closest("[data-subcategories]");
  if (categoryButton && subcategoryDialog && subcategoryChart) {
    let items = [];
    try {
      items = JSON.parse(categoryButton.dataset.subcategories);
    } catch {
      items = [];
    }
    buildSubcategoryChart(categoryButton.dataset.categoryName, items);
    subcategoryDialog.showModal();
    return;
  }

  if (event.target.closest("[data-close-dialog]") && subcategoryDialog?.open) {
    subcategoryDialog.close();
  }
});

subcategoryDialog?.addEventListener("click", (event) => {
  if (event.target === subcategoryDialog) subcategoryDialog.close();
});
>>>>>>> d6b40453c92a130e5b5b7944ca268733689bb73c
