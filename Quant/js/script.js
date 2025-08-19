// ====== Firebase imports z vlastního initu ======
import { app, auth, db } from "./firebase-init.js";
import { onAuthStateChanged } from "https://www.gstatic.com/firebasejs/12.1.0/firebase-auth.js";
import { doc, getDoc } from "https://www.gstatic.com/firebasejs/12.1.0/firebase-firestore.js";

// ====== Listen to auth state ======
onAuthStateChanged(auth, async (user) => {
  if (user) {
    localStorage.setItem("current_user", user.uid);

    const userRef = doc(db, "users", user.uid);
    const docSnap = await getDoc(userRef);

    if (docSnap.exists()) {
      const userData = docSnap.data();
      renderUserProgress(userData);
    }
  } else {
    localStorage.removeItem("current_user");
  }
});

// ====== Render user progress ======
function renderUserProgress(data) {
  if (!data) return;

  const xpEl = document.getElementById("xpCount");
  const lvlEl = document.getElementById("levelCount");
  const streakEl = document.getElementById("streakCount");

  if (!xpEl || !lvlEl || !streakEl) {
    console.warn("Některé prvky nebo uživatel chybí.");
    return;
  }

  xpEl.textContent = data.xp || 0;
  lvlEl.textContent = data.level || 1;
  streakEl.textContent = data.streak || 0;

  // === Badge ===
  const badgeList = document.getElementById("badgeList");
  if (badgeList && data.badges?.length > 0) {
    badgeList.innerHTML = "";
    data.badges.forEach(badge => {
      const span = document.createElement("span");
      span.textContent = badge;
      span.className = "bg-yellow-400 text-black font-bold px-2 py-1 rounded mr-2";
      badgeList.appendChild(span);
    });
  }

  // === Lesson Progress ===
  const lessons = data.progress || {};
  for (const [lessonId, status] of Object.entries(lessons)) {
    const el = document.getElementById(`lesson-${lessonId}`);
    if (el && status.completed) {
      el.classList.add("opacity-100");
      el.classList.remove("opacity-50");
      const statusEl = el.querySelector(".status");
      if (statusEl) statusEl.textContent = "✅";
    }
  }
}
