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
  displayRecipes(recipes);

  // Display batch prep steps
  if (batch_prep && batch_prep.length > 0) {
    displayBatchPrep(batch_prep);
  }

  // Display shopping list
  if (shopping_list && shopping_list.length > 0) {
    displayShoppingList(shopping_list);
  }
}

function displayPlanInfo(plan) {
  const startDate = new Date(plan.start_date).toLocaleDateString();
  const endDate = new Date(plan.end_date).toLocaleDateString();

  document.getElementById("planInfo").innerHTML = `
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
    `;
}

function displayRecipes(recipes) {
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

    const dayName = getDayName(parseInt(dayNum));

    dayCard.innerHTML = `
        <div class="day-header">
        <h3 class="day-title">Day ${dayNum} - ${dayName}</h3>
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
  const mealCard = document.createElement("div");
  mealCard.className = "meal-card";

  const ingredientsList = recipe.ingredients
    .map(
      (ing) =>
        `<li class="ingredient-item">${ing.quantity} ${ing.unit} ${ing.name}${
          ing.notes ? " (" + ing.notes + ")" : ""
        }</li>`
    )
    .join("");

  mealCard.innerHTML = `
    <div class="meal-header">
        <div>
        <div class="meal-type">${mealType}</div>
        <h4 class="meal-name">${recipe.name}</h4>
        </div>
    </div>
    
    <div class="meal-meta">
        <span><i class="fas fa-clock"></i> ${
          recipe.prep_time + recipe.cook_time
        } min</span>
        <span><i class="fas fa-users"></i> ${recipe.servings} servings</span>
        <span><i class="fas fa-dollar-sign"></i> $${
          recipe.estimated_cost || "0.00"
        }</span>
        <span><i class="fas fa-signal"></i> ${recipe.difficulty}</span>
    </div>
    
    ${
      recipe.description
        ? `<p class="meal-description">${recipe.description}</p>`
        : ""
    }
    
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
    
    ${
      recipe.notes
        ? `<div style="margin-top: 1rem; font-style: italic; color: var(--text-muted); font-size: 0.875rem;"><i class="fas fa-lightbulb"></i> ${recipe.notes}</div>`
        : ""
    }
    `;

  return mealCard;
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

function getDayName(dayNum) {
  const today = new Date();
  const targetDate = new Date(today);
  targetDate.setDate(today.getDate() + dayNum - 1);
  return targetDate.toLocaleDateString("en-US", { weekday: "long" });
}
