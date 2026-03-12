import { useState, useEffect } from "react";
import { onAuthStateChanged, signInWithCustomToken, signOut } from "firebase/auth";
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

        const unsubscribe = onAuthStateChanged(auth as unknown as Auth, async (firebaseUser) => {
            if (firebaseUser) {
                // Forgemaster: Verify backend sync on load
                try {
                    const token = await firebaseUser.getIdToken();
                    const response = await fetch('http://localhost:8000/api/auth/sync', {
                        method: 'POST',
                        headers: {
                            'Authorization': `Bearer ${token}`
                        }
                    });

                    if (!response.ok) {
                        console.error('Failed to sync user with backend during auth state change', response.status);
                    } else {
                        console.log('User synced successfully with backend');
                    }
                } catch (error) {
                    console.error('Error syncing user with backend:', error);
                }
            }

            setUser(firebaseUser);
            setLoading(false);
        });

        return () => unsubscribe();
    }, []);

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

    return { user, loading, loginWithToken, logout, getToken };
};
