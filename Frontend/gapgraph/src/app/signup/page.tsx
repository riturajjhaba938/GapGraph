"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useApp } from "@/lib/context";
import { roleOptions } from "@/lib/data";
import { motion } from "framer-motion";

export default function SignupPage() {
  const router = useRouter();
  const { login, setSelectedRole } = useApp();
  const [isLoading, setIsLoading] = useState(false);
  const [formData, setFormData] = useState({ name: "", email: "", password: "", role: roleOptions[0] });

  const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:3001";

  const handleSignup = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);

    try {
      const res = await fetch(`${API_URL}/api/auth/signup`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(formData),
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.details ? `${data.error}: ${data.details}` : (data.error || "Signup failed"));
      }

      setSelectedRole(formData.role);
      login(data.user);
      router.push("/upload"); // Route to upload for new users
    } catch (error: any) {
      alert(error.message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-[80vh] flex items-center justify-center px-6 py-12">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="w-full max-w-lg bg-surface-container rounded-2xl p-8 relative overflow-hidden"
      >
        <div className="absolute inset-0 faint-grid opacity-10" />
        <div className="absolute -bottom-32 -left-32 w-64 h-64 bg-secondary/10 rounded-full blur-3xl" />
        
        <h2 className="text-3xl font-extrabold text-primary-container tracking-tight mb-2 relative z-10">
          Create Account
        </h2>
        <p className="text-on-surface-variant text-sm mb-8 relative z-10">
          Join GapGraph to build your personalized technical career roadmap.
        </p>

        <form onSubmit={handleSignup} className="space-y-5 relative z-10">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            <div className="space-y-1.5">
              <label className="text-xs font-bold text-on-surface uppercase tracking-wider">Full Name</label>
              <input
                type="text"
                required
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="w-full bg-surface-container-low border border-outline-variant/30 rounded-xl px-4 py-3 text-on-surface placeholder:text-on-surface-variant/40 focus:outline-none focus:border-primary-container/60 transition-colors"
                placeholder="Arjun Mehta"
              />
            </div>
            <div className="space-y-1.5">
              <label className="text-xs font-bold text-on-surface uppercase tracking-wider">Work Email</label>
              <input
                type="email"
                required
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                className="w-full bg-surface-container-low border border-outline-variant/30 rounded-xl px-4 py-3 text-on-surface placeholder:text-on-surface-variant/40 focus:outline-none focus:border-primary-container/60 transition-colors"
                placeholder="arjun@techcorp.in"
              />
            </div>
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-bold text-on-surface uppercase tracking-wider">Target Role</label>
            <select
              value={formData.role}
              onChange={(e) => setFormData({ ...formData, role: e.target.value })}
              className="w-full bg-surface-container-low border border-outline-variant/30 rounded-xl px-4 py-3 text-on-surface focus:outline-none focus:border-primary-container/60 transition-colors appearance-none"
            >
              {roleOptions.map((role) => (
                <option key={role} value={role}>{role}</option>
              ))}
            </select>
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-bold text-on-surface uppercase tracking-wider">Password</label>
            <input
              type="password"
              required
              value={formData.password}
              onChange={(e) => setFormData({ ...formData, password: e.target.value })}
              className="w-full bg-surface-container-low border border-outline-variant/30 rounded-xl px-4 py-3 text-on-surface placeholder:text-on-surface-variant/40 focus:outline-none focus:border-primary-container/60 transition-colors"
              placeholder="Min. 8 characters"
            />
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="w-full mt-6 pulse-gradient py-3.5 rounded-xl text-on-primary-container font-extrabold text-sm shadow-[0_0_20px_rgba(124,58,237,0.2)] hover:shadow-[0_0_30px_rgba(34,211,238,0.3)] transition-all flex items-center justify-center gap-2"
          >
            {isLoading ? (
              <>
                <span className="material-symbols-outlined animate-spin" style={{ fontVariationSettings: "'FILL' 1" }}>
                  progress_activity
                </span>
                Creating Profile...
              </>
            ) : (
              <>
                Create Account
                <span className="material-symbols-outlined text-sm">person_add</span>
              </>
            )}
          </button>
        </form>

        <div className="mt-8 text-center relative z-10">
          <p className="text-xs text-on-surface-variant">
            Already have an account?{" "}
            <button onClick={() => router.push("/login")} className="text-secondary font-bold hover:underline">
              Log In
            </button>
          </p>
        </div>
      </motion.div>
    </div>
  );
}
