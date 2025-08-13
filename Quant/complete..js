// ✅ Import Firebase moduly
import { auth, db } from './firebase-init.js';
import { doc, setDoc, updateDoc, getDoc, increment } from 'https://www.gstatic.com/firebasejs/12.1.0/firebase-firestore.js';
import { onAuthStateChanged } from 'https://www.gstatic.com/firebasejs/12.1.0/firebase-auth.js';

// ✅ Lesson ID (musí odpovídat databázi)
const currentLessonId = "math1_lesson1";  
const nextLessonId = "math1_lesson2";     
const lessonXP = 150; // XP za tuto lekci

// ✅ Funkce pro ověření, zda jsou všechny checklist položky hotové
function allChecklistCompleted() {
  const allItems = document.querySelectorAll('.checklist-item input');
  const completedItems = document.querySelectorAll('.checklist-item input:checked');
  return allItems.length > 0 && allItems.length === completedItems.length;
}

// ✅ Po přihlášení uživatele
onAuthStateChanged(auth, async (user) => {
  if (user) {
    const completeBtn = document.getElementById('mark-complete');
    if (completeBtn) {
      completeBtn.addEventListener('click', async () => {

        if (!allChecklistCompleted()) {
          alert("⚠️ Please complete all checklist items before marking the lesson as complete.");
          return;
        }

        try {
          const userRef = doc(db, 'users', user.uid);
          const userSnap = await getDoc(userRef);

          // Pokud dokument uživatele neexistuje
          if (!userSnap.exists()) {
            await setDoc(userRef, {
              xp: lessonXP,
              progress: {
                [currentLessonId]: {
                  completed: true,
                  completedAt: new Date()
                },
                [nextLessonId]: { unlocked: true }
              }
            });
          } else {
            // ✅ Ulož progress a odemkni další lekci
            await updateDoc(userRef, {
              [`progress.${currentLessonId}`]: {
                completed: true,
                completedAt: new Date()
              },
              [`progress.${nextLessonId}.unlocked`]: true,
              xp: increment(lessonXP)
            });
          }

          alert(`🎉 Lesson completed! You earned ${lessonXP} XP and unlocked the next lesson.`);
          window.location.href = `../${nextLessonId.replace('_', '/')}.html`; // přesměrování na další lekci

        } catch (error) {
          console.error("❌ Error saving progress:", error);
          alert("Something went wrong while saving your progress.");
        }
      });
    }
  }
});
