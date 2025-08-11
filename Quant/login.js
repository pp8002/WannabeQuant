// login.js
import { initializeApp } from "https://www.gstatic.com/firebasejs/12.1.0/firebase-app.js";
import { getAuth, GoogleAuthProvider, signInWithPopup } from "https://www.gstatic.com/firebasejs/12.1.0/firebase-auth.js";

// ⚙️ Vlož svůj vlastní Firebase config
const firebaseConfig = {
  apiKey: YOUR_API_KEY,
    authDomain: "quant-25068.firebaseapp.com",
  projectId: "quant-25068",
  storageBucket: "quant-25068.firebasestorage.app",
  messagingSenderId: "994280892133",
  appId: "1:994280892133:web:d23746af3460f3300f960c",
  measurementId: "G-1G0LNME5GH"
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
