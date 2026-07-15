// frontend/src/App.jsx
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Snippets from "./pages/Snippets";
import SharedSnippet from "./pages/SharedSnippet";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Navigate to="/login" />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/snippets" element={<Snippets />} />
        <Route path="/s/:slug" element={<SharedSnippet />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;