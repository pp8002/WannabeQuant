// firebase-init.js

// ✅ Firebase imports (z CDN, správné pořadí)
import { initializeApp, getApps } from "https://www.gstatic.com/firebasejs/12.1.0/firebase-app.js";
import { getAuth } from "https://www.gstatic.com/firebasejs/12.1.0/firebase-auth.js";
import { getFirestore } from "https://www.gstatic.com/firebasejs/12.1.0/firebase-firestore.js";

// ✅ Konfigurace načtená z env.js (musíš mít <script src="/env.js"></script> v HTML)
const firebaseConfig = {
  apiKey: window.FIREBASE_API_KEY,
  authDomain: "quant-25068.firebaseapp.com",
  projectId: "quant-25068",
  storageBucket: "quant-25068.firebasestorage.app",
  messagingSenderId: "994280892133",
  appId: "1:994280892133:web:d23746af3460f3300f960c",
  measurementId: "G-1G0LNME5GH"
};

// ✅ Inicializuj Firebase pouze pokud ještě nebyl inicializován
const app = getApps().length === 0 ? initializeApp(firebaseConfig) : getApps()[0];

// ✅ Získej služby
const auth = getAuth(app);
const db = getFirestore(app);

// ✅ Exportuj pro další soubory
export { app, auth, db };
