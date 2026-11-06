/* ================= ROUND 16: a mix, page by page ================= */
/* Swipe cards where a page is really a list of pictures, short pages where it tells a story.
   Each page says which it uses, and one tap swaps it (kept in this browser only). */
(()=>{
if(!window.C14)return;
const viaB=window.C14.pages,base=R14.pages;
const KEY='pf-lay16';
const DEF={scribblescan:'a',site:'a',programs:'a',printing:'a',gaming:'a',nba:'b',planner:'b',work:'b'};
let over={};try{over=JSON.parse(localStorage.getItem(KEY)||'{}')||{}}catch(_){}
const mode=id=>over[id]||DEF[id];
const last=new WeakMap();
const note=(id,m)=>`<button type="button" class="lay16" data-lay="${id}"><span>${m==='a'?'Swipe cards':'Short page'}</span><u>try ${m==='a'?'a short page':'swipe cards'}</u></button>`;
const mark=(h,sw)=>sw?h.replace('<div class="x"','<div class="x" data-sw16="1"'):h;
const addNote=(h,id,m)=>h.replace(/<\/div>\s*$/,note(id,m)+'</div>');
function pages(id,P,o){
  const root=o.root;
  if(!root||!root.classList.contains('s16')||!(id in DEF))return viaB(id,P,o);
  last.set(root,{P,o});
  const m=mode(id);
  let r;
  if(m==='b')r=viaB(id,P,o);
  else{root.querySelectorAll('.st15').forEach(s=>s.remove());r=base(id,P,o).slice();
    if(id==='work'&&!P)r=r.map(h=>mark(h,true));else r[r.length-1]=mark(r[r.length-1],true)}
  r[r.length-1]=addNote(r[r.length-1],id,m);
  return r;
}
window.C14.pages=pages;
/* one tap swaps this page's layout and redraws it in place */
document.addEventListener('click',e=>{
  const b=e.target.closest('.lay16');if(!b)return;e.stopPropagation();
  const root=b.closest('.c14'),st=root&&last.get(root);if(!st)return;
  const id=b.dataset.lay;over[id]=mode(id)==='a'?'b':'a';try{localStorage.setItem(KEY,JSON.stringify(over))}catch(_){}
  for(const r of document.querySelectorAll('.c14.s16')){const s=last.get(r);if(!s)continue;
    const book=r.querySelector('.nb-book');const ins=[...book.querySelectorAll(':scope>.nb-page:not(.st15) .nb-in')];
    if(!ins.some(n=>n.querySelector(`.x[data-pg="${id}"]`)))continue;
    const hs=pages(id,s.P,s.o).map((h,i)=>{h=h.replace('<div class="x"',`<div class="x" data-pg="${id}" data-half="${i}"`);return typeof window.PAGE_DECO==='function'?window.PAGE_DECO(r,id,i,h,s.P):h});
    ins.forEach((n,i)=>{if(hs[i]!=null){n.innerHTML=hs[i];n.scrollTop=0}})}
},true);
})();
