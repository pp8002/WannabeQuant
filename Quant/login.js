// login.js
import { initializeApp } from "https://www.gstatic.com/firebasejs/12.1.0/firebase-app.js";
import { getAuth, GoogleAuthProvider, signInWithPopup } from "https://www.gstatic.com/firebasejs/12.1.0/firebase-auth.js";

// ⚙️ Vlož svůj vlastní Firebase config
const firebaseConfig = {
  apiKey: YOUR_API_KEY,
   authDomain: "quant-5589e.firebaseapp.com",
    projectId: "quant-5589e",
    storageBucket: "quant-5589e.firebasestorage.app",
    messagingSenderId: "795935839648",
    appId: "1:795935839648:web:9b0cfeaeb1e590f90400c5",
    measurementId: "G-6SL04E2WVJ"
  };


const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
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
