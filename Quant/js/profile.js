// ====== PŘIPOJENÍ FIREBASE (centralizované) ======
import { auth, startGoogleSignIn } from "./firebase-init.js";

document.addEventListener("DOMContentLoaded", async () => {
  console.log("✅ profile.js načten");

  // ===== FUNKCE PRO UŽIVATELE =====
  function getAllUsers() {
    return JSON.parse(localStorage.getItem("quant_users")) || {};
  }

  function saveAllUsers(users) {
    localStorage.setItem("quant_users", JSON.stringify(users));
  }

  function getCurrentUserKey() {
    return localStorage.getItem("current_user");
  }

  function setCurrentUserKey(username) {
    localStorage.setItem("current_user", username);
  }

  function getCurrentUser() {
    const users = getAllUsers();
    const key = getCurrentUserKey();
    return users[key];
  }

  function saveCurrentUserData(data) {
    const users = getAllUsers();
    const key = getCurrentUserKey();
    users[key] = { ...users[key], ...data };
    saveAllUsers(users);
  }

  // ===== ELEMENTY Z DOMU =====
  const usernameInput = document.getElementById("profileName");
  const saveBtn = document.getElementById("saveProfileBtn");
  const logoutBtn = document.getElementById("logoutBtn");
  const xpDisplay = document.getElementById("profileXP");
  const levelDisplay = document.getElementById("profileLevel");
  const streakDisplay = document.getElementById("profileStreak");
  const googleBtn = document.getElementById("googleLoginBtn");

  const user = getCurrentUser();

  console.log("🎯 Elementy načteny:", {
    usernameInput,
    saveBtn,
    logoutBtn,
    xpDisplay,
    levelDisplay,
    streakDisplay,
    googleBtn,
    user
  });

  // ===== PŘEDVYPLNĚNÍ PROFILU =====
  if (user) {
    if (usernameInput) usernameInput.value = getCurrentUserKey();
    if (xpDisplay) xpDisplay.textContent = `⚡ XP: ${user.xp}`;
    if (levelDisplay) levelDisplay.textContent = `📈 Level ${user.level}`;
    if (streakDisplay) streakDisplay.textContent = `🔥 Streak: ${user.streak}`;
  }

  // === ULOŽIT JMÉNO ===
  if (saveBtn) {
    saveBtn.addEventListener("click", () => {
      const newName = usernameInput.value.trim();
      const oldName = getCurrentUserKey();

      if (!newName || newName === oldName) {
        alert("Zadej jiné jméno!");
        return;
      }

      const users = getAllUsers();

      if (users[newName]) {
        alert("Toto jméno už existuje.");
        return;
      }

      users[newName] = users[oldName];
      delete users[oldName];
      saveAllUsers(users);
      setCurrentUserKey(newName);
      alert("✅ Username updated! Redirecting...");
      window.location.href = "account.html";
    });
  }

  // === ODJENOUT ===
  if (logoutBtn) {
    logoutBtn.addEventListener("click", () => {
      localStorage.removeItem("current_user");
      window.location.href = "index.html";
    });
  }

  // ===== GOOGLE LOGIN BUTTON (popup, centralizované) =====
  if (googleBtn) {
    googleBtn.addEventListener("click", async () => {
      try {
        await startGoogleSignIn();
      } catch (e) {
        console.error("❌ Login error:", e?.code, e?.message || e);
        alert("Chyba při přihlášení: " + (e?.message || e));
      }
    });
  }
});
