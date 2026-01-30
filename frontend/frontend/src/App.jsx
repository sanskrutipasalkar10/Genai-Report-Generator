import { BrowserRouter as Router, Routes, Route, useLocation } from 'react-router-dom';
import { AnimatePresence } from 'framer-motion';
import Home from './pages/Home';       
import Dashboard from './pages/Dashboard'; 
import './App.css'; // This loads your Princity-style CSS

// Wrapper to handle animations
function AnimatedRoutes() {
  const location = useLocation();

  return (
    <AnimatePresence mode="wait">
      <Routes location={location} key={location.pathname}>
        {/* The Landing Page */}
        <Route path="/" element={<Home />} />
        
        {/* The Generator App */}
        <Route path="/app" element={<Dashboard />} />
      </Routes>
    </AnimatePresence>
  );
}

function App() {
  return (
    <Router>
      <AnimatedRoutes />
    </Router>
  );
}

export default App;