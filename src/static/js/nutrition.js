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
        
        // Only show premium fields if user has access to them
        if (data.goals.daily_carbs !== null) {
          document.getElementById("dailyCarbsInput").value = data.goals.daily_carbs || 250;
        }
        if (data.goals.daily_fat !== null) {
          document.getElementById("dailyFatInput").value = data.goals.daily_fat || 70;
        }
        if (data.goals.daily_fiber !== null) {
          document.getElementById("dailyFiberInput").value = data.goals.daily_fiber || 25;
        }
        if (data.goals.daily_sodium_limit !== null) {
          document.getElementById("dailySodiumLimitInput").value = data.goals.daily_sodium_limit || 2300;
        }
        
        // Handle subscription limitations for free tier
        if (data._limited_tier) {
          await handleSubscriptionLimitations();
        }
      }
    }
  } catch (error) {
    console.error("Error loading nutrition goals:", error);
  }
}

// Handle subscription limitations for free tier users
async function handleSubscriptionLimitations() {
  const subscriptionStatus = await getUserSubscriptionStatus();
  
  if (subscriptionStatus.tier === 'free') {
    // Hide premium-only form fields
    const premiumFields = [
      'dailyCarbsInput', 
      'dailyFatInput', 
      'dailyFiberInput', 
      'dailySodiumLimitInput'
    ];
    
    premiumFields.forEach(fieldId => {
      const fieldGroup = document.getElementById(fieldId)?.closest('.form-group');
      if (fieldGroup) {
        fieldGroup.style.display = 'none';
      }
    });
    
    // Add upgrade prompt to form
    const settingsForm = document.getElementById('nutritionGoalsForm');
    if (settingsForm && !document.getElementById('upgrade-prompt')) {
      const upgradePrompt = document.createElement('div');
      upgradePrompt.id = 'upgrade-prompt';
      upgradePrompt.className = 'upgrade-prompt';
      upgradePrompt.innerHTML = `
        <div style="
          background: var(--bg-secondary);
          border: 2px dashed var(--border-light);
          border-radius: var(--radius-md);
          padding: var(--spacing-lg);
          text-align: center;
          margin-bottom: var(--spacing-lg);
        ">
          <i class="fas fa-star" style="color: var(--primary-color); font-size: 1.5rem; margin-bottom: var(--spacing-sm);"></i>
          <p style="color: var(--text-secondary); margin: 0 0 var(--spacing-md) 0;">
            Track your full macros & nutrients — Upgrade to Preppr Premium!
          </p>
          <button type="button" class="btn-primary" onclick="showUpgradeModal('macro_tracking', 'calories + protein only', 'Track your full macros & nutrients — Upgrade to Preppr Premium!')">
            <i class="fas fa-star"></i>
            Upgrade to Premium
          </button>
        </div>
      `;
      settingsForm.insertBefore(upgradePrompt, settingsForm.firstChild);
    }
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

// Initialize chart controls with subscription-aware functionality
async function initializeChartControls() {
  // Get user's subscription status
  const subscriptionStatus = await getUserSubscriptionStatus();
  
  // Chart period controls
  document.querySelectorAll(".chart-btn").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const period = btn.dataset.period;
      
      // Check if user can access historical data (premium only)
      if (subscriptionStatus.tier === 'free' && period !== '7d') {
        // Show upgrade modal for non-premium users trying to access history
        showUpgradeModal(
          'macro_history',
          'today only',
          'Track your full macro history & trends — Upgrade to Preppr Premium!'
        );
        return;
      }
      
      // Load nutrition chart data for the selected period
      console.log("Loading nutrition charts for period:", period);
      
      // Update active button
      document
        .querySelectorAll(".chart-btn")
        .forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      
      // Load chart data (will be implemented when charts are added)
      await loadNutritionChartData(period);
    });
  });
  
  // Hide historical chart buttons for free tier users
  if (subscriptionStatus.tier === 'free') {
    document.querySelectorAll(".chart-btn").forEach((btn) => {
      if (btn.dataset.period !== '7d') {
        btn.style.display = 'none';
      }
    });
    
    // Update the remaining button text to clarify it's current week only
    const weekBtn = document.querySelector('.chart-btn[data-period="7d"]');
    if (weekBtn) {
      weekBtn.textContent = 'This Week';
      weekBtn.title = 'Free tier: Current week only. Upgrade for full history.';
    }
  }
}

// Placeholder for chart data loading (will be implemented later)
async function loadNutritionChartData(period) {
  // This will be implemented when the nutrition analytics API endpoints are added
  console.log(`Loading chart data for period: ${period}`);
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