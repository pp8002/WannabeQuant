// login.js

import { startGoogleSignIn } from "./firebase-init.js";

const btn = document.getElementById("googleSignIn");
if (!btn) {
  console.error("Login button #googleSignIn not found on page");
} else {
  btn.addEventListener("click", async () => {
    try {
      // Use the robust implementation from firebase-init.js
      await startGoogleSignIn();
    } catch (error) {
      alert("Chyba při přihlášení: " + (error?.message || error));
      console.error(error);
    }
  });
}
