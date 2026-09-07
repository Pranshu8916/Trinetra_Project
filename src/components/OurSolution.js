import Link from "next/link";

export default function OurSolution() {
  const solutions = [
    {
      id: "01",
      title: "Document Forensics & MRZ Validation",
      tag: "ICAO Doc 9303 Compliant",
      description:
        "High-resolution optical character analysis, multi-zone MRZ checksum verification, tamper heatmap generation, and Error Level Analysis (ELA) to detect altered text and photo swaps.",
      icon: (
        <svg className="w-6 h-6 text-[#0b5f54]" fill="none" stroke="currentColor" strokeWidth="1.75" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
      ),
    },
    {
      id: "02",
      title: "1:1 Biometric Face Verification",
      tag: "Neural Vector Matching",
      description:
        "512-dimensional facial embedding comparison matching government-issued document portraits against live-stream selfie frames with calibrated cosine similarity thresholds.",
      icon: (
        <svg className="w-6 h-6 text-[#0b5f54]" fill="none" stroke="currentColor" strokeWidth="1.75" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" d="M5.121 17.804A13.937 13.937 0 0112 16c2.5 0 4.847.655 6.879 1.804M15 10a3 3 0 11-6 0 3 3 0 016 0zm6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      ),
    },
    {
      id: "03",
      title: "Passive Anti-Spoofing & Liveness",
      tag: "ISO/IEC 30107-3 Standard",
      description:
        "Frictionless passive liveness analysis detecting printed paper photos, high-definition digital screen replays, 3D curved latex masks, and specular reflection anomalies.",
      icon: (
        <svg className="w-6 h-6 text-[#0b5f54]" fill="none" stroke="currentColor" strokeWidth="1.75" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
        </svg>
      ),
    },
    {
      id: "04",
      title: "Generative Deepfake Detection",
      tag: "Frequency Spectrum Inspection",
      description:
        "Spatial-frequency domain inspection flagging GAN artifacts, diffusion blurs, synthetic eye-blink irregularities, and boundary blending artifacts across video and imagery.",
      icon: (
        <svg className="w-6 h-6 text-[#0b5f54]" fill="none" stroke="currentColor" strokeWidth="1.75" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
        </svg>
      ),
    },
    {
      id: "05",
      title: "Real-Time Multi-Signal Risk Scoring",
      tag: "Adaptive Decision Matrix",
      description:
        "Instant composite risk scoring aggregating optical, biometric, algorithmic, and metadata fraud signals into an actionable low, medium, or high threat index for border guards.",
      icon: (
        <svg className="w-6 h-6 text-[#0b5f54]" fill="none" stroke="currentColor" strokeWidth="1.75" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
        </svg>
      ),
    },
    {
      id: "06",
      title: "Operator Workstation & PDF Audits",
      tag: "Border Control Ready",
      description:
        "Specialized three-pane desktop workstation with real-time camera capture, document cropping, ICAO field validation, automated logs, and one-click PDF forensic dossier exports.",
      icon: (
        <svg className="w-6 h-6 text-[#0b5f54]" fill="none" stroke="currentColor" strokeWidth="1.75" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
        </svg>
      ),
    },
  ];

  return (
    <section id="solutions" className="py-24 bg-[#fafbfc] border-y border-[#e2e8e6]">
      <div className="max-w-[1280px] mx-auto px-8">
        {/* Header */}
        <div className="max-w-3xl mb-16">
          <div className="flex items-center gap-2 text-[#0b5f54] font-semibold text-xs tracking-widest uppercase mb-3">
            <span className="w-1.5 h-1.5 rounded-none bg-[#0b5f54]" aria-hidden="true" />
            OUR SOLUTIONS
          </div>
          <h2 className="text-3xl lg:text-4xl font-semibold text-[#0a1917] mb-4 tracking-tight">
            Integrated Identity & Fraud Defense Platform
          </h2>
          <p className="text-lg text-gray-600 leading-relaxed">
            From algorithmic physical document tamper detection to sub-second neural biometric cross-matching, explore our modular defense architecture designed for high-security environments.
          </p>
        </div>

        {/* 6-Card Solutions Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 lg:gap-8">
          {solutions.map((item) => (
            <article
              key={item.id}
              className="group relative bg-white border border-[#e2e8e6] p-8 rounded-none flex flex-col justify-between transform transition-all duration-250 ease-out hover:-translate-y-1 hover:border-[#0b5f54] hover:shadow-md motion-reduce:hover:translate-y-0 motion-reduce:transition-none"
            >
              <div
                className="absolute top-0 left-0 right-0 h-[2px] bg-transparent group-hover:bg-[#0b5f54] transition-colors duration-250"
                aria-hidden="true"
              />
              <div>
                <div className="flex items-center justify-between mb-6">
                  <div className="w-12 h-12 flex items-center justify-center bg-[#f0f7f5] border border-[#dcebe6] rounded-none">
                    {item.icon}
                  </div>
                  <span className="text-xs font-mono font-medium tracking-wider text-[#0b5f54] bg-[#f0f7f5] px-2.5 py-1 rounded-none border border-[#dcebe6]">
                    {item.tag}
                  </span>
                </div>
                <h3 className="text-xl font-semibold text-[#0a1917] tracking-tight mb-3">
                  {item.title}
                </h3>
                <p className="text-[15px] leading-relaxed text-gray-600 font-normal">
                  {item.description}
                </p>
              </div>

              <div className="mt-6 pt-4 border-t border-gray-100 flex items-center justify-between text-xs font-medium text-gray-400 group-hover:text-[#0b5f54] transition-colors">
                <span>Trinetra Module {item.id}</span>
                <span className="text-[#0b5f54] opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-1 font-semibold">
                  Active &rarr;
                </span>
              </div>
            </article>
          ))}
        </div>

        {/* Bottom CTA Banner */}
        <div className="mt-14 p-8 bg-white border border-[#e2e8e6] flex flex-col md:flex-row items-center justify-between gap-6 shadow-sm">
          <div>
            <h4 className="text-lg font-semibold text-[#0a1917]">
              Ready to test the verification pipeline?
            </h4>
            <p className="text-sm text-gray-600 mt-1">
              Launch the live operator workstation to analyze passports, national IDs, and real-time biometric streams.
            </p>
          </div>
          <Link
            href="/login"
            className="whitespace-nowrap px-6 py-3 text-sm font-medium text-white bg-[#04332d] hover:bg-[#03241f] rounded-full transition-colors shadow-sm"
          >
            Launch Workstation
          </Link>
        </div>
      </div>
    </section>
  );
}
