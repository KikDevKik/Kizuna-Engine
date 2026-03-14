import { useEffect, useRef, useState } from 'react';
import {
    signInWithEmailAndPassword,
    createUserWithEmailAndPassword,
} from 'firebase/auth';
import { auth } from '../lib/firebase';
import type { Auth } from 'firebase/auth';
import { motion, AnimatePresence } from 'framer-motion';

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
            ctx.lineWidth = 0.5;
            for (const p of points) {
                p.x += p.vx;
                p.y += p.vy;
                if (p.x < 0 || p.x > canvas.width) p.vx *= -1;
                if (p.y < 0 || p.y > canvas.height) p.vy *= -1;
                for (const p2 of points) {
                    const dist = Math.hypot(p.x - p2.x, p.y - p2.y);
                    if (dist < 150) {
                        ctx.globalAlpha = (1 - dist / 150) * 0.4;
                        ctx.strokeStyle = 'rgba(124, 59, 237, 1)';
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

    return <canvas ref={canvasRef} className="fixed inset-0 pointer-events-none" />;
}

// ─── Login Screen ────────────────────────────────────────────────────────────

interface LoginScreenProps {
    onGuestMode?: () => void;
}

type AuthMode = 'login' | 'register';

export function LoginScreen({ onGuestMode }: LoginScreenProps) {
    const [mode, setMode] = useState<AuthMode>('login');
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const friendlyError = (code: string) => {
        const map: Record<string, string> = {
            'auth/user-not-found': 'No existe cuenta con ese email.',
            'auth/wrong-password': 'Contraseña incorrecta.',
            'auth/email-already-in-use': 'Ya existe una cuenta con ese email.',
            'auth/weak-password': 'La contraseña debe tener al menos 6 caracteres.',
            'auth/invalid-email': 'El email no tiene un formato válido.',
            'auth/too-many-requests': 'Demasiados intentos. Espera un momento.',
            'auth/invalid-credential': 'Credenciales inválidas.',
        };
        return map[code] || 'Error desconocido. Intenta de nuevo.';
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!auth || !email || !password) return;
        setLoading(true);
        setError(null);
        try {
            if (mode === 'login') {
                await signInWithEmailAndPassword(auth as unknown as Auth, email, password);
            } else {
                await createUserWithEmailAndPassword(auth as unknown as Auth, email, password);
            }
            // onAuthStateChanged in useAuth.ts handles the rest
        } catch (err: any) {
            setError(friendlyError(err.code));
            setLoading(false);
        }
    };

    const inputClass =
        'w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white/90 text-sm placeholder-white/25 focus:outline-none focus:border-purple-500/60 focus:bg-white/8 transition-all duration-300';

    return (
        <div className="relative min-h-screen flex items-center justify-center overflow-hidden bg-[#0a0a0f] text-white antialiased">
            <NeuralCanvas />

            <main className="relative z-10 w-full max-w-md px-6 text-center">

                {/* ─── Soul Engine Orb ─── */}
                <motion.div
                    className="mb-10 flex justify-center items-center"
                    initial={{ opacity: 0, scale: 0.7 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ duration: 1.2, ease: 'easeOut' }}
                >
                    <div className="relative w-48 h-48 flex items-center justify-center">
                        <motion.div
                            className="absolute inset-0 rounded-full"
                            style={{
                                filter: 'blur(60px)',
                                background: 'radial-gradient(circle, rgba(124,59,237,0.4) 0%, rgba(6,182,212,0.1) 60%, transparent 100%)',
                            }}
                            animate={{ scale: [1, 1.05, 1], opacity: [0.6, 1, 0.6] }}
                            transition={{ duration: 6, repeat: Infinity, ease: 'easeInOut' }}
                        />
                        <motion.div
                            className="absolute inset-4 rounded-full border border-purple-500/20"
                            animate={{ rotate: 360 }}
                            transition={{ duration: 12, repeat: Infinity, ease: 'linear' }}
                        />
                        <motion.div
                            className="absolute inset-8 rounded-full border border-cyan-400/10"
                            animate={{ rotate: -360 }}
                            transition={{ duration: 12, repeat: Infinity, ease: 'linear' }}
                        />
                        <motion.div
                            className="relative z-10 w-20 h-20 rounded-full flex items-center justify-center"
                            style={{
                                background: 'radial-gradient(circle at center, #ffffff 0%, #7c3bed 30%, #06b6d4 70%, transparent 100%)',
                                boxShadow: '0 0 50px 15px rgba(124,59,237,0.3), 0 0 80px 30px rgba(6,182,212,0.15)',
                            }}
                            animate={{ scale: [1, 1.05, 1] }}
                            transition={{ duration: 6, repeat: Infinity, ease: 'easeInOut' }}
                        >
                            <div className="w-12 h-12 border-2 border-white/20 rounded-full flex items-center justify-center overflow-hidden">
                                <div className="w-1.5 h-12 bg-white/40 rotate-45" style={{ filter: 'blur(3px)' }} />
                            </div>
                        </motion.div>
                    </div>
                </motion.div>

                {/* ─── Branding ─── */}
                <motion.div
                    className="space-y-2 mb-8"
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.8, delay: 0.3 }}
                >
                    <h1 className="text-3xl font-light tracking-widest uppercase text-white/90" style={{ fontFamily: "'Space Grotesk', sans-serif" }}>
                        Kizuna Engine
                    </h1>
                    <p className="text-cyan-400/50 italic font-light tracking-wide text-xs" style={{ fontFamily: "'Space Grotesk', sans-serif" }}>
                        "Donde las almas tienen memoria"
                    </p>
                </motion.div>

                {/* ─── Form Card ─── */}
                <motion.div
                    className="rounded-2xl p-6"
                    style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.07)' }}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.8, delay: 0.5 }}
                >
                    {/* Mode toggle */}
                    <div className="flex rounded-xl overflow-hidden mb-6" style={{ background: 'rgba(255,255,255,0.05)' }}>
                        {(['login', 'register'] as AuthMode[]).map((m) => (
                            <button
                                key={m}
                                onClick={() => { setMode(m); setError(null); }}
                                className="flex-1 py-2.5 text-xs tracking-widest uppercase transition-all duration-300"
                                style={{
                                    fontFamily: "'Space Grotesk', sans-serif",
                                    background: mode === m ? 'rgba(124,59,237,0.3)' : 'transparent',
                                    color: mode === m ? 'rgba(255,255,255,0.9)' : 'rgba(255,255,255,0.35)',
                                    borderRadius: '0.75rem',
                                }}
                            >
                                {m === 'login' ? 'Iniciar sesión' : 'Crear cuenta'}
                            </button>
                        ))}
                    </div>

                    {/* Form */}
                    <form onSubmit={handleSubmit} className="flex flex-col gap-3">
                        <input
                            type="email"
                            placeholder="Email"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            className={inputClass}
                            style={{ fontFamily: "'Space Grotesk', sans-serif" }}
                            required
                            autoComplete="email"
                        />
                        <input
                            type="password"
                            placeholder="Contraseña"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            className={inputClass}
                            style={{ fontFamily: "'Space Grotesk', sans-serif" }}
                            required
                            autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
                            minLength={6}
                        />

                        {/* Error message */}
                        <AnimatePresence>
                            {error && (
                                <motion.p
                                    className="text-red-400/80 text-xs text-left px-1"
                                    style={{ fontFamily: "'Space Grotesk', sans-serif" }}
                                    initial={{ opacity: 0, height: 0 }}
                                    animate={{ opacity: 1, height: 'auto' }}
                                    exit={{ opacity: 0, height: 0 }}
                                >
                                    {error}
                                </motion.p>
                            )}
                        </AnimatePresence>

                        {/* Submit button */}
                        <button
                            type="submit"
                            disabled={loading}
                            className="mt-2 flex items-center justify-center gap-3 py-3 px-6 rounded-xl transition-all duration-300 disabled:opacity-60 disabled:cursor-not-allowed"
                            style={{
                                background: 'linear-gradient(135deg, rgba(124,59,237,0.6) 0%, rgba(6,182,212,0.4) 100%)',
                                border: '1px solid rgba(124,59,237,0.3)',
                                fontFamily: "'Space Grotesk', sans-serif",
                            }}
                        >
                            {loading ? (
                                <>
                                    <motion.div
                                        className="w-4 h-4 rounded-full border-2 border-white/20 border-t-white/80"
                                        animate={{ rotate: 360 }}
                                        transition={{ duration: 0.8, repeat: Infinity, ease: 'linear' }}
                                    />
                                    <span className="text-sm text-white/70 tracking-wide">
                                        {mode === 'login' ? 'Entrando...' : 'Creando cuenta...'}
                                    </span>
                                </>
                            ) : (
                                <span className="text-sm text-white/90 tracking-wide font-medium">
                                    {mode === 'login' ? 'Iniciar sesión' : 'Crear cuenta'}
                                </span>
                            )}
                        </button>
                    </form>

                    {/* Divider */}
                    <div className="flex items-center gap-3 my-5">
                        <div className="flex-1 h-px" style={{ background: 'rgba(255,255,255,0.07)' }} />
                        <span className="text-white/20 text-xs" style={{ fontFamily: "'Space Grotesk', sans-serif" }}>o</span>
                        <div className="flex-1 h-px" style={{ background: 'rgba(255,255,255,0.07)' }} />
                    </div>

                    {/* Google button — disabled, coming soon */}
                    <div className="relative group">
                        <button
                            disabled
                            className="flex items-center justify-center gap-3 w-full py-3 px-6 rounded-xl opacity-35 cursor-not-allowed transition-all"
                            style={{
                                background: 'rgba(255,255,255,0.04)',
                                border: '1px solid rgba(255,255,255,0.07)',
                                fontFamily: "'Space Grotesk', sans-serif",
                            }}
                        >
                            <svg className="w-4 h-4 flex-shrink-0" viewBox="0 0 24 24">
                                <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4" />
                                <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853" />
                                <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05" />
                                <path d="M12 5.38c1.62 0 3.06.56 4.21 1.66l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335" />
                            </svg>
                            <span className="text-sm text-white/60 tracking-wide">Continuar con Google</span>
                        </button>
                        {/* Tooltip */}
                        <div
                            className="absolute -top-9 left-1/2 -translate-x-1/2 px-3 py-1.5 rounded-lg text-xs text-white/60 whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none"
                            style={{ background: 'rgba(0,0,0,0.8)', border: '1px solid rgba(255,255,255,0.1)', fontFamily: "'Space Grotesk', sans-serif" }}
                        >
                            Próximamente (requiere plugin nativo)
                        </div>
                    </div>
                </motion.div>

                {/* Guest mode */}
                {onGuestMode && (
                    <motion.button
                        onClick={onGuestMode}
                        className="mt-6 text-white/25 hover:text-white/50 text-xs tracking-widest uppercase transition-all duration-300"
                        style={{ fontFamily: "'Space Grotesk', sans-serif" }}
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        transition={{ delay: 0.9 }}
                    >
                        Continuar sin cuenta
                    </motion.button>
                )}
            </main>
        </div>
    );
}
