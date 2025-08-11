// === Firebase imports ===
import { auth, db } from './firebase-init.js';
import { GoogleAuthProvider, signInWithPopup, signOut, onAuthStateChanged } from "https://www.gstatic.com/firebasejs/12.1.0/firebase-auth.js";
import { doc, getDoc, setDoc } from "https://www.gstatic.com/firebasejs/12.1.0/firebase-firestore.js";

// === Google provider ===
const provider = new GoogleAuthProvider();

// === Přihlášení pomocí Google ===
export async function signInWithGoogle() {
  try {
    const result = await signInWithPopup(auth, provider);
    const user = result.user;

    const userRef = doc(db, "users", user.uid);
    const userSnap = await getDoc(userRef);

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
        progress: {}
      });
    }

    localStorage.setItem("current_user", user.uid);
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

  return userSnap.exists() ? userSnap.data() : null;
}
