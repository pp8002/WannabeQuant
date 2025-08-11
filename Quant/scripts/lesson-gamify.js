// lesson-gamify.js

// ✅ Tato funkce bude reagovat na dokončení lekce a přidá XP, uloží progress atd.

window.addEventListener("lessonCompleted", async (e) => {
  const lessonId = e.detail.id; // např. "math1_lesson1"
  const currentUserId = localStorage.getItem("current_user");
  if (!currentUserId) return;

  const users = JSON.parse(localStorage.getItem("quant_users")) || {};
  const user = users[currentUserId] || {
    xp: 0,
    level: 1,
    streak: 0,
    badges: [],
    progress: {}
  };

  // Pokud už lekce byla dokončena, nepočítej XP znovu
  if (user.progress[lessonId]?.completed) return;

  // 🎁 Odměny za dokončení lekce
  const XP_REWARD = 20;
  user.xp += XP_REWARD;
  user.progress[lessonId] = { completed: true, timestamp: Date.now() };

  // Levelování (každých 100 XP -> nový level)
  if (user.xp >= user.level * 100) {
    user.level += 1;
  }

  // Uložení zpět
  users[currentUserId] = user;
  localStorage.setItem("quant_users", JSON.stringify(users));

  // 🎉 Toast nebo alert
  alert("🎉 Lesson completed! +" + XP_REWARD + " XP");
});
