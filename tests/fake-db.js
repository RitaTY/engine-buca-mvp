// Fake claude.use('db'/'user') backed by localStorage, synced across tabs with the storage event.
(()=>{const K='FAKEDB';const uid=sessionStorage.getItem('uid')||('u'+Math.random().toString(36).slice(2,7));sessionStorage.setItem('uid',uid);
const load=()=>JSON.parse(localStorage.getItem(K)||'{}'),store=o=>localStorage.setItem(K,JSON.stringify(o));
const subs=[];const snapDoc=(p)=>{const d=load()[p];return {id:p.split('/').pop(),exists:!!d,data:()=>d?JSON.parse(JSON.stringify(d)):undefined,metadata:{fromCache:false,hasPendingWrites:false}}};
const snapCol=(c)=>{const all=load();const docs=Object.keys(all).filter(k=>k.startsWith(c+'/')&&k.split('/').length===c.split('/').length+1).sort().map(snapDoc);return {docs,size:docs.length,empty:!docs.length,docChanges:()=>[],metadata:{fromCache:false,hasPendingWrites:false}}};
const fire=()=>subs.forEach(s=>setTimeout(()=>s.cb(s.col?snapCol(s.path):snapDoc(s.path)),5));
window.addEventListener('storage',e=>{if(e.key===K)fire()});
const doc=p=>({id:p.split('/').pop(),path:p,get:async()=>snapDoc(p),set:async d=>{const a=load();a[p]=d;store(a);await new Promise(r=>setTimeout(r,20));fire()},delete:async()=>{const a=load();delete a[p];store(a);fire()},update:async d=>{const a=load();a[p]=Object.assign(a[p]||{},d);store(a);fire()},onSnapshot:(cb)=>{const s={path:p,cb};subs.push(s);setTimeout(()=>cb(snapDoc(p)),10);return()=>{}}});
const col=p=>({path:p,doc:id=>doc(p+'/'+id),get:async()=>snapCol(p),onSnapshot:(cb)=>{const s={path:p,cb,col:true};subs.push(s);setTimeout(()=>cb(snapCol(p)),10);return()=>{}}});
const db={doc,collection:col};const names={};
const user={id:async()=>uid,can:async()=>true,canEdit:async()=>true,isOwner:async()=>true,profiles:async ids=>Object.fromEntries(ids.map(i=>[i,{name:'Tester '+i.slice(1,4).toUpperCase()}]))};
window.claude={use:async n=>n==='db'?db:n==='user'?user:null};})();
