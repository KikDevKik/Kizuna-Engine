import { useState, useEffect } from "react";
import { onAuthStateChanged, signInWithCustomToken, signInWithRedirect, getRedirectResult, signOut, GoogleAuthProvider } from "firebase/auth";
import type { User, Auth } from "firebase/auth";
import { auth } from "../lib/firebase";

export const useAuth = () => {
    const [user, setUser] = useState<User | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (!auth) {
            setLoading(false);
            return;
        }

        let unsubscribe: (() => void) | null = null;

        const init = async () => {
            // Step 1: Await redirect result BEFORE subscribing to auth state.
            // This prevents the flash of "logged out" that causes the login loop.
            try {
                const result = await getRedirectResult(auth as unknown as Auth);
                if (result?.user) {
                    console.log('Redirect sign-in captured:', result.user.email);
                }
            } catch (err: any) {
                // auth/no-auth-event is expected when no redirect just happened — ignore it.
                if (err.code && err.code !== 'auth/no-auth-event') {
                    console.error('Redirect result error:', err);
                }
            }

            // Step 2: Subscribe to auth state AFTER redirect result is resolved.
            unsubscribe = onAuthStateChanged(auth as unknown as Auth, async (firebaseUser) => {
                if (firebaseUser) {
                }
                setUser(firebaseUser);
                setLoading(false);
            });
        };

        init();

        return () => {
            if (unsubscribe) unsubscribe();
        };
    }, []);

    const loginWithGoogle = async () => {
        if (!auth) throw new Error("Firebase Auth not initialized");
        const provider = new GoogleAuthProvider();
        return signInWithRedirect(auth as unknown as Auth, provider);
    };

    const loginWithToken = async (token: string) => {
        if (!auth) throw new Error("Firebase Auth not initialized");
        return signInWithCustomToken(auth as unknown as Auth, token);
    };

    const logout = async () => {
        if (!auth) return Promise.resolve();
        return signOut(auth as unknown as Auth);
    };

    const getToken = async () => {
        if (!user) return null;
        return user.getIdToken();
    };

    return { user, loading, loginWithGoogle, loginWithToken, logout, getToken };
};
