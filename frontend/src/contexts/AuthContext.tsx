import React, { createContext, useContext, useEffect, useState } from 'react';
import { initializeApp, getApps } from 'firebase/app';
import {
  getAuth,
  signInWithPopup,
  GoogleAuthProvider,
  signOut as fbSignOut,
  onAuthStateChanged,
  User,
} from 'firebase/auth';
import { api, setAuthToken } from '../api/client';

const FALLBACK_FIREBASE_CONFIG = {
  apiKey: "AIzaSyD6u4nLxVQeVwZa31sg8rwApmJ52Woyu1U",
  authDomain: "clipper-v.firebaseapp.com",
  projectId: "clipper-v",
  storageBucket: "clipper-v.firebasestorage.app",
  messagingSenderId: "9527946121",
  appId: "1:9527946121:web:0f7e59f7a0ad1b44968f58",
  measurementId: "G-XW9QLRPC1D",
};

interface AuthContextType {
  user: User | null;
  loading: boolean;
  signInWithGoogle: () => Promise<void>;
  devSignIn: (email?: string) => void;
  signOut: () => Promise<void>;
  isDev: boolean;
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  loading: true,
  signInWithGoogle: async () => { },
  devSignIn: () => { },
  signOut: async () => { },
  isDev: false,
});

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [isDev, setIsDev] = useState(false);

  useEffect(() => {
    let unsubscribe = () => { };

    const initAuth = async () => {
      try {
        const publicConfig = await api.getPublicConfig();
        const fbConfig = (publicConfig.firebase && publicConfig.firebase.apiKey)
          ? publicConfig.firebase
          : FALLBACK_FIREBASE_CONFIG;

        if (fbConfig && fbConfig.apiKey) {
          const app = getApps().length === 0 ? initializeApp(fbConfig) : getApps()[0];
          const auth = getAuth(app);

          unsubscribe = onAuthStateChanged(auth, async (currentUser) => {
            if (currentUser) {
              const token = await currentUser.getIdToken();
              setAuthToken(token);
              setUser(currentUser);
            } else {
              setAuthToken(null);
              setUser(null);
            }
            setLoading(false);
          });
        } else {
          // No Firebase web config provided, enable local dev bypass
          setIsDev(true);
          const savedMock = localStorage.getItem('clipper_dev_user');
          if (savedMock) {
            setUser(JSON.parse(savedMock) as any);
            setAuthToken('mock-token');
          }
          setLoading(false);
        }
      } catch (err) {
        console.warn('Firebase init error, falling back to dev mode:', err);
        setIsDev(true);
        setLoading(false);
      }
    };

    initAuth();
    return () => unsubscribe();
  }, []);

  const signInWithGoogle = async () => {
    try {
      const auth = getAuth();
      const provider = new GoogleAuthProvider();
      const result = await signInWithPopup(auth, provider);
      const token = await result.user.getIdToken();
      setAuthToken(token);
      setUser(result.user);
    } catch (err) {
      console.error('Sign-in failed:', err);
      throw err;
    }
  };

  const devSignIn = (email = 'creator@clipper.ai') => {
    const mockUser = {
      uid: 'dev-creator-123',
      email,
      displayName: 'Creator',
      photoURL: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=100&h=100&fit=crop&crop=faces',
    } as any;
    localStorage.setItem('clipper_dev_user', JSON.stringify(mockUser));
    setUser(mockUser);
    setAuthToken('mock-token');
  };

  const signOut = async () => {
    try {
      if (getApps().length > 0) {
        const auth = getAuth();
        await fbSignOut(auth);
      }
    } catch (e) {
      // ignore
    }
    localStorage.removeItem('clipper_dev_user');
    setAuthToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, signInWithGoogle, devSignIn, signOut, isDev }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);

