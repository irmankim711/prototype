// Common navigation functionality for all pages
document.addEventListener('DOMContentLoaded', function() {
  // Add click event listeners for menu items
  document.querySelectorAll('.menu-item').forEach(item => {
    item.addEventListener('click', function() {
      // Skip if this item is already active
      if (this.classList.contains('active')) return;

      // Get the text content (menu name)
      const menuName = this.querySelector('.menu-text').textContent.trim();
      
      // Navigate based on menu name
      switch(menuName) {
        case 'Admin Dashboard':
          window.location.href = 'admin-dashboard.html';
          break;
        case 'Submission':
          window.location.href = 'submission.html';
          break;
        case 'Form':
          window.location.href = 'form.html';
          break;
        case 'Generate Report':
          window.location.href = 'generate-report.html';
          break;
        case 'Setting':
          window.location.href = 'settings.html';
          break;
        default:
          console.log('Unknown menu item:', menuName);
      }
    });
  });

  // Theme toggle functionality (if present on page)
  const themeSwitch = document.getElementById('theme-switch');
  if (themeSwitch) {
    const themeLabel = document.getElementById('theme-label');
    
    // Set initial state based on localStorage
    if (localStorage.getItem('theme') === 'dark') {
      document.body.classList.add('dark-theme');
      themeSwitch.checked = true;
      if (themeLabel) themeLabel.textContent = 'Dark Mode';
    }
    
    // Add change listener
    themeSwitch.addEventListener('change', function() {
      if (this.checked) {
        document.body.classList.add('dark-theme');
        localStorage.setItem('theme', 'dark');
        if (themeLabel) themeLabel.textContent = 'Dark Mode';
      } else {
        document.body.classList.remove('dark-theme');
        localStorage.setItem('theme', 'light');
        if (themeLabel) themeLabel.textContent = 'Light Mode';
      }
    });
  }
});
