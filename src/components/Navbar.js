"use client"; 

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import TrinetraLogo from "./TrinetraLogo";
import { Menu, X } from "lucide-react";

export default function Navbar() {
  const pathname = usePathname();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const handleScroll = (e, targetId) => {
    setMobileMenuOpen(false);
    if (pathname === "/") {
      e.preventDefault();
      const element = document.getElementById(targetId);
      if (element) {
        element.scrollIntoView({ behavior: "smooth", block: "start" });
      }
    }
  };

  return (
    <>
      {/* MHA & SSB Official Government Branding Topbar */}
      <div className="bg-[#021815] text-emerald-300 text-[11px] py-1.5 px-4 font-mono flex items-center justify-between border-b border-[#08423a]">
        <div className="max-w-[1280px] mx-auto w-full flex items-center justify-between px-2 sm:px-4">
          <div className="flex items-center gap-2">
            <span className="bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 text-[9px] font-bold px-1.5 py-0.5 rounded">GOVT OF INDIA</span>
            <span className="font-semibold text-white/90">Ministry of Home Affairs (MHA) & Sashastra Seema Bal (SSB)</span>
            <span className="hidden md:inline text-white/50">· Police II Division</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="bg-amber-500/20 text-amber-300 border border-amber-500/40 text-[9px] font-bold px-2 py-0.5 rounded">SIH PS ID: 26188</span>
          </div>
        </div>
      </div>

      <nav className="bg-white/95 backdrop-blur-md border-b border-gray-100 font-sans sticky top-0 z-50 shadow-xs">
        <div className="max-w-[1280px] mx-auto px-4 sm:px-8 py-3.5 flex items-center justify-between">
          {/* Logo Area with Enhanced Eye Emblem */}
          <Link href="/" className="flex items-center cursor-pointer group">
            <TrinetraLogo size="sm" textClassName="text-lg sm:text-xl group-hover:text-[#0b5f54] transition-colors" />
          </Link>

        {/* Center Navigation Links (Desktop) */}
        <div className="hidden lg:flex items-center space-x-8 text-sm font-medium text-gray-800">
          <Link
            href="/#solutions"
            onClick={(e) => handleScroll(e, "solutions")}
            className="flex items-center gap-1.5 hover:text-[#04332d] transition-colors"
          >
            Solutions
            <svg className="w-3 h-3 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" />
            </svg>
          </Link>
          <Link
            href="/#why-trinetra"
            onClick={(e) => handleScroll(e, "why-trinetra")}
            className="flex items-center gap-1.5 hover:text-[#04332d] transition-colors"
          >
            <svg className="w-4 h-4 text-[#04332d]" fill="currentColor" viewBox="0 0 20 20">
              <path
                fillRule="evenodd"
                d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z"
                clipRule="evenodd"
              />
            </svg>
            Why Trinetra?
          </Link>
          <Link
            href="/#about-us"
            onClick={(e) => handleScroll(e, "about-us")}
            className="hover:text-[#04332d] transition-colors"
          >
            About Us
          </Link>
        </div>

        {/* Right Action Buttons (Desktop) */}
        <div className="hidden sm:flex items-center space-x-4">
          <Link 
            href="/login"
            className="px-5 py-2 text-sm font-medium text-white bg-[#04332d] rounded-full hover:bg-[#03241f] active:scale-[0.98] transition-all shadow-sm"
          >
            Sign In
          </Link>
        </div>

        {/* Mobile Hamburger Button */}
        <div className="flex sm:hidden items-center">
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            aria-label="Toggle navigation menu"
            className="p-2 rounded-lg text-gray-700 hover:text-[#04332d] hover:bg-gray-100 transition-colors"
          >
            {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
        </div>
      </div>

      {/* Mobile Menu Dropdown */}
      {mobileMenuOpen && (
        <div className="sm:hidden border-t border-gray-100 bg-white px-4 pt-3 pb-6 space-y-3 shadow-lg animate-in slide-in-from-top-2">
          <Link
            href="/#solutions"
            onClick={(e) => handleScroll(e, "solutions")}
            className="block px-3 py-2 text-base font-semibold text-gray-800 hover:bg-gray-50 rounded-lg"
          >
            Solutions
          </Link>
          <Link
            href="/#why-trinetra"
            onClick={(e) => handleScroll(e, "why-trinetra")}
            className="block px-3 py-2 text-base font-semibold text-gray-800 hover:bg-gray-50 rounded-lg"
          >
            Why Trinetra?
          </Link>
          <Link
            href="/#about-us"
            onClick={(e) => handleScroll(e, "about-us")}
            className="block px-3 py-2 text-base font-semibold text-gray-800 hover:bg-gray-50 rounded-lg"
          >
            About Us
          </Link>
          <div className="pt-2">
            <Link 
              href="/login"
              onClick={() => setMobileMenuOpen(false)}
              className="block w-full text-center py-2.5 px-4 text-base font-bold text-white bg-[#04332d] rounded-full hover:bg-[#03241f] transition-all shadow-sm"
            >
              Sign In
            </Link>
          </div>
        </div>
      )}
    </nav>
    </>
  );
}