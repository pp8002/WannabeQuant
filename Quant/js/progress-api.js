// === progress-api.js ===
// Jednotné API pro ukládání progresu do users/{uid}.progress
// - když není přihlášeno: queue do localStorage
// - při přihlášení: queue se slije a uloží do Firestore

import { auth, getUserProgress, saveUserProgress } from './firebase-init.js';
import { onAuthStateChanged } from 'https://www.gstatic.com/firebasejs/12.1.0/firebase-auth.js';

const QUEUE_KEY = 'qq_progress_queue_v1';

// --- util: hluboké sloučení (shallow + vnořené objekty)
function deepMerge(target = {}, source = {}) {
  const out = Array.isArray(target) ? [...target] : { ...target };
  Object.keys(source || {}).forEach((key) => {
    const sv = source[key];
    const tv = out[key];
    if (sv && typeof sv === 'object' && !Array.isArray(sv)) {
      out[key] = deepMerge(tv && typeof tv === 'object' ? tv : {}, sv);
    } else {
      out[key] = sv;
    }
  });
  return out;
}

// --- queue operace
function readQueue() {
  try { return JSON.parse(localStorage.getItem(QUEUE_KEY) || '[]'); }
  catch { return []; }
}
function writeQueue(arr) {
  localStorage.setItem(QUEUE_KEY, JSON.stringify(arr || []));
}
function enqueuePatch(patch) {
  const q = readQueue();
  q.push({ t: Date.now(), patch });
  writeQueue(q);
}

// --- normalizace patche: povolíme obojí
//   1) saveProgress({progress: {k:v}})
//   2) saveProgress({k:v})
function normalizePatch(patch) {
  if (!patch || typeof patch !== 'object') return {};
  if ('progress' in patch && typeof patch.progress === 'object') return patch.progress;
  return patch;
}

// --- veřejné API ---

export function onUserReady(cb) {
  // vrací unsubscribe
  return onAuthStateChanged(auth, async (user) => {
    if (user?.uid) {
      // po přihlášení zkus flushnout queue
      await flushQueuedProgress();
      cb(user);
    } else {
      cb(null);
    }
  });
}

export async function loadProgress() {
  const uid = auth.currentUser?.uid;
  if (!uid) return {};
  const doc = await getUserProgress(uid);
  return (doc && doc.progress) || {};
}

export async function saveProgress(patch) {
  const uid = auth.currentUser?.uid;
  const norm = normalizePatch(patch);

  if (!Object.keys(norm).length) return { ok: true, queued: false };

  if (!uid) {
    // guest → do fronty
    enqueuePatch(norm);
    return { ok: true, queued: true };
    }
  try {
    // zapiš pod users/{uid}.progress (merge)
    await saveUserProgress(uid, { progress: norm });
    return { ok: true, queued: false };
  } catch (e) {
    console.error('saveProgress error:', e);
    // fallback do fronty (aby se nic neztratilo)
    enqueuePatch(norm);
    return { ok: false, queued: true, error: String(e) };
  }
}

export async function flushQueuedProgress() {
  const uid = auth.currentUser?.uid;
  if (!uid) return false;

  const q = readQueue();
  if (!q.length) return false;

  // poskládej do jednoho patche (poslední vyhrává)
  let merged = {};
  for (const { patch } of q) merged = deepMerge(merged, patch);

  try {
    await saveUserProgress(uid, { progress: merged });
    writeQueue([]);
    return true;
  } catch (e) {
    console.error('flushQueuedProgress error:', e);
    return false;
  }
}
