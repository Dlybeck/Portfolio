/* ================= ROUND 11: the pages inside ================= */
/* Three looks for the inside pages that carry the round 10 cover in: the same paper and band ideas, and a few of the
   cover's own stickers stuck on the page they belong to. The page words stay as they are. */
const R11=(()=>{
const W=R6.lib.W;
// which cover sticker goes on which page: [sticker, its width on the cover in cqw, width on the page in px, tilt]
const ACC={
  me:      [()=>W.hike(),'hike',36,92,5],
  scribblescan:[(r12)=>W.pal(r12?'raccoon':'octopus'),'oct',19,64,7],
  site:    [()=>W.print(),'print',21,58,-5,true],
  work:    [()=>W.pal('raccoon'),'rac',19,64,-5,true],
  work12:  [()=>W.now().replace('<b></b><span></span>','<b>now</b><span>AI tools at Denali</span>').replace('wd-now','wd-now live'),'now',40,132,-2],
  printing:[()=>W.puzzle(),'puz',26,62,6],
  tennis:  [()=>W.ball(),'ball',14,54,0],
  say:     [()=>W.name9('still'),'name',44,98,-4],
};
const DETAIL=new Set(['scribblescan','site','printing','tennis']);
const C=460; // the cover width the stickers are drawn for; each one is zoomed down to its page size
const quiet=h=>h.replace(/\srole="button"/g,'').replace(/\stabindex="0"/g,'').replace(/\saria-label="[^"]*"/g,'');
function accent(id,r12){
  // round 12: the octopus is cut, so the raccoon moves to ScribbleScan and Work gets the now sticker; the site page has none
  if(r12){if(id==='work')id='work12';else if(ACC[id]&&ACC[id][5])return ''}
  const a=ACC[id];if(!a)return '';
  const [mk,key,pct,w,tilt]=a;
  let h=quiet(mk(r12));
  // the puzzle is drawn still: the logo one slide from solved
  if(key==='puz'){const pos=[0,1,2,3,4,5,6,8];
    h=h.replace('<div class="pz" role="group"',`<div class="pz" style="--logo-img:url('${LOGO}')"`).replace(/<button type="button" class="pz-t" data-i="(\d)"[^>]*><\/button>/g,(m,i)=>{i=+i;const p=pos[i];
      return `<span class="pz-t" style="background-position:${(i%3)*50}% ${Math.floor(i/3)*50}%;translate:${(p%3)*100}% ${Math.floor(p/3)*100}%"></span>`})}
  const end=h.lastIndexOf('</div>');
  h=h.slice(0,end)+'<i class="wd-sh"></i>'+(key==='name'?'<i class="wd-curl"></i>':'')+h.slice(end);
  const z=(w/(C*pct/100)).toFixed(4);
  // the box is a whole cover wide so the sticker's own sizes work; it hangs off to the left and the sticker sits at its right end
  return `<span class="acc acc-${key}" style="--tilt:${tilt}deg;width:${w}px" aria-hidden="true"><span class="acc-c cv7 cv7-cover10 tr-worn tr-vinyl tr-r9" style="width:${C}px;zoom:${z};margin-left:${-(C*(1-pct/100)).toFixed(1)}px">${h}</span></span>`;
}
window.PAGE_DECO=(root,id,half,h,P)=>{
  if(!root.closest('.in-worn,.in-scrap,.in-clean'))return h;
  const want=DETAIL.has(id)?(P?0:1):0;
  if(half!==want||!ACC[id])return h;
  return h.replace(/(<div class="x"[^>]*>)/,`$1${accent(id,!!root.closest('.in-r12'))}`);
};
return {accent};
})();
