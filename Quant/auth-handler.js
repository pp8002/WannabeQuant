// auth-handler.js

// === Firebase imports ===
import { initializeApp } from "https://www.gstatic.com/firebasejs/12.1.0/firebase-app.js";
import { getAuth, GoogleAuthProvider, signInWithPopup, signOut, onAuthStateChanged } from "https://www.gstatic.com/firebasejs/12.1.0/firebase-auth.js";
import { getFirestore, doc, getDoc, setDoc } from "https://www.gstatic.com/firebasejs/12.1.0/firebase-firestore.js";

// === Firebase config ===
const firebaseConfig = {
  apiKey: YOUR_API_KEY,
   authDomain: "quant-5589e.firebaseapp.com",
    projectId: "quant-5589e",
    storageBucket: "quant-5589e.firebasestorage.app",
    messagingSenderId: "795935839648",
    appId: "1:795935839648:web:9b0cfeaeb1e590f90400c5",
    measurementId: "G-6SL04E2WVJ"
  };

// === Inicializace Firebase ===
const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
const db = getFirestore(app);
const provider = new GoogleAuthProvider();

// === Přihlášení pomocí Google ===
export async function signInWithGoogle() {
  try {
    const result = await signInWithPopup(auth, provider);
    const user = result.user;

    // Referenční dokument v databázi
    const userRef = doc(db, "users", user.uid);
    const userSnap = await getDoc(userRef);

    // Pokud uživatel neexistuje v DB, vytvoříme výchozí profil
    if (!userSnap.exists()) {
      await setDoc(userRef, {
        name: user.displayName,
        email: user.email,
        photoURL: user.photoURL,
        xp: 0,
        level: 1,
        streak: 0,
        badges: [],
        achievements: [],
        progress: {} // zde bude pokrok v lekcích
      });
    }

    // Uložení UID do localStorage
    localStorage.setItem("current_user", user.uid);

    // Přesměrování po přihlášení
    window.location.href = "account.html";

  } catch (error) {
    console.error("❌ Chyba při přihlášení:", error);
    alert("Přihlášení selhalo. Zkontroluj konzoli.");
  }
}

// === Odhlášení ===
export function logoutUser() {
  signOut(auth).then(() => {
    localStorage.removeItem("current_user");
    window.location.href = "index.html";
  }).catch((error) => {
    console.error("❌ Chyba při odhlášení:", error);
  });
}

// === Poslouchání změn přihlášení ===
export function listenToAuthState(callback) {
  onAuthStateChanged(auth, (user) => {
    if (user) {
      localStorage.setItem("current_user", user.uid);
      callback(user);
    } else {
      localStorage.removeItem("current_user");
      callback(null);
    }
  });
}

// === Pomocná funkce pro získání dat uživatele ===
export async function getUserData() {
  const uid = localStorage.getItem("current_user");
  if (!uid) return null;

  const userRef = doc(db, "users", uid);
  const userSnap = await getDoc(userRef);

  if (userSnap.exists()) {
    return userSnap.data();
  } else {
    return null;
  }
}
