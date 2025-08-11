// firebase-init.js
import { initializeApp } from "https://www.gstatic.com/firebasejs/12.1.0/firebase-app.js";
import { getAuth } from "https://www.gstatic.com/firebasejs/12.1.0/firebase-auth.js";
import { getFirestore } from "https://www.gstatic.com/firebasejs/12.1.0/firebase-firestore.js";

// 🔐 Tady vlož svou vlastní konfiguraci Firebase (z konzole)
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

// Exportujeme Firebase služby
export const auth = getAuth(app);
export const db = getFirestore(app);
