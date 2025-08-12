// === Firebase importy ===
import { app } from '../firebase-init.js';
import { getFirestore, doc, getDoc } from 'https://www.gstatic.com/firebasejs/12.1.0/firebase-firestore.js';

const db = getFirestore(app);
const uid = localStorage.getItem('current_user');

// === Curriculum definice ===
const curriculum = {
  math1: [
    {
      id: "math1_lesson1",
      title: "Lesson 1: Vectors",
      path: "math1-linear-algebra/lesson1.html",
      requiredXP: 0,
    },
    {
      id: "math1_lesson2",
      title: "Lesson 2: Matrices",
      path: "math1-linear-algebra/lesson2.html",
      requiredXP: 20,
    },
    {
      id: "math1_lesson3",
      title: "Lesson 3: Determinants",
      path: "math1-linear-algebra/lesson3.html",
      requiredXP: 40,
    },
    {
      id: "math1_lesson4",
      title: "Lesson 4: Linear Systems",
      path: "math1-linear-algebra/lesson4.html",
      requiredXP: 60,
    },
    {
      id: "math1_lesson5",
      title: "Lesson 5: Eigenvalues & Eigenvectors",
      path: "math1-linear-algebra/lesson5.html",
      requiredXP: 80,
    },
  ]
};

async function renderCurriculum() {
  const container = document.querySelector('.sidebar');
  const userRef = doc(db, 'users', uid);
  const userSnap = await getDoc(userRef);

  if (!userSnap.exists()) {
    console.error("❌ Uživatel nenalezen.");
    return;
  }

  const userData = userSnap.data();
  const progress = userData.progress || {};
  const userXP = userData.xp || 0;

  // Titulek
  const header = document.createElement('h2');
  header.textContent = "📘 Math I: Linear Algebra";
  header.style.color = "#00ffcc";
  container.appendChild(header);

  curriculum.math1.forEach((lesson) => {
    const div = document.createElement('div');
    div.className = "lesson-title";
    div.textContent = lesson.title;


    // Zamčené lekce
    const locked = userXP < lesson.requiredXP;
    const completed = progress[lesson.id]?.completed;

    if (locked) {
      div.textContent += " 🔒";
      div.classList.add("opacity-50");
      div.style.pointerEvents = "none";
    }

    if (completed) {
      div.textContent += " ✅";
      div.classList.add("completed");
      div.classList.remove("opacity-50");
    }

    div.addEventListener("click", () => {
      document.getElementById("lessonFrame").src = lesson.path;
      document.querySelectorAll(".lesson-title").forEach(el => el.classList.remove("active"));
      div.classList.add("active");
    });

    container.appendChild(div);
  });
}

// === Start ===
document.addEventListener("DOMContentLoaded", () => {
  renderCurriculum();
});