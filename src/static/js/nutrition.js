// Initialize nutrition page functionality

// Initialize goal/limit toggles
function initializeGoalLimitToggles() {
  const toggleGroups = document.querySelectorAll('.goal-limit-toggle');
  
  toggleGroups.forEach(toggleGroup => {
    const buttons = toggleGroup.querySelectorAll('.toggle-option');
    
    buttons.forEach(button => {
      button.addEventListener('click', function() {
        // Remove active class from all buttons in this group
        buttons.forEach(btn => btn.classList.remove('active'));
        
        // Add active class to clicked button
        this.classList.add('active');
        
        // Get the metric and type
        const metric = toggleGroup.dataset.metric;
        const type = this.dataset.type;
        
        // Update label text to reflect goal vs limit
        const label = toggleGroup.parentElement.querySelector('.form-label');
        const originalText = label.textContent.replace(' Goal', '').replace(' Limit', '');
        
        if (type === 'goal') {
          label.textContent = originalText + ' Goal';
        } else {
          label.textContent = originalText + ' Limit';
        }
        
        // Store the selection for form submission
        toggleGroup.setAttribute('data-selected-type', type);
        
        console.log(`${metric} set to ${type}`, 'Toggle group:', toggleGroup);
      });
    });
  });
}

// Get nutrition goals data including goal/limit types
function getNutritionGoalsData() {
  const formData = {};
  
  // Get all toggle groups
  const toggleGroups = document.querySelectorAll('.goal-limit-toggle');
  
  toggleGroups.forEach(toggleGroup => {
    const metric = toggleGroup.dataset.metric;
    const selectedType = toggleGroup.getAttribute('data-selected-type') || 'goal';
    const input = toggleGroup.parentElement.querySelector('.form-input');
    
    formData[metric] = {
      value: parseFloat(input.value),
      type: selectedType
    };
  });
  
  return formData;
}

// Load saved nutrition goals and preferences
async function loadNutritionGoals() {
  try {
    const response = await fetch("/api/nutrition/goals");
    const data = await response.json();

    console.log("IDK WHATS GOING ON")
    console.log(data)

    if (data.success && data.goals) {
      const goals = data.goals;
      
      // Update form inputs with saved values
      document.getElementById("dailyCaloriesInput").value = goals.daily_calories || 2000;
      document.getElementById("dailyProteinInput").value = goals.daily_protein || 150;
      document.getElementById("dailyCarbsInput").value = goals.daily_carbs || 250;
      document.getElementById("dailyFatInput").value = goals.daily_fat || 70;
      document.getElementById("dailyFiberInput").value = goals.daily_fiber || 25;
      document.getElementById("dailySodiumLimitInput").value = goals.daily_sodium || 2300;
      
      // Update toggles with saved preferences
      updateToggleState('calories', goals.calories_type || 'goal');
      updateToggleState('protein', goals.protein_type || 'goal');
      updateToggleState('carbs', goals.carbs_type || 'goal');
      updateToggleState('fat', goals.fat_type || 'goal');
      updateToggleState('fiber', goals.fiber_type || 'goal');
      updateToggleState('sodium', goals.sodium_type || 'limit');
      
      console.log("Nutrition goals loaded successfully");
    } else {
      console.log("No saved nutrition goals found, using defaults");
    }
  } catch (error) {
    console.error("Error loading nutrition goals:", error);
  }
}

// Update toggle state and label for a specific metric
function updateToggleState(metric, type) {
  const toggleGroup = document.querySelector(`[data-metric="${metric}"]`);
  if (!toggleGroup) return;
  
  const buttons = toggleGroup.querySelectorAll('.toggle-option');
  const label = toggleGroup.parentElement.querySelector('.form-label');
  
  // Remove active class from all buttons
  buttons.forEach(btn => btn.classList.remove('active'));
  
  // Add active class to the correct button
  const activeButton = toggleGroup.querySelector(`[data-type="${type}"]`);
  if (activeButton) {
    activeButton.classList.add('active');
  }
  
  // Update label text
  const originalText = label.textContent.replace(' Goal', '').replace(' Limit', '');
  if (type === 'goal') {
    label.textContent = originalText + ' Goal';
  } else {
    label.textContent = originalText + ' Limit';
  }
  
  // Store the selection
  toggleGroup.setAttribute('data-selected-type', type);
}


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


// Handle subscription limitations for free tier users
async function handleSubscriptionLimitations() {
  const subscriptionStatus = await getUserSubscriptionStatus();
  
  if (subscriptionStatus.tier === 'free') {
    // Hide premium-only form fields (carbs, fiber, sodium - fat is allowed for free users)
    const premiumFields = [
      'dailyCarbsInput', 
      'dailyFiberInput', 
      'dailySodiumLimitInput'
    ];
    
    premiumFields.forEach(fieldId => {
      const fieldGroup = document.getElementById(fieldId)?.closest('.form-group-with-toggle');
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
          <button type="button" class="btn-primary" onclick="redirectToUpgrade()">
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

  // Get the toggle data using our new function
  const nutritionData = getNutritionGoalsData();
  console.log('Collected nutrition data:', nutritionData);
  
  // Format the data for the API, maintaining backwards compatibility
  const goalData = {
    daily_calories: nutritionData.calories.value,
    calories_type: nutritionData.calories.type,
    daily_protein: nutritionData.protein.value,
    protein_type: nutritionData.protein.type,
    daily_carbs: nutritionData.carbs.value,
    carbs_type: nutritionData.carbs.type,
    daily_fat: nutritionData.fat.value,
    fat_type: nutritionData.fat.type,
    daily_fiber: nutritionData.fiber.value,
    fiber_type: nutritionData.fiber.type,
    daily_sodium: nutritionData.sodium.value,
    sodium_type: nutritionData.sodium.type,
    goal_type: "custom",
    activity_level: "moderately_active"
  };

  console.log('Sending goal data to server:', goalData);

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
  initializeGoalLimitToggles();
  handleSubscriptionLimitations();

  // Nutrition goals form
  document
    .getElementById("nutritionGoalsForm")
    .addEventListener("submit", handleNutritionGoals);

  // Load initial data
  loadNutritionGoals();
  loadNutritionStats();
});