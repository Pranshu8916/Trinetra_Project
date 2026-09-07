"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function DashboardRedirect() {
  const router = useRouter();

  useEffect(() => {
    router.replace("/workstation");
  }, [router]);

  return (
    <div className="min-h-screen bg-[#f5f5f3] flex items-center justify-center font-sans">
      <div className="flex items-center gap-2 text-[#04332d] text-sm font-semibold">
        <svg className="w-5 h-5 animate-spin" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
          <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83" />
        </svg>
        Redirecting to Workstation…
      </div>
    </div>
  );
}
