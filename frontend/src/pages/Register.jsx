import { useState } from "react";
import api from "../api";
import { useNavigate, Link } from "react-router-dom";

export default function Register() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const navigate = useNavigate();

  const passwordsMatch = password.length > 0 && password === confirmPassword;
  const canSubmit = email.length > 0 && passwordsMatch;

  const handleRegister = async (e) => {
    e.preventDefault();
    if (!canSubmit) return;
    setError("");
    try {
      await api.post("/users/register", { email, password });
      navigate("/login");
    } catch {
      setError("Could not register — email may already be in use.");
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-paper px-4">
      <div className="w-full max-w-sm bg-surface border border-comment/20 rounded-lg p-6 space-y-5">
        <div>
          <div className="flex items-center gap-2 font-mono font-semibold text-xl">
            <span className="text-accent">&lt;/&gt;</span>
            <span className="text-ink">CodeVault</span>
          </div>
          <p className="text-xs font-mono text-comment mt-1">create your vault</p>
        </div>

        <form onSubmit={handleRegister} className="space-y-3">
          <input
            className="border border-comment/20 bg-surface2 text-ink rounded px-3 py-2 w-full text-sm outline-none focus:ring-2 focus:ring-accent/50 placeholder:text-comment"
            placeholder="Email"
            value={email} onChange={e => setEmail(e.target.value)}
          />
          <input
            className="border border-comment/20 bg-surface2 text-ink rounded px-3 py-2 w-full text-sm outline-none focus:ring-2 focus:ring-accent/50 placeholder:text-comment"
            type="password"
            placeholder="Password"
            value={password} onChange={e => setPassword(e.target.value)}
          />
          <input
            className={`border bg-surface2 text-ink rounded px-3 py-2 w-full text-sm outline-none focus:ring-2 placeholder:text-comment ${
              confirmPassword.length > 0
                ? passwordsMatch
                  ? "border-success/50 focus:ring-success/50"
                  : "border-danger/50 focus:ring-danger/50"
                : "border-comment/20 focus:ring-accent/50"
            }`}
            type="password"
            placeholder="Confirm Password"
            value={confirmPassword} onChange={e => setConfirmPassword(e.target.value)}
          />
          {confirmPassword.length > 0 && !passwordsMatch && (
            <p className="text-danger text-xs font-mono">Passwords don't match</p>
          )}
          {error && <p className="text-danger text-xs font-mono">{error}</p>}
          <button
            disabled={!canSubmit}
            className="bg-accent text-paper rounded px-4 py-2 w-full text-sm font-semibold hover:brightness-110 transition disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:brightness-100"
          >
            Create Account
          </button>
        </form>

        <p className="text-xs text-comment text-center">
          Already have an account? <Link to="/login" className="text-accent hover:underline">Sign in</Link>
        </p>
      </div>
    </div>
  );
}