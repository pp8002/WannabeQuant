// ====== PŘIPOJENÍ FIREBASE Z INIT ======
import { auth } from "./firebase-init.js";
import { GoogleAuthProvider, signInWithPopup } from "https://www.gstatic.com/firebasejs/12.1.0/firebase-auth.js";

const provider = new GoogleAuthProvider();

document.addEventListener("DOMContentLoaded", () => {
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

  const user = getCurrentUser();

  // DEBUG výpis pro jistotu
  console.log("🎯 Elementy načteny:", {
    usernameInput,
    saveBtn,
    logoutBtn,
    xpDisplay,
    levelDisplay,
    streakDisplay,
    user
  });

  if (user && usernameInput && saveBtn && logoutBtn) {
    usernameInput.value = getCurrentUserKey();
    if (xpDisplay) xpDisplay.textContent = `XP: ${user.xp}`;
    if (levelDisplay) levelDisplay.textContent = `Level ${user.level}`;
    if (streakDisplay) streakDisplay.textContent = `Streak: ${user.streak}🔥`;

    // === ULOŽIT JMÉNO A PŘESMĚROVAT ===
    saveBtn.addEventListener("click", () => {
      const newName = usernameInput.value.trim();
      const oldName = getCurrentUserKey();

      console.log("💾 Ukládání nového jména:", newName);

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

    // === ODJENOUT ===
    logoutBtn.addEventListener("click", () => {
      localStorage.removeItem("current_user");
      window.location.href = "index.html";
    });

  } else {
    console.error("❌ Některé prvky nebo uživatel chybí.");
  }

  // ===== GOOGLE LOGIN BUTTON =====
  const googleBtn = document.getElementById("googleLoginBtn");
  if (googleBtn) {
    googleBtn.addEventListener("click", () => {
      signInWithPopup(auth, provider)
        .then((result) => {
          const user = result.user;
          const username = user.displayName;

          // Uložení nebo vytvoření profilu v localStorage
          let users = JSON.parse(localStorage.getItem("quant_users")) || {};
          if (!users[username]) {
            users[username] = {
              xp: 0,
              level: 1,
              streak: 0,
              tasks: [],
              badges: []
            };
          }

          localStorage.setItem("quant_users", JSON.stringify(users));
          localStorage.setItem("current_user", username);

          // Přesměrování na účet
          window.location.href = "account.html";
        })
        .catch((error) => {
          alert("Chyba při přihlášení: " + error.message);
        });
    });
  }
});
