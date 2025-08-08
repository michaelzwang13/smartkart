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
      await displayMealPlan(data.meal_plan);
      document.getElementById("loadingState").style.display = "none";
      document.getElementById("planContent").style.display = "block";
      
      // Check for pantry change notifications after loading
      await checkPantryChangeNotifications();
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

async function displayMealPlan(mealPlan) {
  const { plan_info, recipes, batch_prep, shopping_list, fuzzy_matching } = mealPlan;

  // Update page title
  document.getElementById("planTitle").textContent = plan_info.plan_name;

  // Display plan info with fuzzy matching summary
  displayPlanInfo(plan_info, fuzzy_matching?.summary);

  // Display recipes by day
  await displayRecipes(recipes, plan_info.start_date);

  // Display batch prep steps
  if (batch_prep && batch_prep.length > 0) {
    displayBatchPrep(batch_prep);
  }

  // Display shopping list with fuzzy matching data
  if (shopping_list && shopping_list.length > 0) {
    displayShoppingList(shopping_list, fuzzy_matching?.ingredient_matches, plan_info);
  }
  
  // Store fuzzy matching data globally for confirmation functions
  window.fuzzyMatchingData = fuzzy_matching;
}

function formatDateString(dateString) {
  // Parse YYYY-MM-DD format manually
  const [year, month, day] = dateString.split('-');
  const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  return `${months[parseInt(month) - 1]} ${parseInt(day)}`;
}

function formatFullExpirationDate(dateString, planInfo = {}) {
  if (!dateString) {
    return { text: 'No expiration date', cssClass: '' };
  }
  
  // Parse dates
  const expirationDate = new Date(dateString + 'T00:00:00');
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  
  const planStartDate = planInfo.start_date ? new Date(planInfo.start_date + 'T00:00:00') : null;
  const planEndDate = planInfo.end_date ? new Date(planInfo.end_date + 'T00:00:00') : null;
  
  // Format full date
  const options = { year: 'numeric', month: 'short', day: 'numeric' };
  const formattedDate = expirationDate.toLocaleDateString('en-US', options);
  
  // Determine text and color coding
  let fullDateText, cssClass = '';
  
  if (expirationDate < today) {
    // Already expired - red
    fullDateText = `Expired: ${formattedDate}`;
    cssClass = 'expired';
  } else if (planStartDate && planEndDate && 
             expirationDate >= planStartDate && expirationDate <= planEndDate) {
    // Expires during meal plan session - yellow warning
    fullDateText = `Expires: ${formattedDate}`;
    cssClass = 'expires-during-plan';
  } else {
    // Expires after plan or no plan dates - no special styling (default)
    fullDateText = `Expires: ${formattedDate}`;
  }
  
  return { text: fullDateText, cssClass };
}

function convertToMixedFraction(decimal) {
  if (!decimal || decimal === 0) return '0';
  
  const num = parseFloat(decimal);
  const wholeNumber = Math.floor(num);
  const fractionalPart = num - wholeNumber;
  
  // If no fractional part, return whole number
  if (fractionalPart === 0) {
    return wholeNumber.toString();
  }
  
  // Round to nearest common fraction
  let fraction = '';
  const tolerance = 0.04; // Tolerance for rounding
  
  // Check for halves
  if (Math.abs(fractionalPart - 0.5) < tolerance) {
    fraction = '1/2';
  }
  // Check for quarters
  else if (Math.abs(fractionalPart - 0.25) < tolerance) {
    fraction = '1/4';
  }
  else if (Math.abs(fractionalPart - 0.75) < tolerance) {
    fraction = '3/4';
  }
  // Check for thirds
  else if (Math.abs(fractionalPart - 0.333) < tolerance || Math.abs(fractionalPart - 0.33) < tolerance) {
    fraction = '1/3';
  }
  else if (Math.abs(fractionalPart - 0.667) < tolerance || Math.abs(fractionalPart - 0.66) < tolerance) {
    fraction = '2/3';
  }
  // If doesn't match common fractions, round to nearest quarter
  else {
    const rounded = Math.round(fractionalPart * 4) / 4;
    if (rounded === 0.25) fraction = '1/4';
    else if (rounded === 0.5) fraction = '1/2';
    else if (rounded === 0.75) fraction = '3/4';
    else if (rounded === 0) return wholeNumber.toString();
    else if (rounded === 1) return (wholeNumber + 1).toString();
  }
  
  // Return formatted result
  if (wholeNumber === 0) {
    return fraction; // Pure fractions stay normal size
  } else {
    return `${wholeNumber}&nbsp;<span class="mixed-fraction">${fraction}</span>`;
  }
}

function displayPlanInfo(plan, fuzzyMatchingSummary) {
  // Format dates manually from YYYY-MM-DD string
  const startDate = formatDateString(plan.start_date);
  const endDate = formatDateString(plan.end_date);
  
  // Handle single day vs multi-day display
  const dateDisplay = plan.total_days === 1 ? startDate : `${startDate} - ${endDate}`;
  const daysDisplay = plan.total_days === 1 ? '1 day' : `${plan.total_days} days`;

  let fuzzyMatchingHtml = '';
  if (fuzzyMatchingSummary) {
    const utilizationRate = fuzzyMatchingSummary.pantry_utilization_rate || 0;
    const utilizationColor = utilizationRate >= 70 ? 'success' : utilizationRate >= 50 ? 'warning' : 'error';
    
    // Check if data might be outdated (simple heuristic based on generated time)
    const generatedAt = new Date(fuzzyMatchingSummary.generated_at);
    const now = new Date();
    const hoursSinceGenerated = (now - generatedAt) / (1000 * 60 * 60);
    const isStale = hoursSinceGenerated > 24; // Consider stale after 24 hours
    
    let staleWarning = '';
    if (isStale) {
      staleWarning = `
        <div class="stale-warning">
          <i class="fas fa-exclamation-triangle"></i>
          <span>Pantry analysis is ${Math.floor(hoursSinceGenerated)} hours old. Consider refreshing for accurate results.</span>
          <button class="btn-link refresh-suggestion" onclick="refreshPantryMatches()">Refresh now</button>
        </div>
      `;
    }
    
    fuzzyMatchingHtml = `
      <div class="fuzzy-matching-summary">
        <div class="summary-header">
          <i class="fas fa-brain meta-icon"></i>
          <span>Smart Pantry Analysis</span>
        </div>
        ${staleWarning}
        <div class="summary-stats">
          <div class="stat-item success">
            <i class="fas fa-check"></i>
            <span>${fuzzyMatchingSummary.auto_matched} auto-matched</span>
          </div>
          <div class="stat-item warning">
            <i class="fas fa-question"></i>
            <span>${fuzzyMatchingSummary.confirm_needed} need confirmation</span>
          </div>
          <div class="stat-item error">
            <i class="fas fa-exclamation"></i>
            <span>${fuzzyMatchingSummary.missing} missing</span>
          </div>
        </div>
        <div class="utilization-rate">
          <span class="rate-label">Pantry utilization:</span>
          <span class="rate-value ${utilizationColor}">${utilizationRate.toFixed(1)}%</span>
        </div>
      </div>
    `;
  }

  document.getElementById("planInfo").innerHTML = `
    <div class="plan-meta">
        <div class="meta-item">
        <i class="fas fa-calendar-alt meta-icon"></i>
        <span>${dateDisplay}</span>
        </div>
        <div class="meta-item">
        <i class="fas fa-clock meta-icon"></i>
        <span>${daysDisplay}</span>
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
    </div>
    ${fuzzyMatchingHtml}
    `;
}

async function displayRecipes(recipes, startDate) {
  const daysGrid = document.getElementById("daysGrid");
  daysGrid.innerHTML = "";

  // Get timezone-aware today for comparison
  let serverToday = window.serverToday;
  if (!serverToday) {
    try {
      const response = await fetch('/api/meals/today');
      const data = await response.json();
      if (data.success && data.date) {
        serverToday = data.date;
        window.serverToday = serverToday; // Cache it
      } else {
        serverToday = new Date().toISOString().split("T")[0]; // Fallback
      }
    } catch (error) {
      serverToday = new Date().toISOString().split("T")[0]; // Fallback
    }
  }

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
        <div class="day-header-content">
            <h3 class="day-title">Day ${dayNum} - ${dayName}, ${dateString}</h3>
            <button class="day-toggle-btn" onclick="toggleDayMeals(${dayNum})" title="Hide/Show meals for this day">
                <i class="fas fa-eye" id="dayToggleIcon${dayNum}"></i>
            </button>
        </div>
        </div>
        <div class="meals-grid" id="day${dayNum}Meals">
        </div>
    `;

    daysGrid.appendChild(dayCard);

    // Check if this day is in the past and hide it by default
    const dayDate = new Date(startDate);
    dayDate.setDate(dayDate.getDate() + parseInt(dayNum) - 1);
    const dayDateStr = dayDate.toISOString().split("T")[0];
    
    if (dayDateStr < serverToday) {
      // This day is in the past, hide it by default
      toggleDayMeals(parseInt(dayNum));
    }

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
  mealRow.className = `meal-row ${mealType}`;
  mealRow.setAttribute("data-meal-type", mealType);

  const ingredientsList = recipe.ingredients
    .map(
      (ing) =>
        `<li class="ingredient-item">${convertToMixedFraction(ing.quantity)} ${ing.unit === 'pcs' || ing.unit === 'pc' ? '' : ing.unit} ${ing.name}${
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
                <span><i class="fas fa-dollar-sign"></i> ${recipe.estimated_cost || "0.00"}</span>
                <span><i class="fas fa-signal"></i> ${recipe.difficulty}</span>
            </div>
        </div>
        <div class="meal-toggle">
            <i class="fas fa-chevron-down"></i>
        </div>
    </div>
    
    <div class="meal-details">
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

function displayShoppingList(items, fuzzyMatches = {}, planInfo = {}) {
  document.getElementById("shoppingList").style.display = "block";
  const categoriesContainer = document.getElementById("shoppingCategories");
  categoriesContainer.innerHTML = "";

  // Store data globally for re-sorting
  window.currentShoppingData = { items, fuzzyMatches, planInfo };
  
  // Load user preference for missing items priority
  const prioritizeMissing = localStorage.getItem('prioritizeMissingIngredients') === 'true';
  const toggle = document.getElementById('prioritizeMissingToggle');
  if (toggle) {
    toggle.checked = prioritizeMissing;
  }

  // Group items by category, with special handling for missing items
  const categories = {};
  const missingItems = [];
  
  items.forEach((item) => {
    const matchData = fuzzyMatches[item.ingredient_name];
    const isMissing = isMissingItem(matchData);
    
    if (prioritizeMissing && isMissing) {
      // Put missing items in their own category
      missingItems.push(item);
    } else {
      // Put non-missing items in their regular categories
      const category = item.category || "Other";
      if (!categories[category]) {
        categories[category] = [];
      }
      categories[category].push(item);
    }
  });

  // Create sorted category names
  let sortedCategoryNames = Object.keys(categories).sort();
  
  // If we have missing items, add the Missing category at the top
  if (prioritizeMissing && missingItems.length > 0) {
    categories["Missing Items"] = missingItems;
    sortedCategoryNames = ["Missing Items", ...sortedCategoryNames];
  }

  // Create category cards with fuzzy matching indicators
  sortedCategoryNames.forEach((categoryName) => {
    const categoryCard = document.createElement("div");
    categoryCard.className = "category-card";

    // For the Missing Items category, add special styling
    if (categoryName === "Missing Items") {
      categoryCard.classList.add("missing-category");
    }

    const categoryItems = categories[categoryName];
    const itemsList = categoryItems
      .map((item) => {
        const matchData = fuzzyMatches[item.ingredient_name];
        const matchIndicator = createMatchIndicator(matchData);
        const pantryInfo = createPantryInfo(matchData, planInfo);
        
        return `
          <li class="shopping-item ${matchData ? 'has-match-data' : ''}">
            <div class="item-row">
              <div class="item-main">
                <div class="item-header">
                  ${matchIndicator}
                  <span class="item-details">${convertToMixedFraction(item.total_quantity)} ${item.unit === 'pcs' || item.unit === 'pc' ? '' : item.unit} ${item.ingredient_name}</span>
                  <span class="item-cost">$${item.estimated_cost || "0.00"}</span>
                </div>
                ${matchData && matchData.match_type === 'confirm' ? createConfirmationButtons(item.ingredient_name) : ''}
              </div>
              ${pantryInfo}
            </div>
          </li>
        `;
      })
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

function createMatchIndicator(matchData) {
  if (!matchData) {
    return '<span class="match-indicator no-data" title="No pantry data available"><i class="fas fa-question"></i></span>';
  }
  
  const { match_type, confidence } = matchData;
  
  switch (match_type) {
    case 'auto':
      return `<span class="match-indicator auto-match" title="Automatically matched (${confidence?.toFixed(1)}% confidence)">
                <i class="fas fa-check"></i>
              </span>`;
    case 'confirm':
      return `<span class="match-indicator confirm-match" title="Needs confirmation (${confidence?.toFixed(1)}% confidence)">
                <i class="fas fa-question"></i>
              </span>`;
    case 'missing':
      return '<span class="match-indicator missing" title="Not found in pantry"><i class="fas fa-exclamation"></i></span>';
    default:
      return '<span class="match-indicator unknown" title="Unknown match status"><i class="fas fa-question"></i></span>';
  }
}

function createPantryInfo(matchData, planInfo = {}) {
  if (!matchData || !matchData.pantry_item) {
    return '';
  }
  
  const { pantry_item, needs_to_buy } = matchData;
  const expirationInfo = formatFullExpirationDate(pantry_item.expiration_date, planInfo);
  
  return `
    <div class="pantry-info">
      <div class="pantry-match">
        <i class="fas fa-warehouse"></i>
        <span>Found: ${convertToMixedFraction(pantry_item.available_quantity)} ${pantry_item.available_unit && pantry_item.available_unit !== 'pcs' && pantry_item.available_unit !== 'pc' ? pantry_item.available_unit + ' ' : ''}${pantry_item.name}</span>
        <span class="storage-type">(${pantry_item.storage_type})</span>
      </div>
      <div class="pantry-details">
        <span class="expiration ${expirationInfo.cssClass}">${expirationInfo.text}</span>
        ${needs_to_buy > 0 ? `<span class="still-need">Still need: ${needs_to_buy}</span>` : '<span class="fully-covered">✓ Fully covered</span>'}
      </div>
    </div>
  `;
}

function createConfirmationButtons(ingredientName) {
  return `
    <div class="confirmation-buttons">
      <button class="btn btn-sm btn-success" onclick="confirmMatch('${ingredientName}', true)" title="Confirm this match">
        <i class="fas fa-check"></i> Confirm
      </button>
      <button class="btn btn-sm btn-danger" onclick="confirmMatch('${ingredientName}', false)" title="Reject this match">
        <i class="fas fa-times"></i> Reject
      </button>
    </div>
  `;
}

async function confirmMatch(ingredientName, isConfirmed) {
  if (!window.fuzzyMatchingData?.summary?.generation_id) {
    alert('No fuzzy matching data available');
    return;
  }
  
  const generationId = window.fuzzyMatchingData.summary.generation_id;
  const matchData = window.fuzzyMatchingData.ingredient_matches[ingredientName];
  
  try {
    const response = await fetch('/api/shopping/confirm-match', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        generation_id: generationId,
        ingredient_name: ingredientName,
        pantry_item_id: isConfirmed && matchData?.pantry_item ? matchData.pantry_item.id : null
      })
    });
    
    const result = await response.json();
    
    if (result.success) {
      // Update the UI to reflect the confirmation
      updateMatchConfirmation(ingredientName, isConfirmed);
      
      // Show feedback message
      showNotification(
        isConfirmed ? 'Match confirmed successfully' : 'Match rejected successfully',
        'success'
      );
    } else {
      throw new Error(result.message || 'Failed to confirm match');
    }
  } catch (error) {
    console.error('Error confirming match:', error);
    showNotification('Failed to confirm match: ' + error.message, 'error');
  }
}

function updateMatchConfirmation(ingredientName, isConfirmed) {
  // Find the shopping item element for this ingredient
  const shoppingItems = document.querySelectorAll('.shopping-item');
  
  shoppingItems.forEach(item => {
    const itemDetails = item.querySelector('.item-details');
    if (itemDetails && itemDetails.textContent.includes(ingredientName)) {
      // Update the match indicator
      const matchIndicator = item.querySelector('.match-indicator');
      if (matchIndicator) {
        if (isConfirmed) {
          matchIndicator.className = 'match-indicator auto-match';
          matchIndicator.innerHTML = '<i class="fas fa-check"></i>';
          matchIndicator.title = 'Confirmed by user';
        } else {
          matchIndicator.className = 'match-indicator missing';
          matchIndicator.innerHTML = '<i class="fas fa-exclamation"></i>';
          matchIndicator.title = 'Rejected by user';
        }
      }
      
      // Hide confirmation buttons
      const confirmButtons = item.querySelector('.confirmation-buttons');
      if (confirmButtons) {
        confirmButtons.style.display = 'none';
      }
      
      // Add confirmation badge
      const itemHeader = item.querySelector('.item-header');
      if (itemHeader && !itemHeader.querySelector('.user-confirmed')) {
        const confirmBadge = document.createElement('span');
        confirmBadge.className = 'user-confirmed';
        confirmBadge.innerHTML = '<i class="fas fa-user-check"></i>';
        confirmBadge.title = 'User confirmed';
        itemHeader.appendChild(confirmBadge);
      }
    }
  });
}

function showNotification(message, type = 'info') {
  // Create notification element
  const notification = document.createElement('div');
  notification.className = `notification ${type}`;
  notification.innerHTML = `
    <i class="fas fa-${type === 'success' ? 'check' : type === 'error' ? 'exclamation-triangle' : 'info'}"></i>
    <span>${message}</span>
  `;
  
  // Add to page
  document.body.appendChild(notification);
  
  // Show notification
  setTimeout(() => notification.classList.add('show'), 100);
  
  // Auto-hide after 3 seconds
  setTimeout(() => {
    notification.classList.remove('show');
    setTimeout(() => document.body.removeChild(notification), 300);
  }, 3000);
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

function toggleDayMeals(dayNum) {
  const mealsGrid = document.getElementById(`day${dayNum}Meals`);
  const toggleIcon = document.getElementById(`dayToggleIcon${dayNum}`);
  
  if (mealsGrid.style.display === 'none') {
    // Show meals
    mealsGrid.style.display = 'grid';
    toggleIcon.className = 'fas fa-eye';
    toggleIcon.parentElement.title = 'Hide meals for this day';
  } else {
    // Hide meals
    mealsGrid.style.display = 'none';
    toggleIcon.className = 'fas fa-eye-slash';
    toggleIcon.parentElement.title = 'Show meals for this day';
  }
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

async function refreshPantryMatches() {
  const refreshBtn = document.getElementById("refreshMatchesBtn");
  
  // Show loading state
  const originalContent = refreshBtn.innerHTML;
  refreshBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Refreshing...';
  refreshBtn.disabled = true;
  
  try {
    const response = await fetch(`/api/meal-plans/${planId}/refresh-matches`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
    });
    
    const data = await response.json();
    
    if (data.success) {
      // Show success message briefly
      refreshBtn.innerHTML = '<i class="fas fa-check"></i> Updated!';
      refreshBtn.style.background = "var(--success-color)";
      refreshBtn.style.color = "white";
      
      // Show notification with details
      showNotification(
        `Refreshed ${data.refreshed_count} of ${data.total_ingredients} ingredient matches`,
        'success'
      );
      
      // Reload the meal plan data to show updated matches
      setTimeout(async () => {
        await loadMealPlanDetails();
        
        // Dismiss the notification banner since matches are now refreshed
        const banner = document.getElementById('pantry-change-banner');
        if (banner) {
          banner.style.animation = 'slideUp 0.3s ease';
          setTimeout(() => {
            banner.remove();
          }, 300);
        }
        
        // Reset button
        refreshBtn.innerHTML = originalContent;
        refreshBtn.style.background = "";
        refreshBtn.style.color = "";
        refreshBtn.disabled = false;
      }, 1500);
      
    } else {
      throw new Error(data.message || "Failed to refresh matches");
    }
  } catch (error) {
    console.error("Error refreshing matches:", error);
    
    // Show error state
    refreshBtn.innerHTML = '<i class="fas fa-exclamation-triangle"></i> Error';
    refreshBtn.style.background = "var(--error-color)";
    refreshBtn.style.color = "white";
    
    // Show error notification
    showNotification('Failed to refresh matches: ' + error.message, 'error');
    
    // Reset button after delay
    setTimeout(() => {
      refreshBtn.innerHTML = originalContent;
      refreshBtn.style.background = "";
      refreshBtn.style.color = "";
      refreshBtn.disabled = false;
    }, 2000);
  }
}

async function checkPantryChangeNotifications() {
  if (!window.fuzzyMatchingData?.ingredient_matches) {
    return; // No fuzzy matching data to check
  }
  
  const matchData = window.fuzzyMatchingData.ingredient_matches;
  const recentlyDeleted = [];
  
  // Check for items that have match_type 'auto' but pantry_item is null
  // This indicates the pantry item was deleted after fuzzy matching
  for (const [ingredientName, match] of Object.entries(matchData)) {
    // If match_type is still 'auto' but pantry_item is null,
    // it means the item was matched before but the pantry item was deleted
    if (match.match_type === 'auto' && (!match.pantry_item || match.pantry_item.id === null)) {
      // We need the original pantry item name, but since it's null, we'll use a generic message
      // or we could store the ingredient name as a fallback
      recentlyDeleted.push({
        ingredient_name: ingredientName,
        item_name: ingredientName // Fallback to ingredient name since pantry item data is gone
      });
    }
  }
  
  if (recentlyDeleted.length > 0) {
    displayPantryChangeNotifications(recentlyDeleted);
  }
}

function displayPantryChangeNotifications(notifications) {
  // Create a notification banner
  const existingBanner = document.getElementById('pantry-change-banner');
  if (existingBanner) {
    existingBanner.remove();
  }
  
  const itemNames = notifications.map(n => n.item_name).join(', ');
  const itemCount = notifications.length;
  
  const banner = document.createElement('div');
  banner.id = 'pantry-change-banner';
  banner.className = 'pantry-change-notification';
  banner.innerHTML = `
    <div class="notification-content">
      <i class="fas fa-exclamation-circle"></i>
      <div class="notification-text">
        <strong>Pantry Changes Detected</strong>
        <span>${itemCount} item${itemCount > 1 ? 's' : ''} used in this meal plan ${itemCount > 1 ? 'have' : 'has'} been deleted: ${itemNames}</span>
      </div>
      <div class="notification-actions">
        <button class="btn btn-primary btn-sm" onclick="refreshPantryMatches()">
          <i class="fas fa-sync-alt"></i> Refresh Matches
        </button>
        <button class="btn btn-secondary btn-sm" onclick="dismissPantryNotifications()">
          <i class="fas fa-times"></i> Dismiss
        </button>
      </div>
    </div>
  `;
  
  // Insert banner at the top of the main content
  const mainContent = document.querySelector('.main-content');
  const pageHeader = document.querySelector('.page-header');
  mainContent.insertBefore(banner, pageHeader.nextSibling);
  
  // Store notification data for dismissal (simplified - no need for database IDs)
  banner.dataset.notifications = JSON.stringify(notifications);
}

function dismissPantryNotifications() {
  const banner = document.getElementById('pantry-change-banner');
  if (!banner) return;
  
  // Simple dismissal - just remove the banner with animation
  banner.style.animation = 'slideUp 0.3s ease';
  setTimeout(() => {
    banner.remove();
  }, 300);
}

function toggleMissingPriority() {
  const toggle = document.getElementById('prioritizeMissingToggle');
  const isEnabled = toggle.checked;
  
  // Store preference for next time
  localStorage.setItem('prioritizeMissingIngredients', isEnabled);
  
  // Re-render the shopping list with new sorting
  if (window.currentShoppingData) {
    displayShoppingList(
      window.currentShoppingData.items, 
      window.currentShoppingData.fuzzyMatches, 
      window.currentShoppingData.planInfo
    );
  }
}


function isMissingItem(matchData) {
  if (!matchData) return true;
  
  // Consider items missing if:
  // 1. match_type is 'missing'
  // 2. match_type is 'auto' but pantry_item is null (recently deleted)
  return matchData.match_type === 'missing' || 
         (matchData.match_type === 'auto' && (!matchData.pantry_item || matchData.pantry_item.id === null));
}
