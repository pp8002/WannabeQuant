// login.js

import { auth } from "./firebase-init.js";
import { GoogleAuthProvider, signInWithPopup } from "https://www.gstatic.com/firebasejs/12.1.0/firebase-auth.js";

const provider = new GoogleAuthProvider();

document.getElementById("google-login").addEventListener("click", async () => {
  try {
    const result = await signInWithPopup(auth, provider);
    const user = result.user;

    // Ulož informace o uživateli do localStorage
    localStorage.setItem("current_user", JSON.stringify({
      name: user.displayName,
      email: user.email,
      uid: user.uid
    }));

    // Přesměrování na account.html
    window.location.href = "account.html";
  } catch (error) {
    alert("Chyba při přihlášení: " + error.message);
    console.error(error);
  }
});
