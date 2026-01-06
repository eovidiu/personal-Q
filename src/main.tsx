import React from "react";
import * as ReactDOM from "react-dom";
import { createRoot } from "react-dom/client";
import App from "./App";
import "./index.css";

console.log("=== Personal-Q Frontend Starting ===");

// Make React and ReactDOM globally available immediately (not in useEffect)
window.React = React;
window.ReactDOM = ReactDOM;

function Main() {
  console.log("Main component rendering");
  return (
    <React.StrictMode>
      <App />
    </React.StrictMode>
  );
}

try {
  const rootElement = document.getElementById("root");
  if (!rootElement) {
    throw new Error("Root element not found");
  }
  console.log("Creating React root...");
  const root = createRoot(rootElement);
  console.log("Rendering app...");
  root.render(<Main />);
  console.log("App rendered successfully");
} catch (error) {
  console.error("Failed to mount React app:", error);
  document.body.innerHTML = `<div style="padding: 20px; color: red;">
    <h1>Error loading application</h1>
    <pre>${error}</pre>
  </div>`;
}

// If you want to start measuring performance in your app, pass a function
// to log results (for example: reportWebVitals(console.log))
// or send to an analytics endpoint. Learn more: https://bit.ly/CRA-vitals
