// firebase-init.js
import { initializeApp } from "https://www.gstatic.com/firebasejs/12.1.0/firebase-app.js";
import { getAuth } from "https://www.gstatic.com/firebasejs/12.1.0/firebase-auth.js";
import { getFirestore } from "https://www.gstatic.com/firebasejs/12.1.0/firebase-firestore.js";

// 🔐 Tady vlož svou vlastní konfiguraci Firebase (z konzole)
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

// Exportujeme Firebase služby
export const auth = getAuth(app);
export const db = getFirestore(app);
