// lesson1-gamify.js – verze s Firebase zápisem

import { app } from '../../firebase-init.js';
import {
  getFirestore,
  doc,
  getDoc,
  updateDoc,
  setDoc,
} from 'https://www.gstatic.com/firebasejs/12.1.0/firebase-firestore.js';

const db = getFirestore(app);
const uid = localStorage.getItem('current_user');

document.addEventListener("DOMContentLoaded", function () {
  const completeBtn = document.querySelector(".btn");

  completeBtn.addEventListener("click", async function () {
    if (!uid) return alert("Please log in first!");

    const userRef = doc(db, 'users', uid);
    const snap = await getDoc(userRef);

    if (!snap.exists()) {
      alert("❌ User not found.");
      return;
    }

    const userData = snap.data();
    const progress = userData.progress || {};
    const xp = userData.xp || 0;
    const badges = userData.badges || [];

    if (progress["math1_lesson1"]?.completed) {
      alert("✔️ You’ve already completed this lesson.");
      return;
    }

    // Ulož nový pokrok a XP
    progress["math1_lesson1"] = { completed: true };

    await updateDoc(userRef, {
      xp: xp + 50,
      progress,
      badges: badges.includes("Vector Master")
        ? badges
        : [...badges, "Vector Master"],
    });

    alert("✅ Lesson complete! +50 XP\n🏅 You unlocked: Vector Master");
  });
});
