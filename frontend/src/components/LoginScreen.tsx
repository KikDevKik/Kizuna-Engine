import { useEffect, useRef } from 'react';
import { signInWithRedirect, GoogleAuthProvider } from 'firebase/auth';
import { auth } from '../lib/firebase';
import type { Auth } from 'firebase/auth';
import { motion } from 'framer-motion';

// ─── Neural Network Canvas ──────────────────────────────────────────────────

function NeuralCanvas() {
    const canvasRef = useRef<HTMLCanvasElement>(null);

    useEffect(() => {
        const canvas = canvasRef.current;
        if (!canvas) return;
        const ctx = canvas.getContext('2d')!;

        type Point = { x: number; y: number; vx: number; vy: number };
        let points: Point[] = [];
        let rafId: number;

        const resize = () => {
            canvas.width = window.innerWidth;
            canvas.height = window.innerHeight;
        };

        const init = () => {
            resize();
            points = Array.from({ length: 40 }, () => ({
                x: Math.random() * canvas.width,
                y: Math.random() * canvas.height,
                vx: (Math.random() - 0.5) * 0.5,
                vy: (Math.random() - 0.5) * 0.5,
            }));
        };

        const animate = () => {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            ctx.strokeStyle = 'rgba(124, 59, 237, 0.2)';
            ctx.lineWidth = 0.5;

            for (const p of points) {
                p.x += p.vx;
                p.y += p.vy;
                if (p.x < 0 || p.x > canvas.width) p.vx *= -1;
                if (p.y < 0 || p.y > canvas.height) p.vy *= -1;

                for (const p2 of points) {
                    const dist = Math.hypot(p.x - p2.x, p.y - p2.y);
                    if (dist < 150) {
                        ctx.globalAlpha = 1 - dist / 150;
                        ctx.beginPath();
                        ctx.moveTo(p.x, p.y);
                        ctx.lineTo(p2.x, p2.y);
                        ctx.stroke();
                    }
                }
            }
            ctx.globalAlpha = 1;
            rafId = requestAnimationFrame(animate);
        };

        init();
        animate();
        window.addEventListener('resize', resize);

        return () => {
            cancelAnimationFrame(rafId);
            window.removeEventListener('resize', resize);
        };
    }, []);

    return (
        <canvas
            ref={canvasRef}
            className="fixed inset-0 pointer-events-none opacity-40"
        />
    );
}

// ─── Login Screen ────────────────────────────────────────────────────────────

interface LoginScreenProps {
    onGuestMode?: () => void;
}

export function LoginScreen({ onGuestMode }: LoginScreenProps) {
    const handleGoogleSignIn = async () => {
        if (!auth) {
            console.error('Firebase Auth not initialized');
            return;
        }
        try {
            const provider = new GoogleAuthProvider();
            await signInWithRedirect(auth as unknown as Auth, provider);
            // getRedirectResult in useAuth.ts captures the result after the browser returns
        } catch (err: any) {
            console.error('Google Sign-In redirect error:', err);
        }
    };

    return (
        <div className="relative min-h-screen flex items-center justify-center overflow-hidden bg-[#0a0a0f] text-white antialiased">
            <NeuralCanvas />

            <main className="relative z-10 w-full max-w-md px-6 text-center">

                {/* ─── Soul Engine Orb ─── */}
                <motion.div
                    className="mb-12 flex justify-center items-center"
                    initial={{ opacity: 0, scale: 0.7 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ duration: 1.2, ease: 'easeOut' }}
                >
                    <div className="relative w-64 h-64 flex items-center justify-center">
                        {/* Outer glow blob */}
                        <motion.div
                            className="absolute inset-0 rounded-full"
                            style={{
                                filter: 'blur(80px)',
                                background: 'radial-gradient(circle, rgba(124,59,237,0.4) 0%, rgba(6,182,212,0.1) 60%, transparent 100%)',
                            }}
                            animate={{ scale: [1, 1.05, 1], opacity: [0.6, 1, 0.6] }}
                            transition={{ duration: 6, repeat: Infinity, ease: 'easeInOut' }}
                        />

                        {/* Spinning outer ring */}
                        <motion.div
                            className="absolute inset-4 rounded-full border border-purple-500/20"
                            animate={{ rotate: 360 }}
                            transition={{ duration: 12, repeat: Infinity, ease: 'linear' }}
                        />
                        {/* Spinning inner ring — reverse */}
                        <motion.div
                            className="absolute inset-8 rounded-full border border-cyan-400/10"
                            animate={{ rotate: -360 }}
                            transition={{ duration: 12, repeat: Infinity, ease: 'linear' }}
                        />

                        {/* Core orb */}
                        <motion.div
                            className="relative z-10 w-24 h-24 rounded-full flex items-center justify-center"
                            style={{
                                background: 'radial-gradient(circle at center, #ffffff 0%, #7c3bed 30%, #06b6d4 70%, transparent 100%)',
                                boxShadow: '0 0 60px 20px rgba(124,59,237,0.3), 0 0 100px 40px rgba(6,182,212,0.2)',
                            }}
                            animate={{ scale: [1, 1.05, 1], opacity: [0.9, 1, 0.9] }}
                            transition={{ duration: 6, repeat: Infinity, ease: 'easeInOut' }}
                        >
                            <div className="w-16 h-16 border-2 border-white/20 rounded-full flex items-center justify-center overflow-hidden">
                                <div
                                    className="w-2 h-16 bg-white/40 rotate-45"
                                    style={{ filter: 'blur(4px)' }}
                                />
                            </div>
                        </motion.div>
                    </div>
                </motion.div>

                {/* ─── Branding ─── */}
                <motion.div
                    className="space-y-4 mb-16"
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.8, delay: 0.4 }}
                >
                    <h1
                        className="text-4xl font-light tracking-widest uppercase text-white/90"
                        style={{ fontFamily: "'Space Grotesk', sans-serif" }}
                    >
                        Kizuna Engine
                    </h1>
                    <p
                        className="text-cyan-400/60 italic font-light tracking-wide text-sm"
                        style={{ fontFamily: "'Space Grotesk', sans-serif" }}
                    >
                        "Donde las almas tienen memoria"
                    </p>
                </motion.div>

                {/* ─── Buttons ─── */}
                <motion.div
                    className="flex flex-col gap-6 items-center"
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.8, delay: 0.7 }}
                >
                    {/* Google Sign In */}
                    <button
                        onClick={handleGoogleSignIn}
                        className="group relative flex items-center justify-center gap-4 py-3.5 px-8 rounded-2xl w-full max-w-xs overflow-hidden transition-all duration-500"
                        style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.08)' }}
                    >
                        {/* Hover glow */}
                        <div
                            className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500"
                            style={{ background: 'rgba(124,59,237,0.1)' }}
                        />
                        {/* Google icon */}
                        <svg className="w-5 h-5 relative z-10 flex-shrink-0" viewBox="0 0 24 24">
                            <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4" />
                            <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853" />
                            <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05" />
                            <path d="M12 5.38c1.62 0 3.06.56 4.21 1.66l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335" />
                        </svg>
                        <span
                            className="font-medium tracking-wide text-white/80 group-hover:text-white transition-colors relative z-10"
                            style={{ fontFamily: "'Space Grotesk', sans-serif" }}
                        >
                            Iniciar sesión con Google
                        </span>
                    </button>

                    {/* Guest / no-auth fallback */}
                    {onGuestMode && (
                        <button
                            onClick={onGuestMode}
                            className="text-white/30 hover:text-white/60 text-xs tracking-widest uppercase transition-all duration-300 px-4 py-2"
                            style={{ fontFamily: "'Space Grotesk', sans-serif" }}
                        >
                            Continuar sin cuenta
                        </button>
                    )}
                </motion.div>
            </main>
        </div>
    );
}
