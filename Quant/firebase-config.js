// firebase-config.js
import { initializeApp } from "https://www.gstatic.com/firebasejs/10.12.2/firebase-app.js";
import { getAuth, GoogleAuthProvider, signInWithPopup } from "https://www.gstatic.com/firebasejs/10.12.2/firebase-auth.js";

const firebaseConfig = {
  apiKey: YOUR_API_KEY,
  authDomain: "quant-25068.firebaseapp.com",
  projectId: "quant-25068",
  storageBucket: "quant-25068.firebasestorage.app",
  messagingSenderId: "994280892133",
  appId: "1:994280892133:web:d23746af3460f3300f960c",
  measurementId: "G-1G0LNME5GH"
};

// Inicializace Firebase
const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
const provider = new GoogleAuthProvider();

export { auth, provider, signInWithPopup };
