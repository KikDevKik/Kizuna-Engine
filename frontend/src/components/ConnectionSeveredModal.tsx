import React from 'react';
import { RefreshCw, ShieldAlert } from 'lucide-react';
import '../KizunaHUD.css';

interface ConnectionSeveredModalProps {
    reason: string | null;
    onReboot: () => void;
}

export const ConnectionSeveredModal: React.FC<ConnectionSeveredModalProps> = ({ reason, onReboot }) => {
    return (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black backdrop-blur-xl">
            {/* Red Atmospheric Glow */}
            <div className="absolute inset-0 bg-red-900/10 mix-blend-overlay pointer-events-none animate-pulse" />

            <div className="relative max-w-2xl w-full mx-4">
                 {/* Outer Border Wrapper (Red Glow) */}
                 <div className="relative p-[1px] bg-gradient-to-b from-red-900 via-red-600 to-red-900 shadow-[0_0_50px_rgba(255,51,102,0.15)] shape-modal-shard">

                    {/* Inner Content */}
                    <div className="bg-[#05080F] shape-modal-shard p-12 flex flex-col items-center text-center relative overflow-hidden">

                        {/* Background Texture/Noise */}
                        <div className="absolute inset-0 opacity-10 bg-[url('https://www.transparenttextures.com/patterns/dark-matter.png')] mix-blend-overlay pointer-events-none" />

                        {/* Icon */}
                        <div className="mb-6 text-[#FF3366] animate-pulse">
                            <ShieldAlert size={64} strokeWidth={1} />
                        </div>

                        {/* Title */}
                        <h2 className="font-monumental text-4xl md:text-5xl tracking-[0.15em] text-[#FF3366] mb-2 drop-shadow-[0_0_15px_rgba(255,51,102,0.6)]">
                            CONNECTION SEVERED
                        </h2>

                        {/* Divider */}
                        <div className="w-32 h-[2px] bg-gradient-to-r from-transparent via-red-900 to-transparent mb-8" />

                        {/* Reason */}
                        <div className="font-technical text-xl text-[#00D1FF]/80 mb-10 max-w-md leading-relaxed tracking-wide border-l-2 border-red-900/50 pl-4 py-2">
                            {reason || "CRITICAL SOCIAL BATTERY DEPLETION DETECTED. SYSTEM FORCEFULLY TERMINATED."}
                        </div>

                        {/* Action Button */}
                        <button
                            onClick={onReboot}
                            className="relative group overflow-hidden px-8 py-3 bg-red-950/30 border border-red-500/50 hover:border-[#FF3366] transition-all duration-300"
                            style={{ clipPath: 'polygon(10% 0, 100% 0, 100% 80%, 90% 100%, 0 100%, 0 20%)' }}
                        >
                            <span className="relative z-10 flex items-center gap-3 font-monumental text-sm tracking-widest text-[#FF3366] group-hover:text-white transition-colors duration-300">
                                <RefreshCw size={18} className="group-hover:rotate-180 transition-transform duration-700" />
                                RE-INITIALIZE SYSTEM
                            </span>
                            {/* Hover Fill */}
                            <div className="absolute inset-0 bg-[#FF3366] transform scale-x-0 group-hover:scale-x-100 transition-transform duration-300 origin-left z-0 opacity-80" />
                        </button>

                        {/* Footer */}
                        <div className="mt-8 text-[10px] font-technical text-red-900/60 uppercase tracking-[0.2em]">
                            PROTOCOL: SILENT_GRACE // ERROR: 0xDEAD_BATTERY
                        </div>
                    </div>
                 </div>
            </div>
        </div>
    );
};
