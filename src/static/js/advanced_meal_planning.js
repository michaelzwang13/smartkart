// ============================================================================
// ADVANCED MEAL PLANNING PAGE FUNCTIONALITY
// ============================================================================

let chatbotState = {
  pantryItems: [],
  foodRestrictions: [''],
  isLoading: false
};

// Initialize page functionality
document.addEventListener("DOMContentLoaded", function () {
  initializeChatbot();
});

// ============================================================================
// CHATBOT FUNCTIONALITY
// ============================================================================

function initializeChatbot() {
  const chatInput = document.getElementById('chatInput');
  const sendBtn = document.getElementById('chatSendBtn');
  
  if (!chatInput || !sendBtn) return;

  // Chat input functionality
  chatInput.addEventListener('input', updateSendButton);
  chatInput.addEventListener('keypress', handleChatKeyPress);
  sendBtn.addEventListener('click', sendChatMessage);
  
  // Auto-resize textarea
  chatInput.addEventListener('input', autoResizeTextarea);
  
  // Suggestion buttons
  initializeSuggestionButtons();
  
  // Sidebar functionality
  initializeSidebar();
  
  // Load pantry items
  loadPantryItems();
}

function updateSendButton() {
  const chatInput = document.getElementById('chatInput');
  const sendBtn = document.getElementById('chatSendBtn');
  
  if (chatInput && sendBtn) {
    const hasText = chatInput.value.trim().length > 0;
    sendBtn.disabled = !hasText || chatbotState.isLoading;
  }
}

function handleChatKeyPress(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendChatMessage();
  }
}

function autoResizeTextarea() {
  const chatInput = document.getElementById('chatInput');
  if (!chatInput) return;
  
  chatInput.style.height = 'auto';
  chatInput.style.height = Math.min(chatInput.scrollHeight, 120) + 'px';
}

function sendChatMessage() {
  const chatInput = document.getElementById('chatInput');
  const message = chatInput?.value.trim();
  
  if (!message || chatbotState.isLoading) return;
  
  // Add user message to chat
  addMessageToChat(message, 'user');
  
  // Clear input
  chatInput.value = '';
  updateSendButton();
  autoResizeTextarea();
  
  // Set loading state
  chatbotState.isLoading = true;
  updateSendButton();
  
  // Show typing indicator
  showTypingIndicator();
  
  // Send message to backend
  sendMessageToAPI(message)
    .then(response => {
      hideTypingIndicator();
      
      if (response.success) {
        addMessageToChat(response.response, 'assistant');
        
        // Update suggestions if provided
        if (response.suggestions && response.suggestions.length > 0) {
          updateSuggestionButtons(response.suggestions);
        }
        
        // Handle action required (e.g., ready to generate meal plan)
        if (response.action_required && response.meal_plan_data) {
          handleMealPlanGeneration(response.meal_plan_data);
        }
      } else {
        addMessageToChat(response.message || "Sorry, I encountered an error. Please try again.", 'assistant');
      }
      
      chatbotState.isLoading = false;
      updateSendButton();
    })
    .catch(error => {
      hideTypingIndicator();
      console.error('Chat API error:', error);
      addMessageToChat("Sorry, I'm having trouble connecting right now. Please check your connection and try again.", 'assistant');
      chatbotState.isLoading = false;
      updateSendButton();
    });
}

function addMessageToChat(message, sender) {
  const chatMessages = document.getElementById('chatMessages');
  if (!chatMessages) return;
  
  const messageDiv = document.createElement('div');
  messageDiv.className = `message ${sender}-message`;
  
  const avatar = sender === 'user' ? '<i class="fas fa-user"></i>' : '<i class="fas fa-robot"></i>';
  
  messageDiv.innerHTML = `
    <div class="message-avatar">${avatar}</div>
    <div class="message-content">
      <p>${message}</p>
    </div>
  `;
  
  chatMessages.appendChild(messageDiv);
  
  // Scroll to bottom
  chatMessages.scrollTop = chatMessages.scrollHeight;
  
  // Add entrance animation
  messageDiv.style.opacity = '0';
  messageDiv.style.transform = 'translateY(20px)';
  setTimeout(() => {
    messageDiv.style.transition = 'all 0.3s ease';
    messageDiv.style.opacity = '1';
    messageDiv.style.transform = 'translateY(0)';
  }, 50);
}

function showTypingIndicator() {
  const chatMessages = document.getElementById('chatMessages');
  if (!chatMessages) return;
  
  const typingDiv = document.createElement('div');
  typingDiv.id = 'typingIndicator';
  typingDiv.className = 'message assistant-message';
  typingDiv.innerHTML = `
    <div class="message-avatar"><i class="fas fa-robot"></i></div>
    <div class="message-content">
      <p style="opacity: 0.6;">
        <i class="fas fa-circle" style="animation: pulse 1.5s ease-in-out infinite;"></i>
        <i class="fas fa-circle" style="animation: pulse 1.5s ease-in-out 0.5s infinite;"></i>
        <i class="fas fa-circle" style="animation: pulse 1.5s ease-in-out 1s infinite;"></i>
      </p>
    </div>
  `;
  
  chatMessages.appendChild(typingDiv);
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

function hideTypingIndicator() {
  const typingIndicator = document.getElementById('typingIndicator');
  typingIndicator?.remove();
}

function initializeSuggestionButtons() {
  const suggestionBtns = document.querySelectorAll('.suggestion-btn');
  
  suggestionBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const text = btn.getAttribute('data-text');
      const chatInput = document.getElementById('chatInput');
      
      if (chatInput && text) {
        chatInput.value = text;
        updateSendButton();
        autoResizeTextarea();
        chatInput.focus();
      }
    });
  });
}

// ============================================================================
// SIDEBAR FUNCTIONALITY
// ============================================================================

function initializeSidebar() {
  initializePantrySection();
  initializeFoodRestrictions();
  initializeDietaryPreferences();
}

function initializePantrySection() {
  const addPantryBtn = document.getElementById('addPantryBtn');
  addPantryBtn?.addEventListener('click', showAddPantryModal);
}

function loadPantryItems() {
  const pantryList = document.getElementById('pantryItemsList');
  if (!pantryList) return;
  
  // Show loading state
  pantryList.innerHTML = '<div style="text-align: center; color: var(--text-muted); padding: 1rem;"><i class="fas fa-spinner fa-spin"></i> Loading pantry items...</div>';
  
  fetch('/api/pantry/items')
    .then(response => response.json())
    .then(data => {
      if (data.success) {
        chatbotState.pantryItems = data.items || [];
        renderPantryItems();
      } else {
        pantryList.innerHTML = '<div style="text-align: center; color: var(--text-muted); padding: 1rem;">No pantry items found</div>';
      }
    })
    .catch(error => {
      console.error('Error loading pantry items:', error);
      pantryList.innerHTML = '<div style="text-align: center; color: var(--error-color); padding: 1rem;">Error loading pantry items</div>';
    });
}

function renderPantryItems() {
  const pantryList = document.getElementById('pantryItemsList');
  if (!pantryList) return;
  
  if (chatbotState.pantryItems.length === 0) {
    pantryList.innerHTML = '<div style="text-align: center; color: var(--text-muted); padding: 1rem;">No pantry items available</div>';
    return;
  }
  
  const itemsHTML = chatbotState.pantryItems
    .slice(0, 10) // Show only first 10 items to prevent overcrowding
    .map(item => `
      <div class="pantry-item">
        <div>
          <div class="pantry-item-name">${item.item_name}</div>
          <div class="pantry-item-amount">${item.quantity} ${item.unit || ''}</div>
        </div>
      </div>
    `).join('');
  
  pantryList.innerHTML = itemsHTML;
  
  if (chatbotState.pantryItems.length > 10) {
    pantryList.innerHTML += `<div style="text-align: center; color: var(--text-muted); font-size: 0.75rem; margin-top: 0.5rem;">+${chatbotState.pantryItems.length - 10} more items available</div>`;
  }
}

function showAddPantryModal() {
  showMessage('Pantry management coming soon! You can add items from the Pantry page.', 'info');
}

function initializeFoodRestrictions() {
  const addRestrictionBtn = document.getElementById('addRestrictionBtn');
  addRestrictionBtn?.addEventListener('click', addFoodRestriction);
  
  // Initialize existing restriction inputs
  updateRestrictionEventListeners();
}

function addFoodRestriction() {
  const restrictionsContainer = document.getElementById('foodRestrictions');
  if (!restrictionsContainer) return;
  
  const restrictionDiv = document.createElement('div');
  restrictionDiv.className = 'restriction-item';
  restrictionDiv.innerHTML = `
    <input type="text" placeholder="Block ingredients..." class="restriction-input" />
    <button class="btn-remove-restriction">
      <i class="fas fa-times"></i>
    </button>
  `;
  
  restrictionsContainer.appendChild(restrictionDiv);
  updateRestrictionEventListeners();
  
  // Focus on new input
  const newInput = restrictionDiv.querySelector('.restriction-input');
  newInput?.focus();
}

function updateRestrictionEventListeners() {
  const removeButtons = document.querySelectorAll('.btn-remove-restriction');
  
  removeButtons.forEach(btn => {
    btn.onclick = (e) => {
      const restrictionItem = e.target.closest('.restriction-item');
      const restrictionsContainer = document.getElementById('foodRestrictions');
      
      // Always keep at least one restriction input
      if (restrictionsContainer?.children.length > 1) {
        restrictionItem?.remove();
      } else {
        // Clear the input instead of removing it
        const input = restrictionItem?.querySelector('.restriction-input');
        if (input) input.value = '';
      }
    };
  });
}

function initializeDietaryPreferences() {
  const dietarySelect = document.getElementById('chatDietaryPreference');
  if (!dietarySelect) return;
  
  // Set default value
  dietarySelect.value = 'none';
}

function getFoodRestrictions() {
  const restrictionInputs = document.querySelectorAll('.restriction-input');
  const restrictions = [];
  
  restrictionInputs.forEach(input => {
    const value = input.value.trim();
    if (value) restrictions.push(value);
  });
  
  return restrictions;
}

function getDietaryPreference() {
  const dietarySelect = document.getElementById('chatDietaryPreference');
  return dietarySelect?.value || 'none';
}

// ============================================================================
// CHAT API INTEGRATION
// ============================================================================

function sendMessageToAPI(message) {
  const chatMessages = document.getElementById('chatMessages');
  const conversationHistory = [];
  
  // Build conversation history from current chat
  const messages = chatMessages.querySelectorAll('.message');
  messages.forEach(msg => {
    const isUser = msg.classList.contains('user-message');
    const content = msg.querySelector('.message-content p')?.textContent;
    if (content) {
      conversationHistory.push({
        sender: isUser ? 'user' : 'assistant',
        message: content
      });
    }
  });

  const payload = {
    message: message,
    pantry_items: chatbotState.pantryItems,
    food_restrictions: getFoodRestrictions(),
    dietary_preference: getDietaryPreference(),
    conversation_history: conversationHistory
  };

  return fetch('/api/advanced-meal-planning/chat', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload)
  })
  .then(response => response.json());
}

function updateSuggestionButtons(suggestions) {
  const suggestionContainer = document.querySelector('.chat-suggestions');
  if (!suggestionContainer || !suggestions.length) return;
  
  // Clear existing suggestions
  suggestionContainer.innerHTML = '';
  
  // Add new suggestions
  suggestions.forEach(suggestion => {
    const btn = document.createElement('button');
    btn.className = 'suggestion-btn';
    btn.textContent = suggestion;
    btn.setAttribute('data-text', suggestion);
    
    btn.addEventListener('click', () => {
      const chatInput = document.getElementById('chatInput');
      if (chatInput) {
        chatInput.value = suggestion;
        updateSendButton();
        autoResizeTextarea();
        chatInput.focus();
      }
    });
    
    suggestionContainer.appendChild(btn);
  });
}

function handleMealPlanGeneration(mealPlanData) {
  // Show confirmation dialog
  const confirmed = confirm('I have enough information to generate your meal plan. Would you like me to create it now?');
  
  if (confirmed) {
    // Redirect to meal plans page with parameters
    const params = new URLSearchParams();
    if (mealPlanData.start_date) params.set('start_date', mealPlanData.start_date);
    if (mealPlanData.days) params.set('days', mealPlanData.days);
    if (mealPlanData.dietary_preference) params.set('dietary_preference', mealPlanData.dietary_preference);
    if (mealPlanData.budget) params.set('budget', mealPlanData.budget);
    if (mealPlanData.cooking_time) params.set('cooking_time', mealPlanData.cooking_time);
    
    // Store additional context
    if (mealPlanData.food_restrictions || mealPlanData.ingredients) {
      sessionStorage.setItem('chatbotMealPlanContext', JSON.stringify({
        food_restrictions: mealPlanData.food_restrictions || [],
        preferred_ingredients: mealPlanData.ingredients || []
      }));
    }
    
    const url = `/meal-plans?${params.toString()}&auto_generate=true`;
    window.location.href = url;
  } else {
    addMessageToChat("No problem! Feel free to ask me any other questions about your meal plan.", 'assistant');
  }
}

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

function showMessage(message, type) {
  // Remove existing messages
  const existingMessages = document.querySelectorAll('.temp-message');
  existingMessages.forEach(msg => msg.remove());

  // Create message element
  const messageDiv = document.createElement('div');
  messageDiv.className = `temp-message ${type}`;
  messageDiv.style.cssText = `
    position: fixed;
    top: 100px;
    left: 50%;
    transform: translateX(-50%);
    padding: 15px 20px;
    border-radius: 8px;
    color: white;
    font-weight: 600;
    z-index: 10000;
    max-width: 400px;
    text-align: center;
    box-shadow: 0 4px 12px rgba(0,0,0,0.2);
  `;

  // Set background color based on type
  if (type === 'success') {
    messageDiv.style.background = '#10b981';
  } else if (type === 'info') {
    messageDiv.style.background = '#3b82f6';
  } else {
    messageDiv.style.background = '#ef4444';
  }

  let icon = 'fa-exclamation-triangle';
  if (type === 'success') icon = 'fa-check-circle';
  if (type === 'info') icon = 'fa-info-circle';

  messageDiv.innerHTML = `
    <i class="fas ${icon}"></i>
    ${message}
  `;

  document.body.appendChild(messageDiv);

  // Animate in
  messageDiv.style.opacity = '0';
  messageDiv.style.transform = 'translateX(-50%) translateY(-20px)';
  setTimeout(() => {
    messageDiv.style.transition = 'all 0.3s ease';
    messageDiv.style.opacity = '1';
    messageDiv.style.transform = 'translateX(-50%) translateY(0)';
  }, 10);

  // Remove after 5 seconds
  setTimeout(() => {
    messageDiv.style.opacity = '0';
    messageDiv.style.transform = 'translateX(-50%) translateY(-20px)';
    setTimeout(() => {
      messageDiv.remove();
    }, 300);
  }, 5000);
}