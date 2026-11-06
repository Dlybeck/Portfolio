/* ================= ROUND 18 (shown as round 17): one longer page per story ================= */
/* From his note on the flowing pages: "The 1 longer page is better in that case. I have no problem with scroll".
   So each story is back on one page that scrolls, with the same roomy pictures and sections as the flowing pages.
   Swipe stays only on the real rows of pictures: site version snapshots, the themes, the 3D models.
   On desktop the contents list stays on the left and the whole story scrolls on the right.
   Same words and pictures. Only mounts with the s18 class. */
(()=>{
if(!window.C14||!window.C17)return;
const prev=window.C14.pages,base=R14.pages,{CH,LISTED}=window.C17;
/* later sections lose their page-title size and get a quiet rule above them */
const sub=h=>h.replace(/<h2( class="h17")?>/g,'<h3 class="h18">').replace(/<\/h2>/g,'</h3>');
const sec=([h,sw],i)=>{
  if(i>0)h=sub(h);
  return sw?`<section class="s18-sec" data-sw16="1">${h}</section>`:`<section class="s18-sec">${h}</section>`;
};
function join(id,from){
  let ch=CH[id].slice(from);
  if(id==='gaming'&&from===0){ // one grid of all twenty covers, no second heading
    const all=CH[id].map(c=>c[0]).join('').replace(/<h2>More favorites<\/h2>/,'').replace(/<\/div>\s*<div class="covers c17">/,'');
    ch=[[all]];
  }
  return `<div class="x">${ch.map((c,i)=>sec(c,i)).join('')}</div>`;
}
function pages(id,P,o){
  const root=o.root;
  if(!root||!root.classList.contains('s18')||!CH[id])return prev(id,P,o);
  if(id==='printing')base('printing',P,o); // loads the 3D viewer
  if(P)return [join(id,0)];
  if(LISTED.has(id))return [base(id,P,o)[0],join(id,0)];
  return [`<div class="x">${sec(CH[id][0],0)}</div>`,join(id,1)];
}
window.C14.pages=pages;
})();
