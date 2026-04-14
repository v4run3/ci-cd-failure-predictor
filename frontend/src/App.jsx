import { useState, useEffect } from "react";
import { Routes, Route } from "react-router-dom";
import Sidebar from "./components/Sidebar";
import Dashboard from "./pages/Dashboard";
import Predict from "./pages/Predict";
import History from "./pages/History";
import "./App.css";

function App() {
  const [dark, setDark] = useState(() => {
    return localStorage.getItem("theme") === "dark";
  });
  const [predictions, setPredictions] = useState(() => {
    const saved = localStorage.getItem("predictions");
    return saved ? JSON.parse(saved) : [];
  });

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", dark ? "dark" : "light");
    localStorage.setItem("theme", dark ? "dark" : "light");
  }, [dark]);

  useEffect(() => {
    localStorage.setItem("predictions", JSON.stringify(predictions));
  }, [predictions]);

  const addPrediction = (entry) => {
    setPredictions((prev) => [entry, ...prev].slice(0, 100));
  };

  return (
    <div className="app-layout">
      <Sidebar dark={dark} setDark={setDark} />
      <main className="main-content">
        <Routes>
          <Route path="/" element={<Dashboard predictions={predictions} />} />
          <Route path="/predict" element={<Predict onPrediction={addPrediction} />} />
          <Route path="/history" element={<History predictions={predictions} />} />
        </Routes>
      </main>
    </div>
  );
}

export default App;
