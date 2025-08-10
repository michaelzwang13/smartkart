// Initialize nutrition page functionality

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

// Load current nutrition goals from API
async function loadNutritionGoals() {
  try {
    const response = await fetch("/api/nutrition/goals");
    if (response.ok) {
      const data = await response.json();
      if (data.success && data.goals) {
        // Populate form with current goals
        document.getElementById("dailyCaloriesInput").value = data.goals.daily_calories || 2000;
        document.getElementById("dailyProteinInput").value = data.goals.daily_protein || 150;
        document.getElementById("dailyCarbsInput").value = data.goals.daily_carbs || 250;
        document.getElementById("dailyFatInput").value = data.goals.daily_fat || 70;
        document.getElementById("dailyFiberInput").value = data.goals.daily_fiber || 25;
        document.getElementById("dailySodiumLimitInput").value = data.goals.daily_sodium_limit || 2300;
      }
    }
  } catch (error) {
    console.error("Error loading nutrition goals:", error);
  }
}

// Handle nutrition goals form submission
async function handleNutritionGoals(event) {
  event.preventDefault();

  const goalData = {
    daily_calories: parseFloat(document.getElementById("dailyCaloriesInput").value),
    daily_protein: parseFloat(document.getElementById("dailyProteinInput").value),
    daily_carbs: parseFloat(document.getElementById("dailyCarbsInput").value),
    daily_fat: parseFloat(document.getElementById("dailyFatInput").value),
    daily_fiber: parseFloat(document.getElementById("dailyFiberInput").value),
    daily_sodium_limit: parseFloat(document.getElementById("dailySodiumLimitInput").value),
    goal_type: "custom",
    activity_level: "moderately_active"
  };

  try {
    const response = await fetch("/api/nutrition/goals", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(goalData),
    });

    if (response.ok) {
      const data = await response.json();
      if (data.success) {
        alert("Nutrition goals saved successfully!");
        // Refresh nutrition stats if they exist
        loadNutritionStats();
      } else {
        alert("Failed to save nutrition goals: " + data.message);
      }
    } else {
      const errorData = await response.json();
      alert("Failed to save nutrition goals: " + errorData.message);
    }
  } catch (error) {
    console.error("Error saving nutrition goals:", error);
    alert("An error occurred while saving nutrition goals.");
  }
}

// Load nutrition statistics (placeholder for future implementation)
async function loadNutritionStats() {
  try {
    // TODO: Implement nutrition analytics API endpoints
    // This will be implemented later when nutrition analytics are added
    console.log("Nutrition stats loading will be implemented later");
    
    // For now, we can update the stats with placeholder or calculated values
    // In the future, this will fetch real data from nutrition analytics API
  } catch (error) {
    console.error("Error loading nutrition stats:", error);
  }
}

// Initialize chart controls (placeholder for future implementation)
function initializeChartControls() {
  // Chart period controls
  document.querySelectorAll(".chart-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      const period = btn.dataset.period;
      
      // TODO: Load nutrition chart data for the selected period
      console.log("Loading nutrition charts for period:", period);
      
      // Update active button
      document
        .querySelectorAll(".chart-btn")
        .forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
    });
  });
}

// Initialize everything when DOM is loaded
document.addEventListener("DOMContentLoaded", function () {
  initializeDropdowns();
  handleDropdownResize();
  initializeChartControls();

  // Nutrition goals form
  document
    .getElementById("nutritionGoalsForm")
    .addEventListener("submit", handleNutritionGoals);

  // Load initial data
  loadNutritionGoals();
  loadNutritionStats();
});