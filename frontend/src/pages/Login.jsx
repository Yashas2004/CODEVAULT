import { useState } from "react";
import api from "../api";
import { useNavigate, Link } from "react-router-dom";

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();
    setError("");
    try {
      const form = new URLSearchParams();
      form.append("username", email);
      form.append("password", password);
      const res = await api.post("/users/login", form);
      localStorage.setItem("token", res.data.access_token);
      navigate("/snippets");
    } catch {
      setError("Invalid email or password.");
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-paper px-4">
      <div className="w-full max-w-lg bg-surface border border-comment/20 rounded-2xl p-10 space-y-8 shadow-[0_0_40px_-12px_theme(colors.accent)]">
        <div className="text-center space-y-2">
          <div className="flex items-center justify-center gap-3 font-mono font-bold text-5xl">
            <span className="text-accent">&lt;/&gt;</span>
            <span className="text-ink tracking-tight">CodeVault</span>
          </div>
          <p className="text-sm font-mono text-comment">sign in to your vault</p>
        </div>

        <form onSubmit={handleLogin} className="space-y-4">
          <input
            className="border border-comment/20 bg-surface2 text-ink rounded-lg px-4 py-3 w-full text-base outline-none focus:ring-2 focus:ring-accent/50 placeholder:text-comment"
            placeholder="Email"
            value={email} onChange={e => setEmail(e.target.value)}
          />
          <input
            className="border border-comment/20 bg-surface2 text-ink rounded-lg px-4 py-3 w-full text-base outline-none focus:ring-2 focus:ring-accent/50 placeholder:text-comment"
            type="password"
            placeholder="Password"
            value={password} onChange={e => setPassword(e.target.value)}
          />
          {error && <p className="text-danger text-sm font-mono text-center">{error}</p>}
          <button className="bg-accent text-paper rounded-lg px-4 py-3 w-full text-base font-semibold hover:brightness-110 transition">
            Sign In
          </button>
        </form>

        <p className="text-sm text-comment text-center">
          No account? <Link to="/register" className="text-accent hover:underline">Register</Link>
        </p>
      </div>
    </div>
  );
}