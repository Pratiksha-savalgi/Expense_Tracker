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

const expenseForm = document.querySelector("[data-expense-form]");
if (expenseForm) {
  const categorySelect = expenseForm.querySelector("#category");
  const subcategorySelect = expenseForm.querySelector("#subcategory_id");
  const newCategoryField = expenseForm.querySelector("#new-category-field");
  const newCategoryInput = expenseForm.querySelector("#new_category");
  const newSubcategoryField = expenseForm.querySelector("#new-subcategory-field");
  const newSubcategoryInput = expenseForm.querySelector("#new_subcategory");
  const saveSubcategoryButton = expenseForm.querySelector("[data-save-subcategory]");
  const subcategorySaveStatus = expenseForm.querySelector("[data-subcategory-save-status]");
  const csrfInput = expenseForm.querySelector('[name="csrf_token"]');
  const amountInput = expenseForm.querySelector("#amount");

  const updateNewCategoryField = () => {
    const addingCategory = categorySelect.value === "__new__";
    newCategoryField.hidden = !addingCategory;
    newCategoryInput.required = addingCategory;
    if (!addingCategory) newCategoryInput.value = "";
  };

  const updateNewSubcategoryField = () => {
    const addingSubcategory = subcategorySelect.value === "__new__";
    newSubcategoryField.hidden = !addingSubcategory;
    newSubcategoryInput.required = addingSubcategory;
    saveSubcategoryButton.hidden = !addingSubcategory || !categorySelect.value || categorySelect.value === "__new__";
    if (!addingSubcategory) newSubcategoryInput.value = "";
  };

  const populateSubcategories = (preserveSelection) => {
    const previousValue = preserveSelection ? subcategorySelect.value : "";
    const categoryOption = categorySelect.selectedOptions[0];
    let subcategories = [];
    if (categoryOption && categoryOption.dataset.subcategories) {
      try {
        subcategories = JSON.parse(categoryOption.dataset.subcategories);
      } catch {
        subcategories = [];
      }
    }

    subcategorySelect.replaceChildren(new Option("No subcategory", ""));
    for (const subcategory of subcategories) {
      subcategorySelect.add(new Option(subcategory.name, String(subcategory.id)));
    }
    subcategorySelect.add(new Option("+ Add subcategory...", "__new__"));
    if ([...subcategorySelect.options].some((option) => option.value === previousValue)) {
      subcategorySelect.value = previousValue;
    }
    updateNewSubcategoryField();
  };

  categorySelect.addEventListener("change", () => {
    updateNewCategoryField();
    populateSubcategories(false);
    subcategorySaveStatus.textContent = "";
  });
  subcategorySelect.addEventListener("change", updateNewSubcategoryField);
  saveSubcategoryButton.addEventListener("click", async () => {
    const subcategoryName = newSubcategoryInput.value.trim().replace(/\s+/g, " ");
    if (!subcategoryName) {
      newSubcategoryInput.setCustomValidity("Enter a subcategory name.");
      newSubcategoryInput.reportValidity();
      return;
    }

    newSubcategoryInput.setCustomValidity("");
    saveSubcategoryButton.disabled = true;
    subcategorySaveStatus.textContent = "Saving subcategory...";
    const endpoint = expenseForm.dataset.subcategoryUrl.replace(
      "/0/subcategories",
      `/${categorySelect.value}/subcategories`,
    );

    try {
      const response = await fetch(endpoint, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRF-Token": csrfInput.value,
        },
        body: JSON.stringify({ name: subcategoryName }),
      });
      const result = await response.json();
      if (!response.ok) {
        subcategorySaveStatus.textContent = result.error || "Could not save the subcategory.";
        return;
      }

      const existingOption = [...subcategorySelect.options].find(
        (option) => option.value === String(result.id),
      );
      if (!existingOption) {
        subcategorySelect.add(new Option(result.name, String(result.id)), subcategorySelect.lastElementChild);
      }
      subcategorySelect.value = String(result.id);
      newSubcategoryInput.value = "";
      updateNewSubcategoryField();
      subcategorySaveStatus.textContent = `${result.name} added to this category.`;
    } catch {
      subcategorySaveStatus.textContent = "Could not save the subcategory. Please try again.";
    } finally {
      saveSubcategoryButton.disabled = false;
    }
  });
  updateNewCategoryField();
  populateSubcategories(true);

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
}