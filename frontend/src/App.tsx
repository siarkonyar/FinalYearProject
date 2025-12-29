import { Routes, Route } from "react-router-dom";
import Home from "./Home";

function App() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      {/* Add more routes as needed */}
    </Routes>
  );
}

export default App;
