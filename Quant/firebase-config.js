// firebase-config.js
import { initializeApp } from "https://www.gstatic.com/firebasejs/10.12.2/firebase-app.js";
import { getAuth, GoogleAuthProvider, signInWithPopup } from "https://www.gstatic.com/firebasejs/10.12.2/firebase-auth.js";

const firebaseConfig = {
  apiKey: "AIzaSyBcJbbjNDvZqLvGcfevfJVX6jKixHmYAwI",
  authDomain: "quant-5589e.firebaseapp.com",
  projectId: "quant-5589e",
  storageBucket: "quant-5589e.firebasestorage.app",
  messagingSenderId: "795935839648",
  appId: "1:795935839648:web:31e0a952fad4d1e60400c5",
  measurementId: "G-DQ0R4TCBFC"
};

// Inicializace Firebase
const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
const provider = new GoogleAuthProvider();

export { auth, provider, signInWithPopup };
