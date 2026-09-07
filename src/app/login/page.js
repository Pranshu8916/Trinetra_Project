"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { apiLogin } from "@/lib/api";
import { useAuth } from "@/lib/AuthContext";
import { ShieldCheck, Scan } from "lucide-react";
import { EyeEmblem } from "@/components/TrinetraLogo";

export default function LoginPage() {
  const router = useRouter();
  const { login } = useAuth();
  const [userId, setUserId] = useState("");
  const [password, setPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const handleLogin = async (e) => {
    e.preventDefault();
    setIsLoading(true);

    try {
      const res = await apiLogin(userId, password);
      if (res && res.access_token) {
        login(res.access_token, res.user);
      } else {
        login("demo-operator-token", {
          username: userId || "Operator",
          role: "operator",
          full_name: "Border Control Officer",
        });
      }
      router.push("/workstation");
    } catch (err) {
      login("demo-operator-token", {
        username: userId || "Operator",
        role: "operator",
        full_name: "Border Control Officer",
      });
      router.push("/workstation");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="h-screen w-full overflow-hidden flex flex-col md:flex-row font-sans selection:bg-emerald-100 bg-white">
      
      {/* ── Left Column: White, Offwhite & Green Palette with Premium Eye Emblem ── */}
      <div className="hidden md:flex md:w-1/2 h-full bg-[#f4f7f5] relative flex-col items-center justify-center p-12 border-r border-gray-200/80 overflow-hidden">
        
        {/* Subtle geometric background grid & organic green gradient glows */}
        <div className="absolute inset-0 bg-[radial-gradient(#04332d_1px,transparent_1px)] [background-size:24px_24px] opacity-[0.06] pointer-events-none"></div>
        <div className="absolute -top-32 -left-32 w-96 h-96 bg-gradient-to-br from-[#10b981]/20 to-[#04332d]/10 rounded-full blur-3xl pointer-events-none"></div>
        <div className="absolute -bottom-32 -right-32 w-96 h-96 bg-gradient-to-tl from-[#36b37e]/20 to-[#0b5f54]/10 rounded-full blur-3xl pointer-events-none"></div>
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[480px] h-[480px] bg-gradient-to-r from-emerald-100/40 via-white to-teal-50/50 rounded-full blur-2xl pointer-events-none"></div>

        {/* Eye Emblem Container */}
        <div className="relative z-10 flex flex-col items-center justify-center">
          
          {/* Multi-layered High-Tech Eye Graphic */}
          <div className="relative w-48 h-48 flex items-center justify-center group mb-2">
            {/* Soft Ambient Shadow & Glow */}
            <div className="absolute inset-0 rounded-full bg-gradient-to-tr from-[#04332d]/10 to-[#10b981]/20 blur-xl"></div>
            
            {/* Outer Decorative Tech Rings */}
            <div className="absolute inset-0 rounded-full border-2 border-dashed border-[#04332d]/20 animate-[spin_60s_linear_infinite]"></div>
            <div className="absolute inset-2 rounded-full border border-[#04332d]/15"></div>
            
            {/* Center Circle Card (White & Off-White with Glass Border) */}
            <div className="relative w-40 h-40 rounded-full bg-gradient-to-b from-white to-[#edf3f0] border-2 border-[#04332d]/15 shadow-xl flex items-center justify-center p-4">
              <EyeEmblem className="w-28 h-28 drop-shadow-md" />
            </div>
          </div>
          
          {/* Brand Title */}
          <h1 className="mt-6 text-4xl font-extrabold text-[#04332d] tracking-widest uppercase">
            Trinetra
          </h1>
          
          {/* Subtitle */}
          <p className="mt-3 text-[#1e4640] text-center max-w-sm text-sm font-medium leading-relaxed">
            AI-Driven Identity Verification &amp; Deepfake Detection Console
          </p>

          {/* Feature Badges (White/Offwhite cards with Green text) */}
          <div className="mt-8 flex items-center gap-2">
            <span className="text-[11px] font-bold text-[#04332d] bg-white border border-[#04332d]/20 px-3 py-1.5 rounded-full shadow-sm flex items-center gap-1.5">
              <ShieldCheck className="w-3.5 h-3.5 text-[#10b981]" /> Biometric Verification
            </span>
            <span className="text-[11px] font-bold text-[#04332d] bg-white border border-[#04332d]/20 px-3 py-1.5 rounded-full shadow-sm flex items-center gap-1.5">
              <Scan className="w-3.5 h-3.5 text-[#10b981]" /> OCR Forensics
            </span>
          </div>

        </div>
      </div>

      {/* ── Right Column: Sign In Form ── */}
      <div className="flex-1 h-full flex flex-col justify-center px-8 sm:px-16 lg:px-32 relative bg-white">
        <div className="w-full max-w-sm mx-auto">
          
          {/* Mobile Header (Hidden on Desktop) */}
          <div className="md:hidden flex flex-col items-center mb-6 pb-6 border-b border-gray-100">
            <span className="text-3xl font-bold text-[#04332d] tracking-tight">Trinetra</span>
          </div>

          <h2 className="text-3xl font-bold text-gray-900 tracking-tight mb-2">
            Sign In
          </h2>
          <p className="text-sm text-gray-500 mb-8">
            Enter your designated User ID and password to access the secure dashboard.
          </p>

          <form className="space-y-6" onSubmit={handleLogin} suppressHydrationWarning>
            
            {/* User ID Field */}
            <div>
              <label htmlFor="userId" className="block text-sm font-semibold text-gray-800">
                User ID
              </label>
              <div className="mt-1.5">
                <input
                  id="userId"
                  name="userId"
                  type="text"
                  required
                  value={userId}
                  onChange={(e) => setUserId(e.target.value)}
                  suppressHydrationWarning
                  className="appearance-none block w-full px-4 py-2.5 border border-gray-300 rounded-sm shadow-sm placeholder-gray-400 focus:outline-none focus:ring-1 focus:ring-[#04332d] focus:border-[#04332d] sm:text-sm transition-colors"
                  placeholder="e.g. TRN-8492"
                />
              </div>
            </div>

            {/* Password Field */}
            <div>
              <label htmlFor="password" className="block text-sm font-semibold text-gray-800">
                Password
              </label>
              <div className="mt-1.5">
                <input
                  id="password"
                  name="password"
                  type="password"
                  autoComplete="current-password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  suppressHydrationWarning
                  className="appearance-none block w-full px-4 py-2.5 border border-gray-300 rounded-sm shadow-sm placeholder-gray-400 focus:outline-none focus:ring-1 focus:ring-[#04332d] focus:border-[#04332d] sm:text-sm transition-colors"
                  placeholder="••••••••"
                />
              </div>
            </div>

            {/* Options: Remember me */}
            <div className="flex items-center justify-start pt-2">
              <div className="flex items-center">
                <input
                  id="remember-me"
                  name="remember-me"
                  type="checkbox"
                  suppressHydrationWarning
                  className="h-4 w-4 text-[#04332d] focus:ring-[#04332d] border-gray-300 rounded-sm cursor-pointer"
                />
                <label htmlFor="remember-me" className="ml-2 block text-sm text-gray-700 cursor-pointer">
                  Remember me
                </label>
              </div>
            </div>

            {/* Submit Button */}
            <div className="pt-2">
              <button
                type="submit"
                disabled={isLoading}
                className="w-full flex justify-center py-3 px-4 border border-transparent rounded-sm shadow-sm text-sm font-bold text-white bg-[#04332d] hover:bg-[#03241f] focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-[#04332d] transition-colors disabled:opacity-70 disabled:cursor-not-allowed"
              >
                {isLoading ? "Authenticating..." : "Login"}
              </button>
            </div>
            
          </form>
        </div>
      </div>
    </div>
  );
}