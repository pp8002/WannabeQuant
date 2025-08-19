// === firebase-init.js ===
// DŮLEŽITÉ: v HTML vždy nejdřív <script src="env.js"></script> a až POTOM tento soubor:
// <script type="module" src="firebase-init.js"></script>

import { initializeApp, getApps } from "https://www.gstatic.com/firebasejs/12.1.0/firebase-app.js";
import {
  getAuth,
  setPersistence,
  browserLocalPersistence,
  GoogleAuthProvider,
  signInWithPopup,
  onAuthStateChanged,
  signOut,
} from "https://www.gstatic.com/firebasejs/12.1.0/firebase-auth.js";
import {
  getFirestore,
  doc,
  getDoc,
  setDoc,
} from "https://www.gstatic.com/firebasejs/12.1.0/firebase-firestore.js";

// --- Firebase config (API key bere z window.FIREBASE_API_KEY v env.js) ---
const firebaseConfig = {
  apiKey: window.FIREBASE_API_KEY,
  authDomain: "quant-dacab.firebaseapp.com",
  projectId: "quant-dacab",
  storageBucket: "quant-dacab.firebasestorage.app",
  messagingSenderId: "1045234348083",
  appId: "1:1045234348083:web:10728b98b79bd0a2da7346",
  measurementId: "G-GX59BDV9BM",
};

// --- Inicializace jen jednou ---
const app  = getApps().length ? getApps()[0] : initializeApp(firebaseConfig);
const auth = getAuth(app);
const db   = getFirestore(app);

// --- Lokální perzistence (uživatel zůstane přihlášen) ---
setPersistence(auth, browserLocalPersistence).catch(e =>
  console.error("Auth persistence error:", e)
);

// --- Guard: prevent multiple concurrent popups ---
let __loginInProgress = false;

// --- Helpers: uživatelský dokument ve Firestore ---
async function ensureUserDoc(uid, profile) {
  try {
    const ref = doc(db, "users", uid);
    const snap = await getDoc(ref);
    if (!snap.exists()) {
      await setDoc(ref, {
        name: profile.displayName || "",
        email: profile.email || "",
        photoURL: profile.photoURL || "",
        xp: 0,
        level: 1,
        streak: 0,
        badges: [],
        achievements: [],
        progress: {},
        createdAt: Date.now(),
      });
    }
  } catch (err) {
    console.warn("ensureUserDoc failed (non-blocking):", err);
  }
}

export async function getUserProgress(uid) {
  try {
    const ref = doc(db, "users", uid);
    const snap = await getDoc(ref);
    return snap.exists() ? snap.data() : null;
  } catch (e) {
    console.error("getUserProgress:", e);
    return null;
  }
}

export async function saveUserProgress(uid, data) {
  try {
    const ref = doc(db, "users", uid);
    await setDoc(ref, data, { merge: true });
  } catch (e) {
    console.error("saveUserProgress:", e);
  }
}

// --- Robustní Google login (POPUP) s pojistkami ---
export async function startGoogleSignIn() {
  // Už je přihlášen? → rovnou na account
  if (auth.currentUser?.uid) {
    console.log("🟢 Already signed in → redirecting to account.html");
    window.location.href = "account.html";
    return;
  }

  const provider = new GoogleAuthProvider();
  provider.setCustomParameters({ prompt: "select_account" });

  let finished = false;

  if (__loginInProgress) {
    console.log("⏳ Login already in progress – ignoring extra click");
    return;
  }
  __loginInProgress = true;

  // „Dokočovací“ funkce — redirect proběhne hned, uložení do DB neblokuje
  const finish = (user) => {
    if (finished || !user) return;
    finished = true;
    console.log("✅ Auth state has user →", user.uid);
    localStorage.setItem("current_user", user.uid);
    setTimeout(() => ensureUserDoc(user.uid, user), 0); // non-blocking
    window.location.href = "account.html";
  };

  // Listener — pokryje zpožděný příchod uživatele z popupu/cache
  const unsub = onAuthStateChanged(auth, (user) => {
    if (user) {
      finish(user);
      unsub();
    }
  });

  try {
    console.log("🔑 Opening Google popup…");
    const res = await signInWithPopup(auth, provider);
    const user = res?.user;
    console.log("🧩 Popup resolved. user:", !!user, user?.uid);

    // Některé prohlížeče nastaví currentUser o chlup později → pojistky:
    setTimeout(() => finish(user || auth.currentUser), 50);
    setTimeout(() => finish(auth.currentUser), 300);
  } catch (err) {
    unsub();
    console.error("❌ signInWithPopup error:", err?.code, err?.message);
    alert("Sign-in failed: " + (err?.message || err));
    __loginInProgress = false;
  }
}

// --- Logout + redirect ---
export function logoutUser() {
  return signOut(auth).then(() => {
    localStorage.removeItem("current_user");
    window.location.href = "login.html";
  });
}

// --- Exporty služeb ---
export { app, auth, db };
