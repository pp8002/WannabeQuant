// Dynamické načítání lekce při kliknutí na curriculum odkaz
document.addEventListener("DOMContentLoaded", () => {
  const lessonContainer = document.getElementById("lesson-container");
  const lessonLinks = document.querySelectorAll(".lesson-link");

  // Výchozí lekce (zatím lesson1.html)
  loadLesson("math1-linear-algebra/lesson1.html");

  lessonLinks.forEach(link => {
    link.addEventListener("click", () => {
      const lessonFile = link.getAttribute("data-lesson");
      loadLesson(`math1-linear-algebra/${lessonFile}`);
    });
  });

  function loadLesson(file) {
    fetch(file)
      .then(res => res.text())
      .then(html => {
        lessonContainer.innerHTML = html;
      })
      .catch(err => {
        lessonContainer.innerHTML = `<p class="text-red-500">❌ Nelze načíst lekci: ${file}</p>`;
        console.error("Chyba načítání:", err);
      });
  }
});
