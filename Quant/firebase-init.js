// firebase-init.js

// ✅ Firebase imports (z CDN, správné pořadí)
import { initializeApp, getApps } from "https://www.gstatic.com/firebasejs/12.1.0/firebase-app.js";
import { getAuth } from "https://www.gstatic.com/firebasejs/12.1.0/firebase-auth.js";
import { getFirestore } from "https://www.gstatic.com/firebasejs/12.1.0/firebase-firestore.js";

// ✅ Konfigurace načtená z env.js (musíš mít <script src="/env.js"></script> v HTML)
const firebaseConfig = {
  apiKey: window.FIREBASE_API_KEY,
  authDomain: "quant-25068.firebaseapp.com",
  projectId: "quant-25068",
  storageBucket: "quant-25068.firebasestorage.app",
  messagingSenderId: "994280892133",
  appId: "1:994280892133:web:d23746af3460f3300f960c",
  measurementId: "G-1G0LNME5GH"
};

// ✅ Inicializuj Firebase pouze pokud ještě nebyl inicializován
const app = getApps().length === 0 ? initializeApp(firebaseConfig) : getApps()[0];

// ✅ Získej služby
const auth = getAuth(app);
const db = getFirestore(app);

// ✅ Exportuj pro další soubory
export { app, auth, db };

// ✅ Uživatelské funkce pro práci s Firestore

/**
 * Uloží nebo aktualizuje uživatelský profil (např. XP, level, completedLessons)
 */
export async function saveUserProgress(userId, data) {
  try {
    const userRef = doc(db, "users", userId);
    await setDoc(userRef, data, { merge: true }); // merge zachová existující data
  } catch (error) {
    console.error("❌ Error saving user progress:", error);
  }
}

/**
 * Načte data o uživateli
 */
export async function getUserProgress(userId) {
  try {
    const userRef = doc(db, "users", userId);
    const docSnap = await getDoc(userRef);
    return docSnap.exists() ? docSnap.data() : null;
  } catch (error) {
    console.error("❌ Error loading user progress:", error);
    return null;
  }
}
