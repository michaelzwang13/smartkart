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

// Calendar functionality
let currentDate = new Date();
let currentView = "month";
let mealPlanData = [];
let mealsData = [];

// Load existing meal plans on page load
// Goals functionality
function initializeGoals() {
  // Set current month
  const currentDate = new Date();
  const monthNames = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
  ];
  document.getElementById("currentMonth").textContent = `${
    monthNames[currentDate.getMonth()]
  } ${currentDate.getFullYear()}`;

  // Load saved goals from localStorage
  loadGoals();

  // Update progress displays
  updateGoalsProgress();

  // Setup event listeners
  setupGoalsEventListeners();
}

async function loadGoals() {
  try {
    const currentMonth = new Date().getMonth() + 1;
    const currentYear = new Date().getFullYear();

    const response = await fetch(
      `/api/meal-goals?month=${currentMonth}&year=${currentYear}`
    );
    const data = await response.json();

    if (data.success) {
      const goals = data.goals;
      document.getElementById("mealPlansGoal").value = goals.meal_plans_goal;
      document.getElementById("mealsCompletedGoal").value =
        goals.meals_completed_goal;
      document.getElementById("newRecipesGoal").value = goals.new_recipes_goal;
    } else {
      console.error("Failed to load goals:", data.message);
      // Set default values on error
      document.getElementById("mealPlansGoal").value = 4;
      document.getElementById("mealsCompletedGoal").value = 60;
      document.getElementById("newRecipesGoal").value = 12;
    }

    updateGoalTargets();
  } catch (error) {
    console.error("Error loading goals:", error);
    // Set default values on error
    document.getElementById("mealPlansGoal").value = 4;
    document.getElementById("mealsCompletedGoal").value = 60;
    document.getElementById("newRecipesGoal").value = 12;
    updateGoalTargets();
  }
}

async function saveGoals() {
  try {
    const currentMonth = new Date().getMonth() + 1;
    const currentYear = new Date().getFullYear();

    const goalsData = {
      month: currentMonth,
      year: currentYear,
      meal_plans_goal: parseInt(document.getElementById("mealPlansGoal").value),
      meals_completed_goal: parseInt(
        document.getElementById("mealsCompletedGoal").value
      ),
      new_recipes_goal: parseInt(
        document.getElementById("newRecipesGoal").value
      ),
    };

    const response = await fetch("/api/meal-goals", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(goalsData),
    });

    const data = await response.json();

    if (data.success) {
      updateGoalTargets();
      updateGoalsProgress();

      // Show success message
      const saveBtn = document.getElementById("saveGoalsBtn");
      const originalText = saveBtn.innerHTML;
      saveBtn.innerHTML = '<i class="fas fa-check"></i> Saved!';
      saveBtn.style.background = "var(--success-gradient)";

      setTimeout(() => {
        saveBtn.innerHTML = originalText;
        saveBtn.style.background = "var(--primary-gradient)";
      }, 2000);
    } else {
      alert("Failed to save goals: " + data.message);
    }
  } catch (error) {
    console.error("Error saving goals:", error);
    alert("Failed to save goals. Please try again.");
  }
}

function resetGoals() {
  document.getElementById("mealPlansGoal").value = 4;
  document.getElementById("mealsCompletedGoal").value = 60;
  document.getElementById("newRecipesGoal").value = 12;

  updateGoalTargets();
  updateGoalsProgress();
}

function updateGoalTargets() {
  document.getElementById("mealPlansTarget").textContent =
    document.getElementById("mealPlansGoal").value;
  document.getElementById("mealsCompletedTarget").textContent =
    document.getElementById("mealsCompletedGoal").value;
  document.getElementById("newRecipesTarget").textContent =
    document.getElementById("newRecipesGoal").value;
}

async function updateGoalsProgress() {
  try {
    const currentMonth = new Date().getMonth() + 1;
    const currentYear = new Date().getFullYear();

    // Get progress data from the API
    const response = await fetch(
      `/api/meal-goals/progress?month=${currentMonth}&year=${currentYear}`
    );
    const data = await response.json();

    if (data.success) {
      const progress = data.progress;

      // Update displays with real data from backend
      updateGoalProgress("mealPlans", progress.meal_plans_count, "plans");
      updateGoalProgress(
        "mealsCompleted",
        progress.completed_meals_count,
        "meals"
      );
      updateGoalProgress("newRecipes", progress.new_recipes_count, "recipes");
    } else {
      console.error("Failed to load progress:", data.message);
      // Set zero values on error
      updateGoalProgress("mealPlans", 0, "plans");
      updateGoalProgress("mealsCompleted", 0, "meals");
      updateGoalProgress("newRecipes", 0, "recipes");
    }
  } catch (error) {
    console.error("Error updating goals progress:", error);
    // Set zero values on error
    updateGoalProgress("mealPlans", 0, "plans");
    updateGoalProgress("mealsCompleted", 0, "meals");
    updateGoalProgress("newRecipes", 0, "recipes");
  }
}

function updateGoalProgress(goalType, current, unit, isBudget = false) {
  const target = parseInt(document.getElementById(`${goalType}Goal`).value);
  const percentage = Math.min((current / target) * 100, 100);

  // Update progress bar
  document.getElementById(`${goalType}Progress`).style.width = `${percentage}%`;

  // Update current count
  const currentText = isBudget ? `$${current}` : `${current} ${unit}`;
  document.getElementById(`${goalType}Count`).textContent = currentText;
}

function setupGoalsEventListeners() {
  // Input change listeners
  document
    .getElementById("mealPlansGoal")
    .addEventListener("input", updateGoalTargets);
  document
    .getElementById("mealsCompletedGoal")
    .addEventListener("input", updateGoalTargets);
  document
    .getElementById("newRecipesGoal")
    .addEventListener("input", updateGoalTargets);

  // Button listeners
  document.getElementById("saveGoalsBtn").addEventListener("click", saveGoals);
  document
    .getElementById("resetGoalsBtn")
    .addEventListener("click", resetGoals);
}

document.addEventListener("DOMContentLoaded", function () {
  initializeDropdowns();
  handleDropdownResize();

  // Set default start date to today and prevent past dates and future dates beyond one month
  const today = new Date();
  const todayString = today.toISOString().split("T")[0];
  const oneMonthFromToday = new Date(today);
  oneMonthFromToday.setMonth(today.getMonth() + 1);
  const maxDateString = oneMonthFromToday.toISOString().split("T")[0];
  
  const startDateInput = document.getElementById("start_date");
  startDateInput.value = todayString;
  startDateInput.min = todayString;
  startDateInput.max = maxDateString;

  loadMealPlans();
  initializeCalendar();
  initializeGoals();

  // Initialize form handlers for slider and calendar preview
  initializeFormHandlers();

  // Setup generate button
  document
    .getElementById("generateBtn")
    .addEventListener("click", generateMealPlan);
});

function initializeCalendar() {
  // Setup calendar navigation with limits
  document.getElementById("prevMonth").addEventListener("click", async () => {
    const today = new Date();
    const twelveMonthsAgo = new Date(today);
    twelveMonthsAgo.setMonth(today.getMonth() - 12);
    
    // Check if we can go back one more month
    const potentialDate = new Date(currentDate);
    potentialDate.setMonth(currentDate.getMonth() - 1);
    
    if (potentialDate >= twelveMonthsAgo) {
      currentDate.setMonth(currentDate.getMonth() - 1);
      clearMealPlanPreview(); // Clear preview when changing months
      await loadMealsForCalendar();
      updateNavigationButtons();
    }
  });

  document.getElementById("nextMonth").addEventListener("click", async () => {
    const today = new Date();
    const twoMonthsFromNow = new Date(today);
    twoMonthsFromNow.setMonth(today.getMonth() + 2);
    
    // Check if we can go forward one more month
    const potentialDate = new Date(currentDate);
    potentialDate.setMonth(currentDate.getMonth() + 1);
    
    if (potentialDate <= twoMonthsFromNow) {
      currentDate.setMonth(currentDate.getMonth() + 1);
      clearMealPlanPreview(); // Clear preview when changing months
      await loadMealsForCalendar();
      updateNavigationButtons();
    }
  });

  // Initial button state update
  updateNavigationButtons();

  // Setup view toggle
  document.querySelectorAll(".calendar-view-btn").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      document
        .querySelectorAll(".calendar-view-btn")
        .forEach((b) => b.classList.remove("active"));
      e.target.classList.add("active");
      currentView = e.target.dataset.view;
      updateCalendarTitle();
      renderCalendar();
    });
  });

  renderCalendar();
}

function updateNavigationButtons() {
  const today = new Date();
  const twelveMonthsAgo = new Date(today);
  twelveMonthsAgo.setMonth(today.getMonth() - 12);
  const twoMonthsFromNow = new Date(today);
  twoMonthsFromNow.setMonth(today.getMonth() + 2);
  
  const prevButton = document.getElementById("prevMonth");
  const nextButton = document.getElementById("nextMonth");
  
  // Check if we can go back one more month
  const potentialPrevDate = new Date(currentDate);
  potentialPrevDate.setMonth(currentDate.getMonth() - 1);
  
  // Check if we can go forward one more month
  const potentialNextDate = new Date(currentDate);
  potentialNextDate.setMonth(currentDate.getMonth() + 1);
  
  // Disable/enable previous button
  if (potentialPrevDate < twelveMonthsAgo) {
    prevButton.disabled = true;
    prevButton.style.opacity = '0.4';
    prevButton.style.cursor = 'not-allowed';
    prevButton.title = 'Cannot go back more than 12 months';
  } else {
    prevButton.disabled = false;
    prevButton.style.opacity = '1';
    prevButton.style.cursor = 'pointer';
    prevButton.title = 'Previous month';
  }
  
  // Disable/enable next button
  if (potentialNextDate > twoMonthsFromNow) {
    nextButton.disabled = true;
    nextButton.style.opacity = '0.4';
    nextButton.style.cursor = 'not-allowed';
    nextButton.title = 'Cannot go forward more than 2 months';
  } else {
    nextButton.disabled = false;
    nextButton.style.opacity = '1';
    nextButton.style.cursor = 'pointer';
    nextButton.title = 'Next month';
  }
}

function updateCalendarTitle() {
  const titleElement = document.getElementById("calendarTitle");
  if (currentView === "month") {
    titleElement.textContent = "Your Month at a Glance";
  } else {
    titleElement.textContent = "Your Week at a Glance";
  }
}

function renderCalendar() {
  const monthNames = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
  ];

  const dayNames = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];

  // Update month/year display
  document.getElementById("monthYear").textContent = `${
    monthNames[currentDate.getMonth()]
  } ${currentDate.getFullYear()}`;

  const calendarGrid = document.getElementById("calendarGrid");
  calendarGrid.innerHTML = "";

  // Add day headers
  dayNames.forEach((day) => {
    const dayHeader = document.createElement("div");
    dayHeader.className = "calendar-day-header";
    dayHeader.textContent = day;
    calendarGrid.appendChild(dayHeader);
  });

  if (currentView === "month") {
    renderMonthView(calendarGrid);
  } else {
    renderWeekView(calendarGrid);
  }
  
  // Update navigation button states after rendering
  updateNavigationButtons();
}

function renderMonthView(container) {
  const year = currentDate.getFullYear();
  const month = currentDate.getMonth();

  // Get first day of month and number of days
  const firstDay = new Date(year, month, 1);
  const lastDay = new Date(year, month + 1, 0);
  const startDate = new Date(firstDay);
  startDate.setDate(startDate.getDate() - firstDay.getDay());

  // Generate 6 weeks (42 days)
  for (let i = 0; i < 42; i++) {
    const cellDate = new Date(startDate);
    cellDate.setDate(startDate.getDate() + i);

    const dayCell = createDayCell(cellDate, month);
    container.appendChild(dayCell);
  }
}

function renderWeekView(container) {
  const today = new Date();
  const currentWeekStart = new Date(today);
  currentWeekStart.setDate(today.getDate() - today.getDay());

  // Generate 7 days for current week
  for (let i = 0; i < 7; i++) {
    const cellDate = new Date(currentWeekStart);
    cellDate.setDate(currentWeekStart.getDate() + i);

    const dayCell = createWeekDayCell(cellDate);
    container.appendChild(dayCell);
  }
}

function createWeekDayCell(date) {
  const dayCell = document.createElement("div");
  dayCell.className = "calendar-day week-view";
  dayCell.setAttribute("data-date", date.toISOString().split("T")[0]);

  const today = new Date();
  const isToday = date.toDateString() === today.toDateString();

  if (isToday) {
    dayCell.classList.add("today");
  }

  // Day number
  const dayNumber = document.createElement("div");
  dayNumber.className = "calendar-day-number";
  dayNumber.textContent = date.getDate();
  dayCell.appendChild(dayNumber);

  // Meals container
  const mealsContainer = document.createElement("div");
  mealsContainer.className = "calendar-meals";

  // Find meals for this date
  const dayMeals = getMealsForDate(date);

  // Group meals by type
  const mealsByType = {
    breakfast: [],
    lunch: [],
    dinner: [],
    snack: [],
  };

  dayMeals.forEach((meal) => {
    if (mealsByType[meal.type]) {
      mealsByType[meal.type].push(meal);
    }
  });

  // Create fixed slots for each meal type
  const mealTypes = ["breakfast", "lunch", "dinner"];

  mealTypes.forEach((type) => {
    const mealSlot = document.createElement("div");
    mealSlot.className = `calendar-meal-slot ${type}`;

    const meals = mealsByType[type];
    if (meals.length > 0) {
      mealSlot.classList.add("has-meal");

      // Get the dish name from the first meal (or combine if multiple)
      const dishName =
        meals.length === 1
          ? getDishName(meals[0])
          : `${getDishName(meals[0])} +${meals.length - 1} more`;

      // Check if meal is in the future
      const today = new Date();
      today.setHours(0, 0, 0, 0);
      const mealDate = new Date(date);
      mealDate.setHours(0, 0, 0, 0);
      const isFuture = mealDate > today;

      mealSlot.innerHTML = `
        <div class="calendar-meal-type">${type}</div>
        <div class="calendar-meal-name">${dishName}</div>
        <div class="meal-completion">
            <input type="checkbox" class="meal-checkbox" ${
              meals[0].is_completed ? "checked" : ""
            } ${
        isFuture ? "disabled" : ""
      } onclick="event.stopPropagation(); toggleMealCompletion(${
        meals[0].meal_id
      }, this.checked, '${date.toISOString().split("T")[0]}')">
            <span style="font-size: 0.6rem; opacity: 0.8;">${
              isFuture ? "Future" : "Complete"
            }</span>
        </div>
        `;

      if (meals[0].is_completed) {
        mealSlot.classList.add("completed");
      }

      mealSlot.title = meals
        .map((meal) => `${type}: ${getDishName(meal)}`)
        .join("\n");

      // Add click handler for individual meal selection
      mealSlot.addEventListener("click", (e) => {
        e.stopPropagation(); // Prevent day click handler
        if (meals.length === 1) {
          showMealDetails(meals[0]);
        } else {
          showMealSelectionModal(date, meals);
        }
      });

      // Add hover effect for clickable meals
      mealSlot.style.cursor = "pointer";
    } else {
      mealSlot.innerHTML = `
        <div class="calendar-meal-type">No ${type}</div>
        `;
    }

    mealsContainer.appendChild(mealSlot);
  });

  if (dayMeals.length > 0) {
    dayCell.classList.add("has-meals");
  }

  dayCell.appendChild(mealsContainer);

  // Click handler for day details
  dayCell.addEventListener("click", () => showDayDetails(date, dayMeals));

  return dayCell;
}

function getDishName(meal) {
  // Extract actual dish name from meal name
  // Meal names might be in format "Day X Breakfast: Dish Name" or just "Dish Name"
  if (meal.name.includes(":")) {
    return meal.name.split(":").slice(1).join(":").trim();
  }
  return meal.name;
}

function createDayCell(date, currentMonth, isWeekView = false) {
  const dayCell = document.createElement("div");
  dayCell.className = "calendar-day";
  dayCell.setAttribute("data-date", date.toISOString().split("T")[0]);

  const today = new Date();
  const isToday = date.toDateString() === today.toDateString();
  const isCurrentMonth = date.getMonth() === currentMonth;

  if (isToday) {
    dayCell.classList.add("today");
  }

  if (!isCurrentMonth && !isWeekView) {
    dayCell.classList.add("other-month");
  }

  // Day number
  const dayNumber = document.createElement("div");
  dayNumber.className = "calendar-day-number";
  dayNumber.textContent = date.getDate();
  dayCell.appendChild(dayNumber);

  // Meals container
  const mealsContainer = document.createElement("div");
  mealsContainer.className = "calendar-meals";

  // Find meals for this date
  const dayMeals = getMealsForDate(date);

  if (dayMeals.length > 0) {
    dayCell.classList.add("has-meals");

    // Show up to 3 meals, then show count
    const visibleMeals = dayMeals.slice(0, 3);
    visibleMeals.forEach((meal) => {
      const mealElement = document.createElement("div");
      mealElement.className = `calendar-meal ${meal.type} ${
        meal.is_completed ? "completed" : ""
      }`;

      // Create checkbox
      const checkbox = document.createElement("input");
      checkbox.type = "checkbox";
      checkbox.className = "meal-checkbox";
      checkbox.checked = meal.is_completed;
      checkbox.addEventListener("click", (e) => {
        e.stopPropagation(); // Prevent day click handler
        toggleMealCompletion(meal.meal_id, checkbox.checked);
      });

      // Create meal name text
      const mealNameText = document.createElement("span");
      mealNameText.className = "meal-name-text";
      mealNameText.textContent = getDishName(meal);
      mealNameText.title = `${meal.type}: ${meal.name}`;

      // Make meal name clickable for details
      mealNameText.style.cursor = "pointer";
      mealNameText.addEventListener("click", (e) => {
        e.stopPropagation(); // Prevent day click handler
        showMealDetails(meal);
      });

      mealElement.appendChild(checkbox);
      mealElement.appendChild(mealNameText);
      mealsContainer.appendChild(mealElement);
    });

    if (dayMeals.length > 3) {
      const countElement = document.createElement("div");
      countElement.className = "calendar-meal-count";
      countElement.textContent = `+${dayMeals.length - 3} more`;
      countElement.style.cursor = "pointer";
      countElement.title = "Click to see all meals for this day";

      // Show meal selection modal when clicking "+X more"
      countElement.addEventListener("click", (e) => {
        e.stopPropagation(); // Prevent day click handler
        showMealSelectionModal(date, dayMeals);
      });

      mealsContainer.appendChild(countElement);
    }
  }

  dayCell.appendChild(mealsContainer);

  // Add click handler
  dayCell.addEventListener("click", () => {
    showDayDetails(date, dayMeals);
  });

  return dayCell;
}

function getMealsForDate(date) {
  const dateStr = date.toISOString().split("T")[0];

  // Return meals from the global mealsData for this date
  return (window.mealsData || mealsData || []).filter(
    (meal) => meal.date === dateStr
  );
}

function getDayName(dayNumber) {
  const dayNames = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
  if (dayNumber <= 7) {
    return dayNames[dayNumber - 1];
  }
  return `Day ${dayNumber}`;
}

function showDayDetails(date, meals) {
  if (meals.length === 0) {
    showEmptyDayPopup(date);
    return;
  }

  // Show meal selection modal if multiple meals, or direct meal view if one meal
  if (meals.length === 1) {
    showMealDetails(meals[0]);
  } else {
    showMealSelectionModal(date, meals);
  }
}

async function loadMealPlans() {
  try {
    console.log("Loading meal plans...");
    const response = await fetch("/api/meal-plans");
    const data = await response.json();

    console.log("Meal plans response:", data);

    if (data.success && data.plans && data.plans.length > 0) {
      console.log(`Found ${data.plans.length} meal plans`);

      // Store meal plan data for plan management
      mealPlanData = data.plans;

      displayMealPlans(data.plans);
      document.getElementById("emptyState").style.display = "none";
    } else {
      console.log("No meal plans found or error:", data);
      mealPlanData = [];
      document.getElementById("emptyState").style.display = "block";
    }

    // Load meals for calendar regardless of meal plans
    await loadMealsForCalendar();
  } catch (error) {
    console.error("Error loading meal plans:", error);
    mealPlanData = [];
    document.getElementById("emptyState").style.display = "block";
    await loadMealsForCalendar();
  }
}

async function loadMealsForCalendar() {
  try {
    // Get date range for current calendar view
    const startDate = new Date(
      currentDate.getFullYear(),
      currentDate.getMonth(),
      1
    );
    const endDate = new Date(
      currentDate.getFullYear(),
      currentDate.getMonth() + 1,
      0
    );

    // Extend range to cover full weeks
    const calendarStart = new Date(startDate);
    calendarStart.setDate(startDate.getDate() - startDate.getDay());
    const calendarEnd = new Date(endDate);
    calendarEnd.setDate(endDate.getDate() + (6 - endDate.getDay()));

    const startDateStr = calendarStart.toISOString().split("T")[0];
    const endDateStr = calendarEnd.toISOString().split("T")[0];

    console.log("Loading meals for calendar:", startDateStr, "to", endDateStr);

    const response = await fetch(
      `/api/meals?start_date=${startDateStr}&end_date=${endDateStr}`
    );
    const data = await response.json();

    if (data.success) {
      console.log(`Found ${data.meals.length} meals for calendar`);

      // Store meals data globally for calendar
      window.mealsData = data.meals || [];
      mealsData = data.meals || [];

      // Update calendar with new meal data
      if (typeof renderCalendar === "function") {
        renderCalendar();
      }
    } else {
      console.log("No meals found or error:", data);
      window.mealsData = [];
      mealsData = [];
      if (typeof renderCalendar === "function") {
        renderCalendar();
      }
    }
  } catch (error) {
    console.error("Error loading meals for calendar:", error);
    window.mealsData = [];
    mealsData = [];
    if (typeof renderCalendar === "function") {
      renderCalendar();
    }
  }
}

function displayMealPlans(plans) {
  const grid = document.getElementById("plansGrid");
  grid.innerHTML = "";

  plans.forEach((plan) => {
    const planCard = createPlanCard(plan);
    grid.appendChild(planCard);
  });
}

function createPlanCard(plan) {
  const card = document.createElement("div");
  card.className = "plan-card";
  card.onclick = () => viewPlanDetails(plan.plan_id);

  const startDate = new Date(plan.start_date).toLocaleDateString();
  const endDate = new Date(plan.end_date).toLocaleDateString();

  card.innerHTML = `
    <div class="plan-header">
        <div>
        <h3 class="plan-name">${plan.plan_name}</h3>
        <p class="plan-dates">${startDate} - ${endDate}</p>
        </div>
        <span class="plan-status status-${plan.status}">${plan.status}</span>
    </div>
    
    <div class="plan-details">
        <div class="plan-detail">
        <i class="fas fa-calendar-alt"></i>
        <span>${plan.total_days} days</span>
        </div>
        <div class="plan-detail">
        <i class="fas fa-leaf"></i>
        <span>${plan.dietary_preference || "No restrictions"}</span>
        </div>
        <div class="plan-detail">
        <i class="fas fa-dollar-sign"></i>
        <span>${
          plan.budget_limit ? "$" + plan.budget_limit : "No budget limit"
        }</span>
        </div>
        <div class="plan-detail">
        <i class="fas fa-clock"></i>
        <span>${plan.max_cooking_time} min/day</span>
        </div>
    </div>
    
    <div class="plan-actions">
        <button class="btn-view" onclick="event.stopPropagation(); viewPlanDetails(${
          plan.plan_id
        })">
        <i class="fas fa-eye"></i> View Details
        </button>
    </div>
    `;

  return card;
}

function highlightMealPlanDates(startDate, days) {
  // Clear any existing preview highlights
  clearMealPlanPreview();

  const startDateObj = new Date(startDate);

  // Highlight each day in the range
  for (let i = 0; i < days; i++) {
    const currentDate = new Date(startDateObj);
    currentDate.setDate(startDateObj.getDate() + i);

    const dateStr = currentDate.toISOString().split("T")[0];
    const calendarCell = document.querySelector(`[data-date="${dateStr}"]`);

    if (calendarCell) {
      calendarCell.classList.add("meal-plan-preview");

      // Add day number indicator
      if (i === 0) {
        calendarCell.classList.add("preview-start");
      } else if (i === days - 1) {
        calendarCell.classList.add("preview-end");
      } else {
        calendarCell.classList.add("preview-middle");
      }
    }
  }
}

function clearMealPlanPreview() {
  // Remove all preview classes from calendar cells
  const previewCells = document.querySelectorAll(".meal-plan-preview");
  previewCells.forEach((cell) => {
    cell.classList.remove(
      "meal-plan-preview",
      "preview-start",
      "preview-end",
      "preview-middle"
    );
  });
}

async function generateMealPlan() {
  const btn = document.getElementById("generateBtn");
  const spinner = document.getElementById("spinner");
  const icon = document.getElementById("generateIcon");
  const text = document.getElementById("generateText");

  // Show loading state
  btn.disabled = true;
  spinner.style.display = "block";
  icon.style.display = "none";
  text.textContent = "Generating...";

  try {
    const formData = new FormData(document.getElementById("generateForm"));

    // Validate required fields
    const startDate = formData.get("start_date");
    if (!startDate) {
      alert("Please select a start date for your meal plan.");
      // Reset button state
      btn.disabled = false;
      spinner.style.display = "none";
      icon.style.display = "inline";
      text.textContent = "Generate Meal Plan";
      return;
    }

    // Validate that start date is not more than one month in the future
    const selectedDate = new Date(startDate);
    const today = new Date();
    const oneMonthFromToday = new Date(today);
    oneMonthFromToday.setMonth(today.getMonth() + 1);

    if (selectedDate > oneMonthFromToday) {
      showDateLimitWarning();
      // Reset button state
      btn.disabled = false;
      spinner.style.display = "none";
      icon.style.display = "inline";
      text.textContent = "Generate Meal Plan";
      return;
    }

    const data = {
      start_date: startDate,
      days: parseInt(formData.get("days")),
      dietary_preference: formData.get("dietary_preference"),
      budget: formData.get("budget")
        ? parseFloat(formData.get("budget"))
        : null,
      cooking_time: parseInt(formData.get("cooking_time")),
    };

    const response = await fetch("/api/generate-meal-plan", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(data),
    });

    const result = await response.json();

    if (result.success) {
      // Show success message and reload plans
      alert(
        `Meal plan generated successfully! Created ${result.created_meals.length} meals.`
      );

      // Reload both meal plans and calendar meals
      await loadMealPlans();

      // Optionally navigate to the new session
      if (result.session_id) {
        viewPlanDetails(result.session_id);
      }
    } else {
      alert("Error generating meal plan: " + result.message);
    }
  } catch (error) {
    console.error("Error generating meal plan:", error);
    alert("Failed to generate meal plan. Please try again.");
  } finally {
    // Reset button state
    btn.disabled = false;
    spinner.style.display = "none";
    icon.style.display = "block";
    text.textContent = "Generate Meal Plan";

    // Clear meal plan preview after generation
    clearMealPlanPreview();
  }
}

function viewPlanDetails(planId) {
  // Navigate to plan details page
  window.location.href = `/meal-plans/${planId}`;
}

function showMealSelectionModal(date, meals) {
  const dateStr = date.toLocaleDateString("en-US", {
    weekday: "long",
    month: "long",
    day: "numeric",
  });

  const modalHTML = `
    <div id="mealSelectionModal" class="modal-overlay">
        <div class="modal-content">
        <div class="modal-header">
            <h3>Select a Meal - ${dateStr}</h3>
            <button class="modal-close" onclick="closeMealSelectionModal()">
            <i class="fas fa-times"></i>
            </button>
        </div>
        <div class="modal-body">
            <div class="meals-grid">
            ${meals
              .map(
                (meal) => `
                <div class="meal-card" onclick="showMealDetails(${JSON.stringify(
                  meal
                ).replace(/"/g, "&quot;")})">
                <div class="meal-type-badge ${meal.type}">
                    <i class="fas fa-${getMealIcon(meal.type)}"></i>
                    ${meal.type.charAt(0).toUpperCase() + meal.type.slice(1)}
                </div>
                <div class="meal-name">${meal.name}</div>
                ${
                  meal.prep_time
                    ? `<div class="meal-time">${
                        meal.prep_time + (meal.cook_time || 0)
                      } min total</div>`
                    : ""
                }
                </div>
            `
              )
              .join("")}
            </div>
        </div>
        </div>
    </div>
    `;

  document.body.insertAdjacentHTML("beforeend", modalHTML);

  // Show modal with animation
  setTimeout(() => {
    document.getElementById("mealSelectionModal").classList.add("show");
  }, 10);
}

function closeMealSelectionModal() {
  const modal = document.getElementById("mealSelectionModal");
  if (modal) {
    modal.classList.remove("show");
    setTimeout(() => {
      modal.remove();
    }, 300);
  }
}

async function showMealDetails(meal) {
  // Close meal selection modal if it exists
  closeMealSelectionModal();

  try {
    // Fetch detailed meal information
    const response = await fetch(`/api/meals/${meal.meal_id}`);
    const data = await response.json();

    if (data.success) {
      displayMealDetailsModal(data.meal);
    } else {
      alert("Failed to load meal details: " + data.message);
    }
  } catch (error) {
    console.error("Error loading meal details:", error);
    alert("Failed to load meal details. Please try again.");
  }
}

function displayMealDetailsModal(meal) {
  const modalHTML = `
    <div id="mealDetailsModal" class="modal-overlay">
        <div class="modal-content meal-details-modal">
        <div class="modal-header">
            <div>
            <h3>${meal.name}</h3>
            <p class="meal-meta">${
              meal.type.charAt(0).toUpperCase() + meal.type.slice(1)
            } • ${new Date(meal.date).toLocaleDateString()}</p>
            </div>
            <button class="modal-close" onclick="closeMealDetailsModal()">
            <i class="fas fa-times"></i>
            </button>
        </div>
        <div class="modal-body">
            <div class="meal-details-content">
            ${
              meal.description
                ? `<div class="meal-description">${meal.description}</div>`
                : ""
            }
            
            <div class="meal-info-grid">
                ${
                  meal.prep_time
                    ? `<div class="info-item"><i class="fas fa-clock"></i> Prep: ${meal.prep_time} min</div>`
                    : ""
                }
                ${
                  meal.cook_time
                    ? `<div class="info-item"><i class="fas fa-fire"></i> Cook: ${meal.cook_time} min</div>`
                    : ""
                }
                ${
                  meal.servings
                    ? `<div class="info-item"><i class="fas fa-users"></i> Serves: ${meal.servings}</div>`
                    : ""
                }
                ${
                  meal.difficulty
                    ? `<div class="info-item"><i class="fas fa-chart-line"></i> ${
                        meal.difficulty.charAt(0).toUpperCase() +
                        meal.difficulty.slice(1)
                      }</div>`
                    : ""
                }
                ${
                  meal.estimated_cost
                    ? `<div class="info-item"><i class="fas fa-dollar-sign"></i> ~$${meal.estimated_cost}</div>`
                    : ""
                }
                ${
                  meal.calories_per_serving
                    ? `<div class="info-item"><i class="fas fa-fire-alt"></i> ${meal.calories_per_serving} cal</div>`
                    : ""
                }
            </div>

            ${
              meal.ingredients && meal.ingredients.length > 0
                ? `
                <div class="meal-section">
                <h4><i class="fas fa-list-ul"></i> Ingredients</h4>
                <div class="ingredients-list">
                    ${meal.ingredients
                      .map(
                        (ingredient) => `
                    <div class="ingredient-item ${
                      ingredient.is_custom ? "custom" : ""
                    }">
                        <span class="ingredient-name">${
                          ingredient.ingredient_name
                        }</span>
                        <span class="ingredient-amount">${
                          ingredient.quantity
                        } ${ingredient.unit}</span>
                        ${
                          ingredient.notes
                            ? `<span class="ingredient-notes">${ingredient.notes}</span>`
                            : ""
                        }
                    </div>
                    `
                      )
                      .join("")}
                </div>
                </div>
            `
                : ""
            }

            ${
              meal.instructions
                ? `
                <div class="meal-section">
                <h4><i class="fas fa-clipboard-list"></i> Instructions</h4>
                <div class="instructions-content">${meal.instructions.replace(
                  /\\n/g,
                  "<br>"
                )}</div>
                </div>
            `
                : ""
            }

            ${
              meal.notes
                ? `
                <div class="meal-section">
                <h4><i class="fas fa-sticky-note"></i> Notes</h4>
                <div class="notes-content">${meal.notes}</div>
                </div>
            `
                : ""
            }
            </div>
            
            <div class="meal-actions">
            ${
              meal.session_id
                ? `
                <button class="btn btn-secondary" onclick="viewPlanDetails(${meal.session_id})">
                <i class="fas fa-calendar-alt"></i> View Full Meal Plan
                </button>
            `
                : ""
            }
            <button class="btn btn-primary" onclick="editMeal(${meal.meal_id})">
                <i class="fas fa-edit"></i> Edit Meal
            </button>
            </div>
        </div>
        </div>
    </div>
    `;

  document.body.insertAdjacentHTML("beforeend", modalHTML);

  // Show modal with animation
  setTimeout(() => {
    document.getElementById("mealDetailsModal").classList.add("show");
  }, 10);
}

function closeMealDetailsModal() {
  const modal = document.getElementById("mealDetailsModal");
  if (modal) {
    modal.classList.remove("show");
    setTimeout(() => {
      modal.remove();
    }, 300);
  }
}

function getMealIcon(mealType) {
  const icons = {
    breakfast: "coffee",
    lunch: "hamburger",
    dinner: "utensils",
    snack: "cookie-bite",
  };
  return icons[mealType] || "utensils";
}

function editMeal(mealId) {
  // Placeholder for meal editing functionality
  alert(
    `Meal editing functionality will be implemented here for meal ID: ${mealId}`
  );
  // This could open an edit modal or navigate to an edit page
}

async function toggleMealCompletion(mealId, isCompleted, mealDate = null) {
  // Prevent completing future meals
  if (mealDate) {
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const checkDate = new Date(mealDate);
    checkDate.setHours(0, 0, 0, 0);

    if (checkDate > today) {
      alert("You can only complete meals for today or past dates.");
      // Revert checkbox
      const checkbox = document.querySelector(`input[onclick*="${mealId}"]`);
      if (checkbox) {
        checkbox.checked = !isCompleted;
      }
      return;
    }
  }
  try {
    const response = await fetch(`/api/meals/${mealId}`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        is_completed: isCompleted,
      }),
    });

    const data = await response.json();

    if (data.success) {
      // Update the meal data in memory
      if (window.mealsData) {
        const meal = window.mealsData.find((m) => m.meal_id === mealId);
        if (meal) {
          meal.is_completed = isCompleted;
        }
      }

      // Refresh calendar view to show updated completion status
      renderCalendar();

      // Update goals progress if we're on the goals section
      if (typeof updateGoalsProgress === "function") {
        updateGoalsProgress();
      }
    } else {
      alert("Failed to update meal completion: " + data.message);
      // Revert checkbox state on error
      const checkbox = document.querySelector(`input[onclick*="${mealId}"]`);
      if (checkbox) {
        checkbox.checked = !isCompleted;
      }
    }
  } catch (error) {
    console.error("Error updating meal completion:", error);
    alert("Failed to update meal completion. Please try again.");
    // Revert checkbox state on error
    const checkbox = document.querySelector(`input[onclick*="${mealId}"]`);
    if (checkbox) {
      checkbox.checked = !isCompleted;
    }
  }
}

function showEmptyDayPopup(date) {
  const dateStr = date.toLocaleDateString("en-US", {
    weekday: "long",
    month: "long",
    day: "numeric",
  });

  // Store the selected date globally for use when navigating
  window.selectedEmptyDate = date.toISOString().split("T")[0];

  const popupHTML = `
    <div id="emptyDayPopup" class="modal-overlay">
        <div class="modal-content empty-day-popup">
        <div class="modal-body">
            <div class="empty-day-content">
            <div class="empty-day-icon">
                <i class="fas fa-calendar-plus"></i>
            </div>
            <h3 class="empty-day-title">No meals planned for ${dateStr}</h3>
            <p class="empty-day-message">
                Generate a meal plan to see your meals for this day and start planning your delicious week ahead!
            </p>
            <div class="empty-day-actions">
                <button class="btn btn-primary" onclick="closeEmptyDayPopupAndNavigate()">
                <i class="fas fa-magic"></i> Generate Meal Plan
                </button>
                <button class="btn btn-secondary" onclick="closeEmptyDayPopup()">
                <i class="fas fa-times"></i> Close
                </button>
            </div>
            </div>
        </div>
        </div>
    </div>
    `;

  document.body.insertAdjacentHTML("beforeend", popupHTML);

  // Show popup with animation
  setTimeout(() => {
    document.getElementById("emptyDayPopup").classList.add("show");
  }, 10);

  // Auto-close after 4 seconds if user doesn't interact
  setTimeout(() => {
    const popup = document.getElementById("emptyDayPopup");
    if (popup && !popup.classList.contains("user-interacted")) {
      closeEmptyDayPopupAndNavigate();
    }
  }, 4000);

  // Mark as user-interacted when they hover or click
  const popup = document.getElementById("emptyDayPopup");
  popup.addEventListener("mouseenter", () => {
    popup.classList.add("user-interacted");
  });

  // Close popup when clicking outside
  popup.addEventListener("click", (e) => {
    if (e.target === popup) {
      closeEmptyDayPopup();
    }
  });

  // Close popup with Escape key
  document.addEventListener("keydown", handleEmptyDayEscape);
}

function handleEmptyDayEscape(e) {
  if (e.key === "Escape") {
    const popup = document.getElementById("emptyDayPopup");
    if (popup) {
      closeEmptyDayPopup();
      document.removeEventListener("keydown", handleEmptyDayEscape);
    }
  }
}

function closeEmptyDayPopup() {
  const popup = document.getElementById("emptyDayPopup");
  if (popup) {
    popup.classList.remove("show");
    document.removeEventListener("keydown", handleEmptyDayEscape);
    setTimeout(() => {
      popup.remove();
    }, 300);
  }
}

function closeEmptyDayPopupAndNavigate() {
  closeEmptyDayPopup();

  // Wait for popup to close, then scroll to generate section
  setTimeout(() => {
    const generateSection = document.querySelector(".generate-section");
    if (generateSection) {
      generateSection.scrollIntoView({
        behavior: "smooth",
        block: "center",
      });

      // Set the start date to the selected empty date
      if (window.selectedEmptyDate) {
        const startDateInput = document.getElementById("start_date");
        if (startDateInput) {
          startDateInput.value = window.selectedEmptyDate;
          
          // Trigger calendar preview update
          const event = new Event('change');
          startDateInput.dispatchEvent(event);
        }
      }

      // Optional: Focus on the form for better UX
      setTimeout(() => {
        const daysInput = document.getElementById("days");
        if (daysInput) {
          daysInput.focus();
        }
      }, 800);
    }
  }, 300);
}

function showDateLimitWarning() {
  const today = new Date();
  const oneMonthFromToday = new Date(today);
  oneMonthFromToday.setMonth(today.getMonth() + 1);
  
  const maxDateStr = oneMonthFromToday.toLocaleDateString("en-US", {
    weekday: "long",
    month: "long",
    day: "numeric",
    year: "numeric"
  });

  const popupHTML = `
    <div id="dateLimitWarning" class="modal-overlay">
        <div class="modal-content date-limit-popup">
        <div class="modal-body">
            <div class="warning-content">
            <div class="warning-icon">
                <i class="fas fa-exclamation-triangle"></i>
            </div>
            <h3 class="warning-title">Date Too Far in Future</h3>
            <p class="warning-message">
                You can only plan meals up to one month in advance. Please select a date on or before <strong>${maxDateStr}</strong>.
            </p>
            <div class="warning-actions">
                <button class="btn btn-primary" onclick="closeDateLimitWarning()">
                <i class="fas fa-check"></i> Got It
                </button>
            </div>
            </div>
        </div>
        </div>
    </div>
    `;

  document.body.insertAdjacentHTML("beforeend", popupHTML);

  // Show popup with animation
  setTimeout(() => {
    document.getElementById("dateLimitWarning").classList.add("show");
  }, 10);

  // Close popup when clicking outside
  const popup = document.getElementById("dateLimitWarning");
  popup.addEventListener("click", (e) => {
    if (e.target === popup) {
      closeDateLimitWarning();
    }
  });

  // Close popup with Escape key
  document.addEventListener("keydown", handleDateLimitEscape);
}

function handleDateLimitEscape(e) {
  if (e.key === "Escape") {
    const popup = document.getElementById("dateLimitWarning");
    if (popup) {
      closeDateLimitWarning();
      document.removeEventListener("keydown", handleDateLimitEscape);
    }
  }
}

function closeDateLimitWarning() {
  const popup = document.getElementById("dateLimitWarning");
  if (popup) {
    popup.classList.remove("show");
    document.removeEventListener("keydown", handleDateLimitEscape);
    setTimeout(() => {
      popup.remove();
    }, 300);
  }
}

// Handle range input for number of days and calendar preview
function initializeFormHandlers() {
  const daysRange = document.getElementById("days");
  const daysValue = document.getElementById("daysValue");
  const startDateInput = document.getElementById("start_date");

  function updateCalendarPreview() {
    const startDate = startDateInput?.value;
    const days = parseInt(daysRange?.value || 7);

    if (startDate && days) {
      highlightMealPlanDates(startDate, days);
    } else {
      clearMealPlanPreview();
    }
  }

  if (daysRange && daysValue) {
    daysRange.addEventListener("input", function () {
      const value = parseInt(this.value);
      daysValue.textContent = value;
      updateCalendarPreview();
    });
  }

  if (startDateInput) {
    startDateInput.addEventListener("change", updateCalendarPreview);
  }
}
