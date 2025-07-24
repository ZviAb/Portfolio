document.addEventListener('DOMContentLoaded', function () {
  // Initialize Lucide icons
  lucide.createIcons();
  
  // Check if user is logged in
  const token = localStorage.getItem('auth_token');
  const userInfo = JSON.parse(localStorage.getItem('user_info') || '{}');
  
  // Update UI based on login status
  updateAuthUI(token, userInfo);
  
  // Add event listeners for primary buttons (Get Started) - but only for buttons without onclick
  document.querySelectorAll('.btn-primary').forEach(btn => {
    // Skip buttons that already have onclick handlers
    if (btn.getAttribute('onclick')) {
      return;
    }
    
    btn.addEventListener('click', () => {
      if (token) {
        window.location.href = '/dashboard';
      } else {
        window.location.href = '/register';
      }
    });
  });
  
  // Add event listeners for secondary buttons and login buttons - but only for buttons without onclick
  document.querySelectorAll('.btn-secondary, .login-btn').forEach(btn => {
    // Skip buttons that already have onclick handlers
    if (btn.getAttribute('onclick')) {
      return;
    }
    
    btn.addEventListener('click', () => {
      window.location.href = '/login';
    });
  });
  
  // Add event listeners for footer primary buttons (Sign Up)
  document.querySelectorAll('.btn-footer-primary').forEach(btn => {
    btn.addEventListener('click', () => {
      window.location.href = '/register';
    });
  });
  
  // Add event listeners for footer secondary buttons
  document.querySelectorAll('.btn-footer-secondary').forEach(btn => {
    btn.addEventListener('click', () => {
      window.location.href = '/dashboard';
    });
  });
});

function updateAuthUI(token, userInfo) {
  const loginBtn = document.querySelector('.login-btn');
  const userSection = document.querySelector('.user-info');
  const userName = document.querySelector('.user-name');
  
  if (token && userInfo.full_name) {
    // User is logged in
    loginBtn.style.display = 'none';
    userSection.style.display = 'flex';
    userName.textContent = userInfo.full_name;
    userName.style.display = 'inline';
    
    // Setup dropdown menu for logged in users
    setupUserDropdown();
    
    // Update hero section for logged in users
    updateHeroForLoggedInUser(userInfo.first_name);
  } else {
    // User not logged in - show login button and guest
    loginBtn.style.display = 'block';
    userSection.style.display = 'flex';
    userName.textContent = 'Guest';
    userName.style.display = 'inline';
    userName.style.visibility = 'visible';
  }
}

function updateHeroForLoggedInUser(firstName) {
  const heroTitle = document.getElementById('heroTitle');
  const heroDescription = document.getElementById('heroDescription');
  const heroButtons = document.getElementById('heroButtons');
  
  if (heroTitle && heroDescription && heroButtons) {
    heroTitle.textContent = `Welcome back, ${firstName}!`;
    heroDescription.textContent = 'Ready to create new quizzes or take on some challenges? Your learning journey continues here.';
    
    // Update buttons for logged in users
    heroButtons.innerHTML = `
      <button class="btn-primary" onclick="window.location.href='/dashboard'">Go to Dashboard</button>
      <button class="btn-secondary" onclick="window.location.href='/create-quiz'">Create Quiz</button>
    `;
  }
}

function logout() {
  localStorage.removeItem('auth_token');
  localStorage.removeItem('user_info');
  showNotification('Logged out successfully', 'You have been logged out.', 'success');
  setTimeout(() => {
    window.location.reload();
  }, 1500);
}

// Notification System
function showNotification(title, message, type = 'info') {
  // Remove existing notifications
  const existingNotifications = document.querySelectorAll('.notification');
  existingNotifications.forEach(notif => notif.remove());
  
  const notification = document.createElement('div');
  notification.className = `notification notification-${type}`;
  
  notification.innerHTML = `
    <div class="notification-title">${title}</div>
    <div class="notification-message">${message}</div>
  `;
  
  document.body.appendChild(notification);
  
  // Show notification
  setTimeout(() => {
    notification.classList.add('show');
  }, 100);
  
  // Auto hide after 4 seconds
  setTimeout(() => {
    notification.classList.remove('show');
    setTimeout(() => {
      notification.remove();
    }, 300);
  }, 4000);
}

// Dropdown functionality
function setupUserDropdown() {
  const userName = document.querySelector('.user-name');
  const userSection = document.querySelector('.user-info');
  
  if (!userName || !userSection) return;
  
  // Create dropdown menu
  const dropdownMenu = document.createElement('div');
  dropdownMenu.className = 'dropdown-menu';
  dropdownMenu.innerHTML = `
    <a href="/dashboard" class="dropdown-item">Dashboard</a>
    <a href="/profile" class="dropdown-item">Profile</a>
    <a href="/my-quizzes" class="dropdown-item">My Quizzes</a>
    <a href="/browse-quizzes" class="dropdown-item">Browse All Quizzes</a>
    <button class="dropdown-item" onclick="logout()">Logout</button>
  `;
  
  // Add dropdown wrapper
  const dropdownWrapper = document.createElement('div');
  dropdownWrapper.className = 'user-dropdown';
  
  // Move user-info into dropdown wrapper
  userSection.parentNode.insertBefore(dropdownWrapper, userSection);
  dropdownWrapper.appendChild(userSection);
  dropdownWrapper.appendChild(dropdownMenu);
  
  // Add hover events to show/hide dropdown
  dropdownWrapper.addEventListener('mouseenter', () => {
    dropdownMenu.classList.add('show');
  });
  
  dropdownWrapper.addEventListener('mouseleave', () => {
    dropdownMenu.classList.remove('show');
  });
}

// Global function to setup dropdown on any page
function initializeDropdown() {
  const token = localStorage.getItem('auth_token');
  const userInfo = JSON.parse(localStorage.getItem('user_info') || '{}');
  
  if (token && userInfo.full_name) {
    const userName = document.querySelector('.user-name');
    if (userName && userName.textContent !== userInfo.full_name) {
      userName.textContent = userInfo.full_name;
      userName.style.display = 'inline';
      setupUserDropdown();
    }
  }
}