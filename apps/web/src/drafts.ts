import { newId, type Generation } from "./client";
export type LocalDraft = {
  draft: Generation;
  title?: string;
  baseRevision: number | null;
  editedAt: number;
  dirty: boolean;
  projectKey?: string;
  tabId?: string;
};
function open(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const r = indexedDB.open("museforge-workspace", 1);
    r.onupgradeneeded = () => r.result.createObjectStore("drafts");
    r.onsuccess = () => resolve(r.result);
    r.onerror = () => reject(r.error);
  });
}
export async function readDraft(key: string): Promise<LocalDraft | undefined> {
  const db = await open();
  return new Promise((resolve, reject) => {
    const tx = db.transaction("drafts");
    const store = tx.objectStore("drafts");
    const values = store.getAll();
    const keys = store.getAllKeys();
    tx.oncomplete = () => {
      const records = values.result
        .map((value: LocalDraft, index) => ({
          value,
          storageKey: String(keys.result[index]),
        }))
        .filter(
          ({ value, storageKey }) =>
            value.projectKey === key || storageKey === key,
        )
        .sort((a, b) => b.value.editedAt - a.value.editedAt);
      db.close();
      resolve(records[0]?.value);
    };
    tx.onerror = () => {
      db.close();
      reject(tx.error);
    };
  });
}
export async function writeDraft(key: string, value: LocalDraft) {
  const db = await open();
  return new Promise<void>((resolve, reject) => {
    const tx = db.transaction("drafts", "readwrite");
    const tabId = getTabId();
    tx.objectStore("drafts").put(
      { ...value, projectKey: key, tabId },
      `${key}:${tabId}`,
    );
    tx.oncomplete = () => {
      db.close();
      resolve();
    };
    tx.onerror = () => {
      db.close();
      reject(tx.error);
    };
  });
}

function getTabId() {
  const key = "museforge-draft-tab-id";
  let id = sessionStorage.getItem(key);
  if (!id) {
    id = newId();
    sessionStorage.setItem(key, id);
  }
  return id;
}
