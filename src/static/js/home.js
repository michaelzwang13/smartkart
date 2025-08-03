// Dynamic greeting based on time of day
function updateWelcomeMessage() {
  const now = new Date();
  const hour = now.getHours();
  const welcomeTimeEl = document.getElementById("welcomeTime");

  let greeting = "";
  let message = "";

  if (hour < 12) {
    greeting = "Good morning";
    message = "Ready to start your day with meal prepping?";
  } else if (hour < 17) {
    greeting = "Good afternoon";
    message = "Perfect time for some smart shopping!";
  } else {
    greeting = "Good evening";
    message = "Plan ahead for tomorrow's meal prep needs!";
  }

  welcomeTimeEl.textContent = `${greeting}! ${message}`;
}

// Animate stats on page load
function animateStats() {
  const statValues = document.querySelectorAll(".stat-value");

  statValues.forEach((stat, index) => {
    setTimeout(() => {
      stat.style.animation = "pulse 0.6s ease";
    }, index * 200);
  });
}

// Interactive Card Stack Functionality
let currentSlide = 2; // Start with center card (index 2) - "Start Shopping" with 5 cards
const totalSlides = 5;
let autoRotateInterval;
let isUserInteracting = false;
let lastNavigationTime = 0;
const NAVIGATION_COOLDOWN = 800; // Minimum time between navigations in milliseconds
const AUTO_ROTATE_INTERVAL = 1500; // 3x slower than manual (800ms * 3)

function initializeCarousel() {
  const container = document.querySelector(".carousel-container");
  const carouselSection = document.querySelector(".carousel-section");

  // Set initial positions
  updateCarousel();

  // Mouse movement for card-based navigation
  container.addEventListener("mousemove", (e) => {
    const rect = container.getBoundingClientRect();
    const centerX = rect.left + rect.width / 2;
    const centerY = rect.top + rect.height / 2;
    const mouseX = e.clientX;
    const mouseY = e.clientY;
    const offsetX = (mouseX - centerX) / rect.width; // -0.5 to 0.5

    // Define center dead zone (rectangular area in the middle)
    const deadZoneWidth = 200; // Width of the dead zone
    const deadZoneHeight = rect.height * 0.8; // Height covers most of the card height

    const isInDeadZone =
      mouseX >= centerX - deadZoneWidth / 2 &&
      mouseX <= centerX + deadZoneWidth / 2 &&
      mouseY >= centerY - deadZoneHeight / 2 &&
      mouseY <= centerY + deadZoneHeight / 2;

    // Apply subtle rotation based on mouse position
    const rotation = offsetX * 8; // Max 4 degrees rotation
    container.style.transform = `perspective(1000px) rotateY(${rotation}deg)`;

    // If in dead zone, stop any continuous navigation
    if (isInDeadZone) {
      if (container.continuousNavigation) {
        container.continuousNavigation = false;
        container.currentDirection = null;

        if (container.navigationInterval) {
          clearInterval(container.navigationInterval);
          container.navigationInterval = null;
        }
      }

      container.style.filter = "brightness(1)";
      resumeAutoRotate();
      return; // Exit early, no further processing
    }

    // Check if mouse is over any card
    const carouselItems = container.querySelectorAll(".carousel-item");
    let isOverCard = false;
    let cardDirection = null;
    let hoveredCardIndex = -1;

    carouselItems.forEach((item, index) => {
      const card = item.querySelector(".action-card");
      const cardRect = card.getBoundingClientRect();

      if (
        e.clientX >= cardRect.left &&
        e.clientX <= cardRect.right &&
        e.clientY >= cardRect.top &&
        e.clientY <= cardRect.bottom
      ) {
        isOverCard = true;
        hoveredCardIndex = index;

        // Check if this is the center card (active card) - this should stop movement
        if (index === currentSlide) {
          cardDirection = "center";
          //   console.log('Hovering over center card - should stop movement');
        } else {
          // Determine if this card is to the left or right of center based on card position
          const cardCenterX = cardRect.left + cardRect.width / 2;
          if (cardCenterX < centerX) {
            cardDirection = "left";
            // console.log('Hovering over left card - should move left');
          } else if (cardCenterX > centerX) {
            cardDirection = "right";
            // console.log('Hovering over right card - should move right');
          }
        }
      }
    });

    if (isOverCard && cardDirection && cardDirection !== "center") {
      pauseAutoRotate();

      // Start continuous navigation if not already running
      if (!container.continuousNavigation) {
        container.continuousNavigation = true;
        startContinuousNavigation(cardDirection);
      }

      // Update direction and hovered card index for continuous navigation
      container.currentDirection = cardDirection;
      container.hoveredCardIndex = hoveredCardIndex;

      // Visual feedback when over a navigable card
      container.style.filter = "brightness(1.05)";
    } else {
      // Stop continuous navigation when not over any card or over center card
      if (container.continuousNavigation) {
        container.continuousNavigation = false;
        container.currentDirection = null;

        if (container.navigationInterval) {
          clearInterval(container.navigationInterval);
          container.navigationInterval = null;
        }
      }

      container.style.filter = "brightness(1)";
      resumeAutoRotate();
    }
  });

  container.addEventListener("mouseleave", () => {
    container.style.transform = "perspective(1000px) rotateY(0deg)";
    container.style.filter = "brightness(1)";

    // Stop continuous navigation on mouse leave
    if (container.continuousNavigation) {
      container.continuousNavigation = false;
      container.currentDirection = null;

      if (container.navigationInterval) {
        clearInterval(container.navigationInterval);
        container.navigationInterval = null;
      }
    }

    // Reset navigation state to prevent speed cap issues
    lastNavigationTime = 0;
    container.hoveredCardIndex = null;

    resumeAutoRotate();
  });

  // Additional mouseleave on carousel section to ensure complete cleanup
  carouselSection.addEventListener("mouseleave", () => {
    // Force stop all navigation
    if (container.continuousNavigation) {
      container.continuousNavigation = false;
      container.currentDirection = null;

      if (container.navigationInterval) {
        clearInterval(container.navigationInterval);
        container.navigationInterval = null;
      }
    }

    // Reset all navigation state
    lastNavigationTime = 0;
    container.hoveredCardIndex = null;

    // Reset visual state
    container.style.transform = "perspective(1000px) rotateY(0deg)";
    container.style.filter = "brightness(1)";

    resumeAutoRotate();
  });

  // Click detection for navigation
  container.addEventListener("click", (e) => {
    const rect = container.getBoundingClientRect();
    const centerX = rect.left + rect.width / 2;
    const clickX = e.clientX;
    const offsetX = (clickX - centerX) / rect.width;

    pauseAutoRotate();

    if (offsetX > 0.2) {
      // Clicked on right side - next slide
      currentSlide = (currentSlide + 1) % totalSlides;
    } else if (offsetX < -0.2) {
      // Clicked on left side - previous slide
      currentSlide = (currentSlide - 1 + totalSlides) % totalSlides;
    }

    updateCarousel();
    resumeAutoRotate();
  });

  // Touch/swipe support
  let startX = 0;
  let isDragging = false;

  container.addEventListener("touchstart", (e) => {
    startX = e.touches[0].clientX;
    isDragging = true;
    pauseAutoRotate();
  });

  container.addEventListener("touchmove", (e) => {
    if (!isDragging) return;
    e.preventDefault();
  });

  container.addEventListener("touchend", (e) => {
    if (!isDragging) return;

    const endX = e.changedTouches[0].clientX;
    const diff = startX - endX;

    if (Math.abs(diff) > 50) {
      if (diff > 0) {
        currentSlide = (currentSlide + 1) % totalSlides;
      } else {
        currentSlide = (currentSlide - 1 + totalSlides) % totalSlides;
      }
      updateCarousel();
    }

    isDragging = false;
    resumeAutoRotate();
  });

  // Start auto-rotation
  startAutoRotate();
}

function updateCarousel() {
  const items = document.querySelectorAll(".carousel-item");

  // Define position configurations for each slot (5 cards: 2 left + 1 center + 2 right)
  const positions = [
    { x: -400, rotation: -12, scale: 0.82, opacity: 0.75, zIndex: 1 }, // Far left
    { x: -200, rotation: -6, scale: 0.9, opacity: 0.85, zIndex: 2 }, // Near left
    { x: 0, rotation: 0, scale: 1, opacity: 1, zIndex: 5 }, // Center
    { x: 200, rotation: 6, scale: 0.9, opacity: 0.85, zIndex: 2 }, // Near right
    { x: 400, rotation: 12, scale: 0.82, opacity: 0.75, zIndex: 1 }, // Far right
  ];

  items.forEach((item, index) => {
    // Calculate the position index for this item based on current slide
    const positionIndex = (index - currentSlide + totalSlides) % totalSlides;
    const position = positions[positionIndex] || positions[4];

    // Ensure smooth z-index transitions to prevent overlapping
    let zIndex = position.zIndex;

    // Boost z-index for cards that are transitioning to/from center
    const distanceFromCenter = Math.abs(positionIndex - 3);
    if (distanceFromCenter <= 1) {
      zIndex = position.zIndex + (2 - distanceFromCenter);
    }

    item.style.transform = `translateX(${position.x}px) rotateY(${position.rotation}deg) scale(${position.scale})`;
    item.style.opacity = position.opacity;
    item.style.zIndex = zIndex;
  });
}

// Continuous navigation function for smooth movement
function startContinuousNavigation(initialDirection) {
  const container = document.querySelector(".carousel-container");

  // Set up interval for continuous movement
  container.navigationInterval = setInterval(() => {
    // Check if we should still be navigating
    if (!container.continuousNavigation || !container.currentDirection) {
      clearInterval(container.navigationInterval);
      container.navigationInterval = null;
      return;
    }

    const currentTime = Date.now();

    // Check cooldown to cap the rate
    if (currentTime - lastNavigationTime < NAVIGATION_COOLDOWN) {
      return; // Skip this iteration if still in cooldown
    }

    // Navigate based on current direction
    if (container.currentDirection === "right") {
      currentSlide = (currentSlide + 1) % totalSlides;
      updateCarousel();
      lastNavigationTime = currentTime;

      // Stop immediately if the hovered card is now the center card
      if (container.hoveredCardIndex === currentSlide) {
        container.continuousNavigation = false;
        container.currentDirection = null;
        clearInterval(container.navigationInterval);
        container.navigationInterval = null;
      }
    } else if (container.currentDirection === "left") {
      currentSlide = (currentSlide - 1 + totalSlides) % totalSlides;
      updateCarousel();
      lastNavigationTime = currentTime;

      // Stop immediately if the hovered card is now the center card
      if (container.hoveredCardIndex === currentSlide) {
        container.continuousNavigation = false;
        container.currentDirection = null;
        clearInterval(container.navigationInterval);
        container.navigationInterval = null;
      }
    }
  }, 100); // Check every 100ms, but actual navigation is rate-limited by cooldown
}

function startAutoRotate() {
  // Clear any existing interval
  if (autoRotateInterval) {
    clearInterval(autoRotateInterval);
  }

  autoRotateInterval = setInterval(() => {
    if (!isUserInteracting) {
      currentSlide = (currentSlide + 1) % totalSlides;
      updateCarousel();
    }
  }, AUTO_ROTATE_INTERVAL); // Use the 3x slower interval
}

function pauseAutoRotate() {
  isUserInteracting = true;
  if (autoRotateInterval) {
    clearInterval(autoRotateInterval);
    autoRotateInterval = null;
  }
}

function resumeAutoRotate() {
  setTimeout(() => {
    isUserInteracting = false;
    startAutoRotate();
  }, 1500); // Resume after 2.7 seconds of no interaction
}

// Enhanced hover effects for carousel items
function initializeHoverEffects() {
  const actionCards = document.querySelectorAll(".action-card");

  actionCards.forEach((card) => {
    card.addEventListener("mouseenter", function () {
      // Enhanced hover animation handled by CSS
      this.classList.add("hovered");
    });

    card.addEventListener("mouseleave", function () {
      this.classList.remove("hovered");
    });
  });
}

// Header scroll effect
function initializeScrollEffects() {
  const header = document.querySelector(".header");

  window.addEventListener("scroll", function () {
    if (window.scrollY > 100) {
      header.style.background = "rgba(255, 255, 255, 0.98)";
      header.style.borderBottom = "1px solid var(--border-medium)";
    } else {
      header.style.background = "rgba(255, 255, 255, 0.95)";
      header.style.borderBottom = "1px solid var(--border-light)";
    }
  });
}

// Mobile menu toggle (placeholder for future implementation)
function initializeMobileMenu() {
  const mobileMenuBtn = document.querySelector(".mobile-menu-btn");
  const navLinks = document.querySelector(".nav-links");

  if (mobileMenuBtn) {
    mobileMenuBtn.addEventListener("click", function () {
      // Future mobile menu implementation
      console.log("Mobile menu toggle");
    });
  }
}

// Dropdown menu functionality
function initializeDropdowns() {
  const dropdownToggles = document.querySelectorAll(".dropdown-toggle");

  dropdownToggles.forEach((toggle) => {
    // Prevent default link behavior
    toggle.addEventListener("click", function (e) {
      e.preventDefault();
    });

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

// Shopping Details Modal Functions
async function openShoppingDetails(cartId) {
  console.log("Opening shopping details for cart:", cartId);

  const modal = document.getElementById("shoppingModal");
  const itemsContainer = document.getElementById("itemsContainer");

  // Show modal with loading state
  showModal();
  resetModalContent();

  try {
    const response = await fetch(
      `/api/shopping-trip/details?cart_id=${cartId}`
    );

    if (response.ok) {
      const data = await response.json();
      console.log("Received data:", data);
      populateModal(data);
    } else {
      console.error("Failed to load shopping details:", response.status);
      showErrorState("Failed to load shopping trip details. Please try again.");
    }
  } catch (error) {
    console.error("Error loading shopping details:", error);
    showErrorState(
      "Unable to connect to server. Please check your connection and try again."
    );
  }
}

function showModal() {
  const modal = document.getElementById("shoppingModal");
  modal.style.display = "flex";
  // Trigger animation
  setTimeout(() => {
    modal.classList.add("show");
  }, 10);

  // Prevent body scroll
  document.body.style.overflow = "hidden";

  // Close modal when clicking overlay
  modal.onclick = function (e) {
    if (e.target === modal) {
      closeShoppingModal();
    }
  };

  // Close modal with Escape key
  document.addEventListener("keydown", handleEscapeKey);
}

function closeShoppingModal() {
  const modal = document.getElementById("shoppingModal");
  modal.classList.remove("show");

  // Wait for animation to complete before hiding
  setTimeout(() => {
    modal.style.display = "none";
    document.body.style.overflow = "";
  }, 300);

  // Remove event listener
  document.removeEventListener("keydown", handleEscapeKey);
}

function handleEscapeKey(e) {
  if (e.key === "Escape") {
    closeShoppingModal();
  }
}

function resetModalContent() {
  document.getElementById("modalTitle").textContent = "Shopping Trip Details";
  document.getElementById("modalDate").textContent = "";
  document.getElementById("modalStoreName").textContent = "-";
  document.getElementById("modalTotalAmount").textContent = "$0.00";
  document.getElementById("modalTotalItems").textContent = "0";

  const itemsContainer = document.getElementById("itemsContainer");
  itemsContainer.innerHTML = `
    <div class="loading-state">
        <i class="fas fa-spinner fa-spin"></i>
        <p>Loading shopping trip details...</p>
    </div>
    `;
}

function populateModal(data) {
  // Format date
  const date = new Date(data.created_at);
  const formattedDate = date.toLocaleDateString("en-US", {
    weekday: "long",
    year: "numeric",
    month: "long",
    day: "numeric",
  });
  const formattedTime = date.toLocaleTimeString("en-US", {
    hour: "2-digit",
    minute: "2-digit",
  });

  // Update modal content
  document.getElementById(
    "modalTitle"
  ).textContent = `${data.store_name} Shopping Trip`;
  document.getElementById(
    "modalDate"
  ).textContent = `${formattedDate} at ${formattedTime}`;
  document.getElementById("modalStoreName").textContent = data.store_name;
  document.getElementById("modalTotalAmount").textContent = `$${Number(
    data.total_amount
  ).toFixed(2)}`;
  document.getElementById(
    "modalTotalItems"
  ).textContent = `${data.total_items}`;

  // Populate items
  const itemsContainer = document.getElementById("itemsContainer");

  if (!data.items || data.items.length === 0) {
    itemsContainer.innerHTML = `
        <div class="empty-state">
        <i class="fas fa-shopping-cart"></i>
        <h3>No Items Found</h3>
        <p>This shopping trip doesn't have any recorded items.</p>
        </div>
    `;
    return;
  }

  itemsContainer.innerHTML = "";

  data.items.forEach((item) => {
    const itemCard = document.createElement("div");
    itemCard.className = "item-card";

    const itemTotal = Number(item.price * item.quantity).toFixed(2);
    const imageUrl =
      item.image_url ||
      "https://images.unsplash.com/photo-1523294587484-bae6cc870010?w=60&h=60&fit=crop&crop=center";

    itemCard.innerHTML = `
        <img src="${imageUrl}" 
            alt="${item.item_name}" 
            class="item-image" 
            onerror="this.src='https://images.unsplash.com/photo-1523294587484-bae6cc870010?w=60&h=60&fit=crop&crop=center'">
        <div class="item-details">
        <div class="item-name" title="${item.item_name}">${item.item_name}</div>
        <div class="item-quantity">Qty: ${item.quantity}</div>
        <div class="item-price">$${item.price} each</div>
        </div>
        <div class="item-total">$${itemTotal}</div>
    `;

    itemsContainer.appendChild(itemCard);
  });
}

function showErrorState(message) {
  const itemsContainer = document.getElementById("itemsContainer");
  itemsContainer.innerHTML = `
    <div class="error-state">
        <i class="fas fa-exclamation-triangle"></i>
        <h3>Unable to Load Details</h3>
        <p>${message}</p>
    </div>
    `;
}

// Load More History Functionality
let currentOffset = 15; // We already loaded 15 trips
const maxTrips = JSON.parse("{{ total_trips|default(0) }}");

async function loadMoreHistory() {
  const showMoreBtn = document.getElementById("showMoreBtn");
  const showLessBtn = document.getElementById("showLessBtn");
  const tableBody = document.getElementById("historyTableBody");

  // Show loading state
  showMoreBtn.disabled = true;
  showMoreBtn.innerHTML =
    '<i class="fas fa-spinner fa-spin" aria-hidden="true"></i> Loading...';

  try {
    const response = await fetch(
      `/api/shopping-history?offset=${currentOffset}&limit=35`
    );

    if (response.ok) {
      const data = await response.json();

      // Add new rows to the table with a class to identify them as additional
      data.history.forEach((cart) => {
        const row = document.createElement("tr");
        row.className = "clickable-row additional-history";
        row.setAttribute("data-cart-id", cart.cart_ID);

        // Format the date
        const date = new Date(cart.created_at);
        const formattedDate = date.toLocaleDateString("en-US", {
          month: "2-digit",
          day: "2-digit",
          year: "2-digit",
        });

        row.innerHTML = `
            <td>
            <div style="display: flex; align-items: center; gap: 8px;">
                <i class="fas fa-store" style="color: var(--primary-color);"></i>
                ${cart.store_name}
            </div>
            </td>
            <td>
            <div style="display: flex; align-items: center; gap: 8px;">
                <i class="fas fa-calendar-alt" style="color: var(--text-secondary);"></i>
                ${formattedDate}
            </div>
            </td>
            <td>
            <span class="cart-badge">
                <i class="fas fa-shopping-basket" aria-hidden="true"></i>
                ${cart.total_items} items
            </span>
            </td>
            <td>
            <span class="amount">$${cart.total_spent}</span>
            </td>
        `;

        // Add click handler to the new row
        row.addEventListener("click", function () {
          const cartId = this.getAttribute("data-cart-id");
          if (cartId) {
            openShoppingDetails(cartId);
          }
        });

        tableBody.appendChild(row);
      });

      currentOffset += data.history.length;

      // Show the "Show Less" button
      showLessBtn.style.display = "inline-flex";

      // Update or hide the "Show More" button
      if (currentOffset >= maxTrips) {
        showMoreBtn.style.display = "none";
      } else {
        showMoreBtn.disabled = false;
        showMoreBtn.innerHTML = `
            <i class="fas fa-chevron-down" aria-hidden="true"></i>
            Show More
        `;
      }
    } else {
      console.error("Failed to load more history");
      showMoreBtn.disabled = false;
      showMoreBtn.innerHTML =
        '<i class="fas fa-chevron-down" aria-hidden="true"></i> Show More';
    }
  } catch (error) {
    console.error("Error loading more history:", error);
    showMoreBtn.disabled = false;
    showMoreBtn.innerHTML =
      '<i class="fas fa-chevron-down" aria-hidden="true"></i> Show More';
  }
}

function showLessHistory() {
  const showMoreBtn = document.getElementById("showMoreBtn");
  const showLessBtn = document.getElementById("showLessBtn");
  const tableBody = document.getElementById("historyTableBody");

  // Remove all additional history rows
  const additionalRows = tableBody.querySelectorAll(".additional-history");
  additionalRows.forEach((row) => row.remove());

  // Reset the offset to 15
  currentOffset = 15;

  // Hide the "Show Less" button
  showLessBtn.style.display = "none";

  // Show and reset the "Show More" button
  showMoreBtn.style.display = "inline-flex";
  showMoreBtn.disabled = false;
  showMoreBtn.innerHTML = `
    <i class="fas fa-chevron-down" aria-hidden="true"></i>
    Show More
    `;
}

// Initialize Shopping History Click Handlers
function initializeShoppingHistory() {
  // Add click handlers to existing rows
  document.querySelectorAll(".clickable-row").forEach((row) => {
    row.addEventListener("click", function () {
      const cartId = this.getAttribute("data-cart-id");
      if (cartId) {
        openShoppingDetails(cartId);
      }
    });
  });
}

// Load and display today's meals
async function loadTodaysMeals() {
  try {
    const today = new Date().toISOString().split("T")[0];
    const response = await fetch(
      `/api/meals?start_date=${today}&end_date=${today}`
    );
    const data = await response.json();

    const loadingDiv = document.getElementById("mealsLoading");
    const noMealsDiv = document.getElementById("noMealsToday");
    const mealsGrid = document.getElementById("todaysMealsGrid");

    loadingDiv.style.display = "none";

    if (data.success && data.meals && data.meals.length > 0) {
      displayTodaysMeals(data.meals);
      noMealsDiv.style.display = "none";
      mealsGrid.style.display = "grid";
    } else {
      noMealsDiv.style.display = "block";
      mealsGrid.style.display = "none";
    }
  } catch (error) {
    console.error("Error loading today's meals:", error);
    document.getElementById("mealsLoading").style.display = "none";
    document.getElementById("noMealsToday").style.display = "block";
    document.getElementById("todaysMealsGrid").style.display = "none";
  }
}

function displayTodaysMeals(meals) {
  const grid = document.getElementById("todaysMealsGrid");
  grid.innerHTML = "";

  // Sort meals by meal type order
  const mealTypeOrder = { breakfast: 1, lunch: 2, dinner: 3, snack: 4 };
  meals.sort(
    (a, b) => (mealTypeOrder[a.type] || 5) - (mealTypeOrder[b.type] || 5)
  );

  meals.forEach((meal) => {
    const mealItem = document.createElement("div");
    mealItem.className = `meal-item ${meal.type} ${
      meal.is_completed ? "completed" : ""
    }`;

    const dishName = getDishName(meal);
    const totalTime = (meal.prep_time || 0) + (meal.cook_time || 0);

    mealItem.innerHTML = `
        <div class="meal-header">
        <span class="meal-type-badge ${meal.type}">${meal.type}</span>
        <div class="meal-content">
            <div class="meal-main-info">
            <div class="meal-name" onclick="showMealDetails(${
              meal.meal_id
            })">${dishName}</div>
            </div>
            <div class="meal-info">
            ${
              totalTime > 0
                ? `<span><i class="fas fa-clock"></i> ${totalTime} min</span>`
                : ""
            }
            ${
              meal.servings
                ? `<span><i class="fas fa-users"></i> ${meal.servings} servings</span>`
                : ""
            }
            ${
              meal.difficulty
                ? `<span><i class="fas fa-chart-line"></i> ${meal.difficulty}</span>`
                : ""
            }
            </div>
        </div>
        </div>
        <label class="meal-completion-checkbox">
        <input type="checkbox" ${meal.is_completed ? "checked" : ""} 
                onchange="toggleMealCompletion(${
                  meal.meal_id
                }, this.checked, this, '${meal.date}')">
        </label>
    `;

    grid.appendChild(mealItem);
  });
}

function getDishName(meal) {
  // Extract actual dish name from meal name
  if (meal.name && meal.name.includes(":")) {
    return meal.name.split(":").slice(1).join(":").trim();
  }
  return meal.name || `Custom ${meal.type}`;
}

async function toggleMealCompletion(
  mealId,
  isCompleted,
  checkbox,
  mealDate = null
) {
  // Prevent completing future meals
  if (mealDate) {
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const checkDate = new Date(mealDate);
    checkDate.setHours(0, 0, 0, 0);

    if (checkDate > today) {
      alert("You can only complete meals for today or past dates.");
      checkbox.checked = !isCompleted;
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
      // Update the meal item appearance
      const mealItem = checkbox.closest(".meal-item");
      if (isCompleted) {
        mealItem.classList.add("completed");
      } else {
        mealItem.classList.remove("completed");
      }

      // Update the monthly progress wheel
      if (typeof loadMonthlyProgress === "function") {
        loadMonthlyProgress();
      }
    } else {
      // Revert checkbox on error
      checkbox.checked = !isCompleted;
      alert("Failed to update meal completion: " + data.message);
    }
  } catch (error) {
    console.error("Error updating meal completion:", error);
    checkbox.checked = !isCompleted;
    alert("Failed to update meal completion. Please try again.");
  }
}

async function showMealDetails(mealId) {
  try {
    const response = await fetch(`/api/meals/${mealId}`);
    const data = await response.json();

    if (data.success) {
      // For now, just navigate to meal plans page
      // In the future, this could open a modal with meal details
      window.location.href = '{{ url_for("shopping.meal_plans") }}';
    } else {
      alert("Failed to load meal details: " + data.message);
    }
  } catch (error) {
    console.error("Error loading meal details:", error);
    alert("Failed to load meal details. Please try again.");
  }
}

// Monthly Meals Progress Wheel Functionality
async function loadMonthlyProgress() {
  try {
    const currentMonth = new Date().getMonth() + 1;
    const currentYear = new Date().getFullYear();

    // Update the month display
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
    document.getElementById("progressMonth").textContent = `${
      monthNames[currentMonth - 1]
    } ${currentYear}`;

    // Get goals and progress data
    const [goalsResponse, progressResponse] = await Promise.all([
      fetch(`/api/meal-goals?month=${currentMonth}&year=${currentYear}`),
      fetch(
        `/api/meal-goals/progress?month=${currentMonth}&year=${currentYear}`
      ),
    ]);

    const goalsData = await goalsResponse.json();
    const progressData = await progressResponse.json();

    if (goalsData.success && progressData.success) {
      const goal = goalsData.goals.meals_completed_goal;
      const completed = progressData.progress.completed_meals_count;

      updateProgressWheel(completed, goal);
    } else {
      // Use default values if API fails
      updateProgressWheel(0, 60);
    }
  } catch (error) {
    console.error("Error loading monthly progress:", error);
    // Use default values on error
    updateProgressWheel(0, 60);
  }
}

function updateProgressWheel(completed, goal) {
  const percentage = Math.min((completed / goal) * 100, 100);
  const remaining = Math.max(goal - completed, 0);

  // Update the progress circle
  const circle = document.getElementById("progressCircle");
  const circumference = 2 * Math.PI * 90; // radius = 90
  const dashArray = (percentage / 100) * circumference;
  circle.style.strokeDasharray = `${dashArray} ${circumference}`;

  // Update text elements
  document.getElementById("progressPercentage").textContent = `${Math.round(
    percentage
  )}%`;
  document.getElementById("completedMeals").textContent = completed;
  document.getElementById("goalTarget").textContent = goal;
  document.getElementById("remainingMeals").textContent = remaining;

  // Update progress circle color based on completion
  if (percentage >= 100) {
    circle.style.stroke = "var(--success-color)";
    document.getElementById("progressPercentage").style.color =
      "var(--success-color)";
  } else if (percentage >= 75) {
    circle.style.stroke = "var(--primary-color)";
    document.getElementById("progressPercentage").style.color =
      "var(--primary-color)";
  } else if (percentage >= 50) {
    circle.style.stroke = "var(--warning-color)";
    document.getElementById("progressPercentage").style.color =
      "var(--warning-color)";
  } else {
    circle.style.stroke = "var(--error-color)";
    document.getElementById("progressPercentage").style.color =
      "var(--error-color)";
  }
}

// Initialize all functionality
document.addEventListener("DOMContentLoaded", function () {
  updateWelcomeMessage();
  animateStats();
  initializeCarousel();
  initializeHoverEffects();
  initializeScrollEffects();
  initializeMobileMenu();
  initializeDropdowns();
  handleDropdownResize();
  initializeShoppingHistory();
  loadTodaysMeals();
  loadMonthlyProgress();

  // Update time-based greeting every minute
  setInterval(updateWelcomeMessage, 60000);
});
