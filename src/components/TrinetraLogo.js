"use client";

/**
 * EyeEmblem
 * Premium multi-layered vector biometric eye logo component.
 */
export function EyeEmblem({ className = "w-8 h-8" }) {
  return (
    <svg viewBox="0 0 120 120" className={className} xmlns="http://www.w3.org/2000/svg">
      <defs>
        {/* Iris Gradient */}
        <linearGradient id="trinetraIrisGrad" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#10b981" />
          <stop offset="50%" stopColor="#0b5f54" />
          <stop offset="100%" stopColor="#04332d" />
        </linearGradient>
        {/* Sclera Gradient */}
        <linearGradient id="trinetraScleraGrad" x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stopColor="#ffffff" />
          <stop offset="100%" stopColor="#e2ece7" />
        </linearGradient>
      </defs>

      {/* Outer Eye Outline / Almond Contour */}
      <path
        d="M10 60 C35 20, 85 20, 110 60 C85 100, 35 100, 10 60 Z"
        fill="url(#trinetraScleraGrad)"
        stroke="#04332d"
        strokeWidth="3.5"
        strokeLinejoin="round"
      />

      {/* Iris Outer Ring */}
      <ellipse cx="60" cy="60" rx="24" ry="24" fill="url(#trinetraIrisGrad)" stroke="#04332d" strokeWidth="1.5" />

      {/* Tech Reticle Dashed Ring */}
      <circle cx="60" cy="60" r="18" fill="none" stroke="#ffffff" strokeWidth="0.75" strokeDasharray="3 2" opacity="0.7" />

      {/* Pupil */}
      <circle cx="60" cy="60" r="10" fill="#031d19" />

      {/* Catchlight / Glint Highlights */}
      <circle cx="55" cy="54" r="3.5" fill="#ffffff" />
      <circle cx="66" cy="65" r="1.5" fill="#ffffff" opacity="0.75" />

      {/* Scanning Corner Reticle Markers */}
      <path d="M15 45 L15 35 L25 35" fill="none" stroke="#0b5f54" strokeWidth="1.5" strokeLinecap="round" />
      <path d="M105 45 L105 35 L95 35" fill="none" stroke="#0b5f54" strokeWidth="1.5" strokeLinecap="round" />
      <path d="M15 75 L15 85 L25 85" fill="none" stroke="#0b5f54" strokeWidth="1.5" strokeLinecap="round" />
      <path d="M105 75 L105 85 L95 85" fill="none" stroke="#0b5f54" strokeWidth="1.5" strokeLinecap="round" />
    </svg>
  );
}

/**
 * TrinetraLogo
 * Full brand component combining EyeEmblem icon and stylized typography.
 */
export default function TrinetraLogo({
  size = "md",
  showText = true,
  subtitle = null,
  textClassName = "",
  iconClassName = "",
}) {
  const sizeMap = {
    sm: "w-6 h-6",
    md: "w-8 h-8",
    lg: "w-12 h-12",
    xl: "w-20 h-20",
    hero: "w-28 h-28 md:w-36 md:h-36",
  };

  const eyeSize = sizeMap[size] || sizeMap.md;

  return (
    <div className="flex items-center gap-2.5 select-none inline-flex">
      <div className="relative flex items-center justify-center shrink-0">
        <EyeEmblem className={`${eyeSize} ${iconClassName}`} />
      </div>
      {showText && (
        <div className="flex flex-col">
          <span className={`font-black text-[#04332d] tracking-tight ${textClassName || "text-lg"}`}>
            Trinetra
          </span>
          {subtitle && (
            <span className="text-[10px] text-gray-400 font-semibold tracking-wider uppercase -mt-1">
              {subtitle}
            </span>
          )}
        </div>
      )}
    </div>
  );
}
