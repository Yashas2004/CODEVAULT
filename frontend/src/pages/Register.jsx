import { useState } from "react";
import api from "../api";
import { useNavigate } from "react-router-dom";

export default function Register() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const navigate = useNavigate();

  const handleRegister = async (e) => {
    e.preventDefault();
    await api.post("/users/register", { email, password });
    navigate("/login");
  };

  return (
    <form onSubmit={handleRegister} className="max-w-sm mx-auto mt-20 space-y-4">
      <h1 className="text-2xl font-bold">Register</h1>
      <input className="border p-2 w-full" placeholder="Email" onChange={e => setEmail(e.target.value)} />
      <input className="border p-2 w-full" type="password" placeholder="Password" onChange={e => setPassword(e.target.value)} />
      <button className="bg-black text-white p-2 w-full">Register</button>
    </form>
  );
}