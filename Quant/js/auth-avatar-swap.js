// === auth-avatar-swap.js ===
// Nenarušuje nic dalšího: jen sleduje přihlášení a přepíná ikonku na avatar.

import { auth } from './firebase-init.js';
import { onAuthStateChanged } from 'https://www.gstatic.com/firebasejs/12.1.0/firebase-auth.js';

const avatarEl   = document.getElementById('profileAvatar');
const fallbackEl = document.getElementById('profileFallbackIcon');

function showFallback() {
  if (!fallbackEl || !avatarEl) return;
  avatarEl.classList.add('hidden');
  fallbackEl.classList.remove('hidden');
}

function showAvatar(src) {
  if (!fallbackEl || !avatarEl) return;
  if (!src) return showFallback();
  avatarEl.src = src;
  avatarEl.onload = () => {
    fallbackEl.classList.add('hidden');
    avatarEl.classList.remove('hidden');
  };
  avatarEl.onerror = showFallback;
}

// Reaguj až na REÁLNÝ login:
onAuthStateChanged(auth, (user) => {
  if (user) {
    // zobraz fotku (pokud není, nech fallback)
    showAvatar(user.photoURL || '');
  } else {
    showFallback();
  }
});
