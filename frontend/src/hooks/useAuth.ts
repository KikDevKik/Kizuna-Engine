import { useState, useEffect } from "react";
import { onAuthStateChanged, signInWithCustomToken, signInWithPopup, signOut, GoogleAuthProvider } from "firebase/auth";
import type { User, Auth } from "firebase/auth";
import { auth } from "../lib/firebase";
import { API_URL } from "../config";

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
                try {
                    const token = await firebaseUser.getIdToken();
                    const response = await fetch(`${API_URL}/api/auth/sync`, {
                        method: 'POST',
                        headers: { 'Authorization': `Bearer ${token}` }
                    });
                    if (!response.ok) {
                        console.error('Failed to sync user with backend', response.status);
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

    const loginWithGoogle = async () => {
        if (!auth) throw new Error("Firebase Auth not initialized");
        const provider = new GoogleAuthProvider();
        return signInWithPopup(auth as unknown as Auth, provider);
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
