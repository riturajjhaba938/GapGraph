"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useApp } from "@/lib/context";
import { user as mockUser, roleOptions } from "@/lib/data";
import { motion } from "framer-motion";
import { useRef } from "react";

export default function ProfilePage() {
  const router = useRouter();
  const { isLoggedIn, logout, selectedRole, setSelectedRole, profileImage, setProfileImage, user: contextUser } = useApp();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [isEditing, setIsEditing] = useState(false);
  const [formData, setFormData] = useState({
    name: contextUser?.name || mockUser.name,
    company: "GapGraph User",
    role: contextUser?.role || selectedRole,
    experience: mockUser.experience,
    email: contextUser?.email || "hello@gapgraph.io", 
    phone: "Not provided"
  });

  // Redirect if not logged in
  if (!isLoggedIn) {
     if (typeof window !== "undefined") router.push("/login");
     return null;
  }

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    setSelectedRole(formData.role);
    setIsEditing(false);
  };

  const handlePhotoUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const url = URL.createObjectURL(file);
      setProfileImage(url);
    }
  };

  const handleLogout = () => {
    logout();
    router.push("/login");
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="max-w-4xl mx-auto px-6 pt-12 pb-32"
    >
      <div className="flex items-center justify-between mb-8">
        <h1 className="text-4xl font-extrabold text-primary-container tracking-tight">
          Profile Settings
        </h1>
        <button
          onClick={handleLogout}
          className="flex items-center gap-2 px-4 py-2 bg-error-container/10 text-error rounded-xl hover:bg-error-container/30 transition-colors text-sm font-bold"
        >
          <span className="material-symbols-outlined text-sm">logout</span>
          Logout
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        {/* Profile Card Summary */}
        <div className="md:col-span-1 space-y-6">
          <div className="bg-surface-container rounded-2xl p-6 relative overflow-hidden text-center flex flex-col items-center">
            <div className="absolute top-0 w-full h-24 bg-gradient-to-br from-primary-container/40 to-secondary/20" />
            <div 
              className={`w-24 h-24 rounded-full bg-surface-container-highest border-4 border-surface-container z-10 flex items-center justify-center text-4xl font-extrabold text-primary-container shadow-xl mt-8 relative overflow-hidden group ${isEditing ? 'cursor-pointer' : ''}`}
              onClick={() => isEditing && fileInputRef.current?.click()}
            >
              <input type="file" ref={fileInputRef} hidden accept="image/*" onChange={handlePhotoUpload} />
              {profileImage ? (
                <img src={profileImage} alt="Profile" className="w-full h-full object-cover" />
              ) : (
                formData.name.split(" ").map((n: string) => n[0]).join("")
              )}
              {isEditing && (
                <div className="absolute inset-0 bg-black/60 flex flex-col justify-center items-center opacity-0 group-hover:opacity-100 transition-opacity">
                  <span className="material-symbols-outlined text-white text-xl">photo_camera</span>
                </div>
              )}
            </div>
            <h2 className="text-xl font-bold text-on-surface mt-4 relative z-10">{formData.name}</h2>
            <p className="text-secondary text-sm font-medium relative z-10">{formData.role}</p>
            <p className="text-on-surface-variant text-xs mt-1 relative z-10">{formData.company} • {formData.experience}</p>
            
            <button
              onClick={() => setIsEditing(!isEditing)}
              className="mt-6 w-full pulse-gradient py-2 rounded-xl text-on-primary-container font-bold text-sm shadow-[0_0_15px_rgba(124,58,237,0.3)] hover:scale-[1.02] transition-all flex items-center justify-center gap-2"
            >
              <span className="material-symbols-outlined text-sm">{isEditing ? "close" : "edit"}</span>
              {isEditing ? "Cancel Edit" : "Edit Profile"}
            </button>
          </div>

          <div className="bg-surface-container-low p-6 rounded-2xl border border-outline-variant/10">
            <h3 className="text-xs font-bold text-on-surface-variant uppercase tracking-widest mb-4">Uploaded Assets</h3>
            <div className="space-y-3">
              <div className="flex items-center gap-3 p-3 bg-surface-container-highest rounded-xl">
                <span className="material-symbols-outlined text-success">task</span>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-bold text-on-surface truncate">resume_v4.pdf</p>
                  <p className="text-[10px] text-on-surface-variant uppercase">Analyzed 2 days ago</p>
                </div>
              </div>
              <div className="flex items-center gap-3 p-3 bg-surface-container-highest rounded-xl">
                <span className="material-symbols-outlined text-secondary">description</span>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-bold text-on-surface truncate">Senior_Google_JD.pdf</p>
                  <p className="text-[10px] text-on-surface-variant uppercase">Target benchmark</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Detailed Settings Form */}
        <div className="md:col-span-2 bg-surface-container rounded-2xl p-8 relative overflow-hidden">
          <div className="absolute inset-0 faint-grid opacity-10 pointer-events-none" />
          <h3 className="text-violet-400 font-bold text-lg mb-6 uppercase tracking-widest flex items-center gap-2">
            <span className="material-symbols-outlined text-lg">manage_accounts</span>
            Personal Information
          </h3>

          <form onSubmit={handleSave} className="space-y-6 relative z-10">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-1.5">
                <label className="text-xs font-bold text-on-surface uppercase tracking-wider">Full Name</label>
                <input
                  type="text"
                  required
                  disabled={!isEditing}
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full bg-surface-container-low border border-outline-variant/30 rounded-xl px-4 py-3 text-on-surface focus:border-primary-container/60 transition-colors disabled:opacity-60 disabled:cursor-not-allowed"
                />
              </div>
              <div className="space-y-1.5">
                <label className="text-xs font-bold text-on-surface uppercase tracking-wider">Work Email</label>
                <input
                  type="email"
                  required
                  disabled={!isEditing}
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  className="w-full bg-surface-container-low border border-outline-variant/30 rounded-xl px-4 py-3 text-on-surface focus:border-primary-container/60 transition-colors disabled:opacity-60 disabled:cursor-not-allowed"
                />
              </div>
              <div className="space-y-1.5">
                <label className="text-xs font-bold text-on-surface uppercase tracking-wider">Phone Number</label>
                <input
                  type="text"
                  disabled={!isEditing}
                  value={formData.phone}
                  onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                  className="w-full bg-surface-container-low border border-outline-variant/30 rounded-xl px-4 py-3 text-on-surface focus:border-primary-container/60 transition-colors disabled:opacity-60 disabled:cursor-not-allowed"
                />
              </div>
              <div className="space-y-1.5">
                <label className="text-xs font-bold text-on-surface uppercase tracking-wider">Current Company</label>
                <input
                  type="text"
                  disabled={!isEditing}
                  value={formData.company}
                  onChange={(e) => setFormData({ ...formData, company: e.target.value })}
                  className="w-full bg-surface-container-low border border-outline-variant/30 rounded-xl px-4 py-3 text-on-surface focus:border-primary-container/60 transition-colors disabled:opacity-60 disabled:cursor-not-allowed"
                />
              </div>
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-bold text-on-surface uppercase tracking-wider">Target Job Role</label>
              <select
                disabled={!isEditing}
                value={formData.role}
                onChange={(e) => setFormData({ ...formData, role: e.target.value })}
                className="w-full bg-surface-container-low border border-outline-variant/30 rounded-xl px-4 py-3 text-on-surface focus:border-primary-container/60 transition-colors disabled:opacity-60 disabled:cursor-not-allowed appearance-none"
              >
                {roleOptions.map((role) => (
                  <option key={role} value={role}>{role}</option>
                ))}
              </select>
            </div>

            {isEditing && (
              <div className="pt-4 flex justify-end gap-3 border-t border-outline-variant/10">
                <button
                  type="button"
                  onClick={() => setIsEditing(false)}
                  className="px-6 py-2.5 rounded-xl border border-outline-variant text-on-surface-variant font-bold text-sm hover:bg-surface-container-high transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-8 py-2.5 rounded-xl bg-success text-slate-900 font-extrabold text-sm hover:brightness-110 shadow-[0_0_15px_rgba(52,211,153,0.3)] hover:scale-105 transition-all flex items-center gap-2"
                >
                  <span className="material-symbols-outlined text-sm" style={{ fontVariationSettings: "'FILL' 1" }}>check_circle</span>
                  Save Changes
                </button>
              </div>
            )}
          </form>
        </div>
      </div>
    </motion.div>
  );
}
