import { useState, useEffect } from 'react';
import { User, signInAnonymously } from 'firebase/auth';
import { auth } from '../lib/firebase';

export function useAuth() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    if (!auth) {
      // Si no hay configuración de Firebase, omitimos la autenticación
      setLoading(false);
      return;
    }

    const unsubscribe = auth.onAuthStateChanged((currentUser) => {
      if (currentUser) {
        setUser(currentUser);
        setLoading(false);
      } else {
        // Autenticar anónimamente si no hay sesión
        signInAnonymously(auth)
          .then((cred) => {
            setUser(cred.user);
            setLoading(false);
          })
          .catch((error) => {
            console.error('Error durante la autenticación anónima:', error);
            setLoading(false);
          });
      }
    });

    return () => unsubscribe();
  }, []);

  const getToken = async (): Promise<string | null> => {
    if (user) {
      try {
        return await user.getIdToken();
      } catch (error) {
        console.error('Error obteniendo ID token:', error);
        return null;
      }
    }
    return null;
  };

  return { user, loading, getToken };
}
