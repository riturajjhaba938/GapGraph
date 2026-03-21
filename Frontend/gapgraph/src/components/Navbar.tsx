"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useApp } from "@/lib/context";

const navItems = [
  { label: "Upload", href: "/upload", icon: "cloud_upload" },
  { label: "Gap Analysis", href: "/dashboard", icon: "analytics" },
  { label: "Roadmap", href: "/roadmap", icon: "route" },
  { label: "Module", href: "/module/1", icon: "view_module" },
];

export default function Navbar() {
  const pathname = usePathname();
  const { overallProgress, isLoggedIn, profileImage, user } = useApp();
  const readiness = 74 + Math.round(overallProgress * 0.26);

  const avatarInitials = user?.name 
    ? user.name.split(" ").map((n: string) => n[0]).join("").toUpperCase().substring(0, 2) 
    : "ME";

  return (
    <>
      {/* Desktop Nav */}
      <nav className="bg-slate-900/80 backdrop-blur-md sticky top-0 z-50 shadow-[0_0_20px_rgba(124,58,237,0.08)] flex justify-between items-center w-full px-6 py-3">
        <div className="flex items-center gap-4">
          <Link href="/upload" className="flex items-end gap-1 group">
            <div className="flex items-end gap-[2px]">
              <div className="w-1.5 h-3 bg-primary-container rounded-t-sm" />
              <div className="w-1.5 h-5 bg-secondary rounded-t-sm" />
              <div className="w-1.5 h-4 bg-emerald-400 rounded-t-sm" />
              <div className="w-1.5 h-6 bg-primary-container rounded-t-sm" />
            </div>
            <span className="text-xl font-bold bg-gradient-to-r from-violet-500 via-cyan-400 to-emerald-400 bg-clip-text text-transparent ml-2">
              GapGraph
            </span>
          </Link>
          <div className="hidden md:flex items-center gap-6 ml-10">
            {isLoggedIn && navItems.map((item) => {
              const isActive =
                pathname === item.href ||
                (item.href === "/module/1" && pathname.startsWith("/module"));
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`text-sm font-medium tracking-tight transition-colors ${
                    isActive
                      ? "text-cyan-400 font-bold border-b-2 border-cyan-400 pb-1"
                      : "text-slate-400 hover:text-slate-200"
                  }`}
                >
                  {item.label}
                </Link>
              );
            })}
          </div>
        </div>
        <div className="flex items-center gap-4 md:gap-6">
          {isLoggedIn ? (
            <>
              <div className="hidden md:flex bg-surface-container-high px-3 py-1.5 rounded-full border border-outline-variant/20 items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                <span className="text-on-surface-variant font-semibold text-sm">
                  Live Readiness: {readiness}%
                </span>
              </div>
              <Link href="/profile" className="w-9 h-9 rounded-full bg-primary-container hover:scale-105 transition-transform flex items-center justify-center text-sm font-bold text-on-primary-container shadow-[0_0_15px_rgba(124,58,237,0.3)] overflow-hidden">
                {profileImage ? (
                  <img src={profileImage} alt="Profile" className="w-full h-full object-cover" />
                ) : (
                  avatarInitials
                )}
              </Link>
            </>
          ) : (
            <>
              <Link
                href="/login"
                className={
                  pathname === "/signup"
                    ? "pulse-gradient px-5 py-2 rounded-full text-on-primary-container text-sm font-bold shadow-[0_0_15px_rgba(124,58,237,0.3)] hover:scale-105 transition-transform"
                    : "hidden md:inline-block text-on-surface-variant text-sm font-bold hover:text-primary transition-all active:text-primary active:drop-shadow-[0_0_12px_rgba(124,58,237,0.9)] focus:text-primary focus:drop-shadow-[0_0_12px_rgba(124,58,237,0.9)]"
                }
              >
                Log In
              </Link>
              <Link
                href="/signup"
                className={
                  pathname !== "/signup"
                    ? "pulse-gradient px-5 py-2 rounded-full text-on-primary-container text-sm font-bold shadow-[0_0_15px_rgba(124,58,237,0.3)] hover:scale-105 transition-transform"
                    : "hidden md:inline-block text-on-surface-variant text-sm font-bold hover:text-primary transition-all active:text-primary active:drop-shadow-[0_0_12px_rgba(124,58,237,0.9)] focus:text-primary focus:drop-shadow-[0_0_12px_rgba(124,58,237,0.9)]"
                }
              >
                Sign Up
              </Link>
            </>
          )}
        </div>
      </nav>

      {/* Mobile Bottom Nav */}
      {isLoggedIn && (
        <nav className="md:hidden fixed bottom-0 left-0 w-full z-50 flex justify-around items-center px-4 pb-6 pt-2 bg-slate-900/90 backdrop-blur-xl shadow-[0_-4px_24px_rgba(0,0,0,0.4)] rounded-t-xl">
          {navItems.map((item) => {
            const isActive =
              pathname === item.href ||
              (item.href === "/module/1" && pathname.startsWith("/module"));
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex flex-col items-center justify-center p-2 transition-all ${
                  isActive
                    ? "text-cyan-400 bg-cyan-400/10 rounded-xl scale-110"
                    : "text-indigo-400 hover:text-cyan-300"
                }`}
              >
                <span className="material-symbols-outlined">{item.icon}</span>
                <span className="text-[10px] uppercase tracking-widest mt-1">
                  {item.label}
                </span>
              </Link>
            );
          })}
        </nav>
      )}
    </>
  );
}
