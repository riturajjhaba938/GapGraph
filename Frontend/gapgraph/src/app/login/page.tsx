"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useApp } from "@/lib/context";
import { motion } from "framer-motion";

export default function LoginPage() {
  const router = useRouter();
  const { login } = useApp();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:3001";

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);

    try {
      const res = await fetch(`${API_URL}/api/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.details ? `${data.error}: ${data.details}` : (data.error || "Login failed"));
      }

      login(data.user);
      router.push("/upload");
    } catch (error: any) {
      alert(error.message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-[80vh] flex items-center justify-center px-6">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="w-full max-w-md bg-surface-container rounded-2xl p-8 relative overflow-hidden"
      >
        <div className="absolute inset-0 faint-grid opacity-10" />
        <div className="absolute -top-32 -right-32 w-64 h-64 bg-primary-container/20 rounded-full blur-3xl" />
        
        <h2 className="text-3xl font-extrabold text-primary-container tracking-tight mb-2 relative z-10">
          Welcome Back
        </h2>
        <p className="text-on-surface-variant text-sm mb-8 relative z-10">
          Log in to continue building your roadmap.
        </p>

        <form onSubmit={handleLogin} className="space-y-5 relative z-10">
          <div className="space-y-1.5">
            <label className="text-xs font-bold text-on-surface uppercase tracking-wider">Email Address</label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full bg-surface-container-low border border-outline-variant/30 rounded-xl px-4 py-3 text-on-surface placeholder:text-on-surface-variant/40 focus:outline-none focus:border-primary-container/60 transition-colors"
              placeholder="name@company.com"
            />
          </div>

          <div className="space-y-1.5">
            <div className="flex items-center justify-between">
              <label className="text-xs font-bold text-on-surface uppercase tracking-wider">Password</label>
              <a href="#" className="text-xs text-primary font-medium hover:underline">Forgot?</a>
            </div>
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full bg-surface-container-low border border-outline-variant/30 rounded-xl px-4 py-3 text-on-surface placeholder:text-on-surface-variant/40 focus:outline-none focus:border-primary-container/60 transition-colors"
              placeholder="••••••••"
            />
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="w-full mt-4 pulse-gradient py-3.5 rounded-xl text-on-primary-container font-extrabold text-sm shadow-[0_0_20px_rgba(124,58,237,0.2)] hover:shadow-[0_0_30px_rgba(34,211,238,0.3)] transition-all flex items-center justify-center gap-2"
          >
            {isLoading ? (
              <>
                <span className="material-symbols-outlined animate-spin" style={{ fontVariationSettings: "'FILL' 1" }}>
                  progress_activity
                </span>
                Authenticating...
              </>
            ) : (
              <>
                Login Securely
                <span className="material-symbols-outlined text-sm">login</span>
              </>
            )}
          </button>
        </form>

        <div className="mt-8 text-center relative z-10">
          <p className="text-xs text-on-surface-variant">
            Don't have an account?{" "}
            <button onClick={() => router.push("/signup")} className="text-secondary font-bold hover:underline">
              Sign Up
            </button>
          </p>
        </div>
      </motion.div>
    </div>
  );
}
