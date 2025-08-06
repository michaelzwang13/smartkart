// Get configuration from global object set by template
const config = window.MEAL_PLAN_DETAILS_CONFIG || {};
const planId = config.planId || 0;

// Initialize dropdown functionality
function initializeDropdowns() {
  // Get all dropdown toggles
  const dropdownToggles = document.querySelectorAll(".dropdown-toggle");

  dropdownToggles.forEach((toggle) => {
    // Handle mobile click behavior
    if (window.innerWidth <= 768) {
      toggle.addEventListener("click", function (e) {
        e.preventDefault();
        const dropdown = this.closest(".nav-dropdown");
        const menu = dropdown.querySelector(".dropdown-menu");

        // Close other dropdowns
        document.querySelectorAll(".nav-dropdown").forEach((otherDropdown) => {
          if (otherDropdown !== dropdown) {
            otherDropdown.classList.remove("active");
          }
        });

        // Toggle current dropdown
        dropdown.classList.toggle("active");
      });
    }
  });

  // Close dropdowns when clicking outside
  document.addEventListener("click", function (e) {
    if (!e.target.closest(".nav-dropdown")) {
      document.querySelectorAll(".nav-dropdown").forEach((dropdown) => {
        dropdown.classList.remove("active");
      });
    }
  });
}

// Handle window resize for dropdown behavior
function handleDropdownResize() {
  window.addEventListener("resize", function () {
    // Remove active class when switching to desktop
    if (window.innerWidth > 768) {
      document.querySelectorAll(".nav-dropdown").forEach((dropdown) => {
        dropdown.classList.remove("active");
      });
    }
  });
}

document.addEventListener("DOMContentLoaded", function () {
  initializeDropdowns();
  handleDropdownResize();
  loadMealPlanDetails();
});

async function loadMealPlanDetails() {
  try {
    const response = await fetch(`/api/meal-plans/${planId}`);
    const data = await response.json();

    if (data.success) {
      displayMealPlan(data.meal_plan);
      document.getElementById("loadingState").style.display = "none";
      document.getElementById("planContent").style.display = "block";
    } else {
      throw new Error(data.message || "Failed to load meal plan");
    }
  } catch (error) {
    console.error("Error loading meal plan:", error);
    document.getElementById("loadingState").innerHTML = `
        <div style="text-align: center; color: var(--error-color);">
        <i class="fas fa-exclamation-triangle" style="font-size: 2rem; margin-bottom: 1rem;"></i>
        <p>Error loading meal plan details</p>
        <p style="font-size: 0.875rem; margin-top: 0.5rem;">${error.message}</p>
        </div>
    `;
  }
}

function displayMealPlan(mealPlan) {
  const { plan_info, recipes, batch_prep, shopping_list } = mealPlan;

  // Update page title
  document.getElementById("planTitle").textContent = plan_info.plan_name;

  // Display plan info
  displayPlanInfo(plan_info);

  // Display recipes by day
  displayRecipes(recipes, plan_info.start_date);

  // Display batch prep steps
  if (batch_prep && batch_prep.length > 0) {
    displayBatchPrep(batch_prep);
  }

  // Display shopping list
  if (shopping_list && shopping_list.length > 0) {
    displayShoppingList(shopping_list);
  }
}

function formatDateString(dateString) {
  // Parse YYYY-MM-DD format manually
  const [year, month, day] = dateString.split('-');
  const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  return `${months[parseInt(month) - 1]} ${parseInt(day)}`;
}

function displayPlanInfo(plan) {
  // Format dates manually from YYYY-MM-DD string
  const startDate = formatDateString(plan.start_date);
  const endDate = formatDateString(plan.end_date);

  document.getElementById("planInfo").innerHTML = `
    <div class="plan-header-content">
        <div class="plan-meta">
            <div class="meta-item">
            <i class="fas fa-calendar-alt meta-icon"></i>
            <span>${startDate} - ${endDate}</span>
            </div>
            <div class="meta-item">
            <i class="fas fa-clock meta-icon"></i>
            <span>${plan.total_days} days</span>
            </div>
            <div class="meta-item">
            <i class="fas fa-leaf meta-icon"></i>
            <span>${plan.dietary_preference || "No restrictions"}</span>
            </div>
            <div class="meta-item">
            <i class="fas fa-dollar-sign meta-icon"></i>
            <span>${
              plan.budget_limit ? "$" + plan.budget_limit : "No budget limit"
            }</span>
            </div>
            <div class="meta-item">
            <i class="fas fa-fire meta-icon"></i>
            <span>Max ${plan.max_cooking_time} min/day</span>
            </div>
            <div class="meta-item">
            <i class="fas fa-robot meta-icon"></i>
            <span>Generated with ${plan.ai_model_used || "AI"}</span>
            </div>
        </div>
        <div class="plan-actions">
            <button class="btn btn-danger" id="deletePlanBtn" onclick="showDeleteConfirmation()">
                <i class="fas fa-trash"></i> Delete Meal Plan
            </button>
        </div>
    </div>
    `;
}

function displayRecipes(recipes, startDate) {
  const daysGrid = document.getElementById("daysGrid");
  daysGrid.innerHTML = "";

  // Sort days
  const sortedDays = Object.keys(recipes).sort(
    (a, b) => parseInt(a) - parseInt(b)
  );

  sortedDays.forEach((dayNum) => {
    const dayRecipes = recipes[dayNum];
    const dayCard = document.createElement("div");
    dayCard.className = "day-card";

    const { dayName, dateString } = getDayNameAndDate(parseInt(dayNum), startDate);

    dayCard.innerHTML = `
        <div class="day-header">
        <h3 class="day-title">Day ${dayNum} - ${dayName}, ${dateString}</h3>
        </div>
        <div class="meals-grid" id="day${dayNum}Meals">
        </div>
    `;

    daysGrid.appendChild(dayCard);

    // Add meals for this day
    const mealsGrid = document.getElementById(`day${dayNum}Meals`);
    const mealTypes = ["breakfast", "lunch", "dinner"];

    mealTypes.forEach((mealType) => {
      if (dayRecipes[mealType]) {
        const mealCard = createMealCard(mealType, dayRecipes[mealType]);
        mealsGrid.appendChild(mealCard);
      }
    });
  });
}

function createMealCard(mealType, recipe) {
  const mealRow = document.createElement("div");
  mealRow.className = "meal-row";
  mealRow.setAttribute("data-meal-type", mealType);

  const ingredientsList = recipe.ingredients
    .map(
      (ing) =>
        `<li class="ingredient-item">${ing.quantity} ${ing.unit} ${ing.name}${
          ing.notes ? " (" + ing.notes + ")" : ""
        }</li>`
    )
    .join("");

  const totalTime = (recipe.prep_time || 0) + (recipe.cook_time || 0);

  mealRow.innerHTML = `
    <div class="meal-row-header" onclick="toggleMealDetails(this)">
        <div class="meal-type-badge ${mealType}">
            <i class="fas fa-${getMealIcon(mealType)}"></i>
            ${mealType.charAt(0).toUpperCase() + mealType.slice(1)}
        </div>
        <div class="meal-row-content">
            <div class="meal-name">${recipe.name}</div>
            <div class="meal-meta">
                <span><i class="fas fa-clock"></i> ${totalTime} min total</span>
                <span><i class="fas fa-users"></i> ${recipe.servings} servings</span>
                <span><i class="fas fa-dollar-sign"></i> $${recipe.estimated_cost || "0.00"}</span>
                <span><i class="fas fa-signal"></i> ${recipe.difficulty}</span>
            </div>
        </div>
        <div class="meal-toggle">
            <i class="fas fa-chevron-down"></i>
        </div>
    </div>
    
    <div class="meal-details">
        ${
          recipe.description
            ? `<p class="meal-description">${recipe.description}</p>`
            : ""
        }
        
        <div class="details-grid">
            <div class="ingredients-section">
                <div class="section-label">
                    <i class="fas fa-list-ul"></i>
                    Ingredients
                </div>
                <ul class="ingredients-list">
                    ${ingredientsList}
                </ul>
            </div>
            
            <div class="instructions-section">
                <div class="section-label">
                    <i class="fas fa-clipboard-list"></i>
                    Instructions
                </div>
                <div class="instructions">${recipe.instructions}</div>
            </div>
        </div>
        
        ${
          recipe.notes
            ? `<div class="meal-notes">
                <i class="fas fa-lightbulb"></i> ${recipe.notes}
               </div>`
            : ""
        }
    </div>
    `;

  return mealRow;
}

function displayBatchPrep(prepSteps) {
  document.getElementById("batchPrep").style.display = "block";
  const stepsContainer = document.getElementById("prepSteps");
  stepsContainer.innerHTML = "";

  prepSteps.forEach((step) => {
    const stepCard = document.createElement("div");
    stepCard.className = "prep-step";

    stepCard.innerHTML = `
        <div class="step-header">
        <h4 class="step-name">${step.prep_session_name}</h4>
        <span class="step-time">${step.estimated_time} min</span>
        </div>
        <p class="step-description">${step.description}</p>
        ${
          step.equipment_needed
            ? `<p><strong>Equipment:</strong> ${step.equipment_needed}</p>`
            : ""
        }
        ${
          step.tips
            ? `<p class="step-tips"><i class="fas fa-lightbulb"></i> ${step.tips}</p>`
            : ""
        }
    `;

    stepsContainer.appendChild(stepCard);
  });
}

function displayShoppingList(items) {
  document.getElementById("shoppingList").style.display = "block";
  const categoriesContainer = document.getElementById("shoppingCategories");
  categoriesContainer.innerHTML = "";

  // Group items by category
  const categories = {};
  items.forEach((item) => {
    const category = item.category || "Other";
    if (!categories[category]) {
      categories[category] = [];
    }
    categories[category].push(item);
  });

  // Create category cards
  Object.keys(categories).forEach((categoryName) => {
    const categoryCard = document.createElement("div");
    categoryCard.className = "category-card";

    const itemsList = categories[categoryName]
      .map(
        (item) =>
          `<li class="shopping-item">
        <span>${item.total_quantity} ${item.unit} ${item.ingredient_name}</span>
        <span class="item-cost">$${item.estimated_cost || "0.00"}</span>
        </li>`
      )
      .join("");

    categoryCard.innerHTML = `
        <h4 class="category-name">${categoryName}</h4>
        <ul class="shopping-items">
        ${itemsList}
        </ul>
    `;

    categoriesContainer.appendChild(categoryCard);
  });
}

function getMealIcon(mealType) {
  switch (mealType) {
    case 'breakfast': return 'sun';
    case 'lunch': return 'leaf';
    case 'dinner': return 'moon';
    default: return 'utensils';
  }
}

function toggleMealDetails(header) {
  const mealRow = header.closest('.meal-row');
  mealRow.classList.toggle('expanded');
}

function getDayNameAndDate(dayNum, startDate) {
  // Parse start date manually: YYYY-MM-DD
  const [year, month, day] = startDate.split('-').map(num => parseInt(num));
  
  // Calculate target date by adding days
  const startDateObj = new Date(year, month - 1, day);
  const targetDate = new Date(startDateObj);
  targetDate.setDate(startDateObj.getDate() + dayNum - 1);
  
  // Get day name manually
  const dayNames = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
  const dayName = dayNames[targetDate.getDay()];
  
  // Format date manually
  const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  const dateString = `${months[targetDate.getMonth()]} ${targetDate.getDate()}, ${targetDate.getFullYear()}`;
  
  return { dayName, dateString };
}

function showDeleteConfirmation() {
  const modalHTML = `
    <div id="deleteConfirmationModal" class="modal-overlay">
        <div class="modal-content delete-confirmation-modal">
        <div class="modal-header">
            <div class="delete-warning-icon">
                <i class="fas fa-exclamation-triangle"></i>
            </div>
            <h3>Delete Meal Plan</h3>
        </div>
        <div class="modal-body">
            <p class="delete-warning-text">
                Are you sure you want to delete this meal plan? This action cannot be undone.
            </p>
            <p class="delete-consequences">
                <strong>This will permanently remove:</strong>
            </p>
            <ul class="delete-consequences-list">
                <li>All meals in this plan</li>
                <li>Recipe details and instructions</li>
                <li>Shopping lists and prep steps</li>
                <li>Progress tracking data</li>
            </ul>
        </div>
        <div class="modal-actions">
            <button class="btn btn-secondary" onclick="closeDeleteConfirmation()">
                <i class="fas fa-times"></i> Cancel
            </button>
            <button class="btn btn-danger" onclick="deleteMealPlan()" id="confirmDeleteBtn">
                <i class="fas fa-trash"></i> Delete Permanently
            </button>
        </div>
        </div>
    </div>
    `;

  document.body.insertAdjacentHTML("beforeend", modalHTML);

  // Show modal with animation
  setTimeout(() => {
    document.getElementById("deleteConfirmationModal").classList.add("show");
  }, 10);

  // Close modal when clicking outside
  const modal = document.getElementById("deleteConfirmationModal");
  modal.addEventListener("click", (e) => {
    if (e.target === modal) {
      closeDeleteConfirmation();
    }
  });

  // Close modal with Escape key
  document.addEventListener("keydown", handleDeleteEscape);
}

function handleDeleteEscape(e) {
  if (e.key === "Escape") {
    const modal = document.getElementById("deleteConfirmationModal");
    if (modal) {
      closeDeleteConfirmation();
      document.removeEventListener("keydown", handleDeleteEscape);
    }
  }
}

function closeDeleteConfirmation() {
  const modal = document.getElementById("deleteConfirmationModal");
  if (modal) {
    modal.classList.remove("show");
    document.removeEventListener("keydown", handleDeleteEscape);
    setTimeout(() => {
      modal.remove();
    }, 300);
  }
}

async function deleteMealPlan() {
  const confirmBtn = document.getElementById("confirmDeleteBtn");

  // Show loading state
  const originalContent = confirmBtn.innerHTML;
  confirmBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Deleting...';
  confirmBtn.disabled = true;

  try {
    const response = await fetch(`/api/meal-plans/${planId}`, {
      method: "DELETE",
      headers: {
        "Content-Type": "application/json",
      },
    });

    const data = await response.json();

    if (data.success) {
      // Show success message briefly
      confirmBtn.innerHTML = '<i class="fas fa-check"></i> Deleted!';
      confirmBtn.style.background = "var(--success-gradient)";

      // Close modal and redirect after short delay
      setTimeout(() => {
        closeDeleteConfirmation();
        // Redirect to meal plans page
        window.location.href = config.urls?.meal_plans || "/meal-plans";
      }, 1500);
    } else {
      throw new Error(data.message || "Failed to delete meal plan");
    }
  } catch (error) {
    console.error("Error deleting meal plan:", error);

    // Show error state
    confirmBtn.innerHTML = '<i class="fas fa-exclamation-triangle"></i> Error';
    confirmBtn.style.background = "var(--error-gradient)";

    // Reset button after delay
    setTimeout(() => {
      confirmBtn.innerHTML = originalContent;
      confirmBtn.style.background = "var(--error-gradient)";
      confirmBtn.disabled = false;
    }, 2000);

    alert("Failed to delete meal plan: " + error.message);
  }
}
