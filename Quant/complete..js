// ✅ Importuj Firebase moduly
import { auth, db } from './firebase-init.js';
import { doc, setDoc, updateDoc, getDoc } from 'https://www.gstatic.com/firebasejs/12.1.0/firebase-firestore.js';
import { onAuthStateChanged } from 'https://www.gstatic.com/firebasejs/12.1.0/firebase-auth.js';

// ✅ Název lekce (mělo by odpovídat ID v databázi)
const currentLessonId = "math1_lesson1";  // např. "math1_lesson1", "math2_lesson3" atd.

// ✅ Počkej na přihlášení uživatele
onAuthStateChanged(auth, async (user) => {
  if (user) {
    const completeBtn = document.getElementById('mark-complete');
    if (completeBtn) {
      completeBtn.addEventListener('click', async () => {
        try {
          const userRef = doc(db, 'users', user.uid);
          const userSnap = await getDoc(userRef);

          // Pokud dokument neexistuje, vytvoř ho
          if (!userSnap.exists()) {
            await setDoc(userRef, {
              xp: 10,
              progress: {
                [currentLessonId]: true
              }
            });
          } else {
            // Jinak aktualizuj stávající
            await updateDoc(userRef, {
              [`progress.${currentLessonId}`]: true
            });

            // Volitelně: přičti XP za dokončení lekce
            const existingXP = userSnap.data().xp || 0;
            await updateDoc(userRef, {
              xp: existingXP + 10
            });
          }

          // ✅ Upozornění
          alert("✅ Lesson marked as complete and XP awarded!");
        } catch (error) {
          console.error("❌ Error saving progress:", error);
          alert("Something went wrong while saving your progress.");
        }
      });
    }
  }
});
