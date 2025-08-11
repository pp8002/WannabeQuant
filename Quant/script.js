// ====== Firebase imports (modulová verze) ======
import { initializeApp } from "https://www.gstatic.com/firebasejs/12.1.0/firebase-app.js";
import { getAuth, onAuthStateChanged } from "https://www.gstatic.com/firebasejs/12.1.0/firebase-auth.js";
import { getFirestore, doc, getDoc } from "https://www.gstatic.com/firebasejs/12.1.0/firebase-firestore.js";

// ====== Firebase config ======
const firebaseConfig = {
  apiKey: "AIzaSyBcJbbjNDvZqLvGcfevfJVX6jKixHmYAwI",
  authDomain: "quant-5589e.firebaseapp.com",
  projectId: "quant-5589e",
  storageBucket: "quant-5589e.firebasestorage.app",
  messagingSenderId: "795935839648",
  appId: "1:795935839648:web:31e0a952fad4d1e60400c5",
  measurementId: "G-DQ0R4TCBFC"
};

// ====== Initialize Firebase ======
const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
const db = getFirestore(app);

// ====== Render user progress to DOM ======
function renderUserProgress(data) {
  if (!data) return;

  document.getElementById("xpCount").textContent = data.xp || 0;
  document.getElementById("levelCount").textContent = data.level || 1;
  document.getElementById("streakCount").textContent = data.streak || 0;

  // Zobraz badge (pokud existují)
  const badgeList = document.getElementById("badgeList");
  if (badgeList && data.badges && data.badges.length > 0) {
    badgeList.innerHTML = "";
    data.badges.forEach(badge => {
      const span = document.createElement("span");
      span.textContent = badge;
      span.className = "bg-yellow-400 text-black font-bold px-2 py-1 rounded mr-2";
      badgeList.appendChild(span);
    });
  }

  // Zobraz progress lekcí (pokud existují)
  const lessons = data.progress || {};
  for (const [lessonId, status] of Object.entries(lessons)) {
    const el = document.getElementById(`lesson-${lessonId}`);
    if (el && status.completed) {
      el.classList.add("opacity-100");
      el.classList.remove("opacity-50");
      el.querySelector(".status").textContent = "✅";
    }
  }
}

// ✅ Importuj správné Firebase moduly
import { getAuth, onAuthStateChanged } from "https://www.gstatic.com/firebasejs/12.1.0/firebase-auth.js";
import { getFirestore, doc, getDoc } from "https://www.gstatic.com/firebasejs/12.1.0/firebase-firestore.js";
import { app } from './firebase-init.js'; // ujisti se, že exportuješ `app`

// === Firebase imports ===
import { auth, db } from './firebase-init.js';
import { onAuthStateChanged } from "https://www.gstatic.com/firebasejs/12.1.0/firebase-auth.js";
import { doc, getDoc } from "https://www.gstatic.com/firebasejs/12.1.0/firebase-firestore.js";

// === Listen to Firebase auth state ===
onAuthStateChanged(auth, async (user) => {
  if (user) {
    localStorage.setItem("current_user", user.uid);

    const userRef = doc(db, "users", user.uid);
    const docSnap = await getDoc(userRef);

    if (docSnap.exists()) {
      const userData = docSnap.data();
      renderUserProgress(userData); // Funkce pro vykreslení progresu
    }
  } else {
    localStorage.removeItem("current_user");
  }
});



