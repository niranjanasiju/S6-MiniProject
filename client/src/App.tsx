import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Landing from './pages/Landing';
import PolypharmacyPredictor from './pages/PolypharmacyPredictor';
import ADRPredictor from './pages/ADRPredictor';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Landing />} />
          <Route path="polypharmacy" element={<PolypharmacyPredictor />} />
          <Route path="adr" element={<ADRPredictor />} />
        </Route>
      </Routes>
    </Router>
  );
}

export default App;
