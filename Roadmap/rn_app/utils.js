import AsyncStorage from "@react-native-async-storage/async-storage";

const PROGRESS_KEY = "progress_v1";

async function readAll() {
  try {
    const raw = await AsyncStorage.getItem(PROGRESS_KEY);
    return raw ? JSON.parse(raw) : { topics: {} };
  } catch {
    return { topics: {} };
  }
}
async function writeAll(obj) {
  await AsyncStorage.setItem(PROGRESS_KEY, JSON.stringify(obj));
}

export async function getTopicProgress(topicId) {
  const state = await readAll();
  const bucket = state.topics?.[String(topicId)];
  return bucket?.tasksDone ?? [];
}

export async function setTaskDone(topicId, index, done) {
  const state = await readAll();
  const id = String(topicId);
  state.topics[id] ??= { tasksDone: [], completed: false };
  const set = new Set(state.topics[id].tasksDone);
  if (done) set.add(index); else set.delete(index);
  state.topics[id].tasksDone = Array.from(set).sort((a,b)=>a-b);
  await writeAll(state);
  return state.topics[id];
}

export async function markTopicCompleted(topicId) {
  const state = await readAll();
  const id = String(topicId);
  state.topics[id] ??= { tasksDone: [], completed: false };
  state.topics[id].completed = true;
  await writeAll(state);
  return state.topics[id];
}

export async function isTopicCompleted(topicId) {
  const state = await readAll();
  return !!state.topics?.[String(topicId)]?.completed;
}
