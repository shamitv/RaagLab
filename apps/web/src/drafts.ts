import type { Generation } from './client';
export type LocalDraft = {draft:Generation; baseRevision:number | null; editedAt:number; dirty:boolean};
function open(): Promise<IDBDatabase> {return new Promise((resolve,reject) => {
  const r = indexedDB.open('museforge-workspace',1);
  r.onupgradeneeded = () => r.result.createObjectStore('drafts');
  r.onsuccess = () => resolve(r.result); r.onerror = () => reject(r.error);
});}
export async function readDraft(key:string): Promise<LocalDraft | undefined> {
  const db = await open();
  return new Promise((resolve,reject) => {const r=db.transaction('drafts').objectStore('drafts').get(key); r.onsuccess=()=>resolve(r.result);r.onerror=()=>reject(r.error); r.transaction!.oncomplete=()=>db.close();});
}
export async function writeDraft(key:string, value:LocalDraft) {
  const db=await open();
  return new Promise<void>((resolve,reject)=>{const tx=db.transaction('drafts','readwrite');tx.objectStore('drafts').put(value,key);tx.oncomplete=()=>{db.close();resolve();};tx.onerror=()=>{db.close();reject(tx.error);};});
}
