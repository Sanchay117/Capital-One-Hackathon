import React, { useState } from 'react';

// Import all the components that will act as "pages"
import AgriAdvisorApp from './components/AgriAdvisorApp';
import LoginPage from './components/Auth/LoginPage';
import SignupPage from './components/Auth/SignupPage';

function App() {
  // 'isAuthenticated' determines if we show the login flow or the main app.
  // 'currentView' switches between 'login' and 'signup'.
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [currentView, setCurrentView] = useState('login');

  // This function will be passed to LoginPage and called on a successful login
  const handleLoginSuccess = () => {
    setIsAuthenticated(true);
  };

  // This function toggles between the Login and Signup forms
  const toggleView = () => {
    setCurrentView(currentView === 'login' ? 'signup' : 'login');
  };

  // Conditional Rendering Logic
  if (isAuthenticated) {
    // If the user is logged in, show the main Agri-Advisor application
    return <AgriAdvisorApp />;
  } else {
    // If not logged in, show either the Login or Signup page
    switch (currentView) {
      case 'login':
        return <LoginPage onToggleView={toggleView} onLoginSuccess={handleLoginSuccess} />;
      case 'signup':
        return <SignupPage onToggleView={toggleView} />;
      default:
        return <LoginPage onToggleView={toggleView} onLoginSuccess={handleLoginSuccess} />;
    }
  }
}

export default App;
