/* ================= ROUND 13: from your round 12 review ================= */
/* Loads after round 12 and before round 7. Printer take A stays without its label (B is cut), the name tag redraws
   your name in a new hand when you tap it, and TENNIS is either gone or switched up for a racket that asks to hit. */
const R13=(()=>{
const L=R6.lib,W=L.W,baseWire=L.wire;
// the printer, no words on it
W.print13=()=>W.print12a().replace('<span class="p12-k">3D printer</span>','').replace('wd-p12 p12a','wd-p12 p12a p13');
// name tag: still on its own; a tap wipes the name and writes it again in the next hand
const HANDS=[['Caveat',1,700],['Permanent Marker',.74,400],['Homemade Apple',.62,400],['Gochi Hand',.92,400],['Nothing You Could Do',.72,400]];
let fontsAsked=false;
W.name13=()=>`<div class="wd wd-name n9 n13" role="button" tabindex="0" aria-label="Name tag: David. Tap to write it in another hand." data-h="0"><b>HELLO</b><small>my name is</small><span class="nm"><span class="nm-w"><span class="nm-i">David</span><i class="nm-pen" aria-hidden="true"></i></span></span></div>`;
// TENNIS, switched up: a racket and the line from your Say hi page
W.hit13=()=>`<div class="wd wd-hit13" role="button" tabindex="0" aria-label="Tennis racket: let's hit? Tap to swing."><svg class="h13-r" viewBox="0 0 60 60" aria-hidden="true"><g class="h13-sw"><rect x="27.2" y="33" width="5.6" height="22" rx="2.4" fill="#2b313d"/><rect x="27.2" y="47" width="5.6" height="9" rx="2" fill="#8a2433"/><ellipse cx="30" cy="19" rx="14" ry="17" fill="#fff" stroke="#8a2433" stroke-width="3.4"/><path d="M19 9h22M17 14h26M16.5 19h27M17 24h26M19 29h22M24 4v30M30 2.5v33M36 4v30" stroke="#c9ced8" stroke-width="1"/></g><circle class="h13-b" cx="50" cy="10" r="5.4" fill="#d7ea4f" stroke="#8a9a22" stroke-width="1"/></svg><span class="h13-t">let's hit?</span></div>`;

function wire13(face){
  const tap=(el,fn)=>{el.addEventListener('click',fn);el.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();fn(e)}})};
  const alive=()=>face.isConnected;
  if(!fontsAsked&&face.querySelector('.n13')&&document.fonts){fontsAsked=true;HANDS.forEach(h=>document.fonts.load(`${h[2]} 2rem "${h[0]}"`).catch(()=>{}))}
  face.querySelectorAll('.n13').forEach(el=>{const nm=el.querySelector('.nm');let tm=0;
    const set=i=>{el.dataset.h=i;nm.style.fontFamily=`"${HANDS[i][0]}",var(--font-hand)`;nm.style.setProperty('--hs',HANDS[i][1]);nm.style.fontWeight=HANDS[i][2]};
    tap(el,()=>{clearTimeout(tm);const i=(+el.dataset.h+1)%HANDS.length;
      if(reduce){set(i);return}
      el.classList.remove('go');el.classList.add('out');
      tm=setTimeout(()=>{if(!alive())return;set(i);el.classList.remove('out');void el.offsetWidth;el.classList.add('go')},260)})});
  face.querySelectorAll('.wd-hit13').forEach(el=>tap(el,()=>{if(reduce)return;el.classList.remove('sw');void el.offsetWidth;el.classList.add('sw')}));
}
L.wire=function(face,ctx){baseWire(face,ctx);wire13(face)};

const SETS={
  // take A: TENNIS gone; the ball stays
  coverA:()=>`${W.name13()}${W.now()}${W.hike()}${W.scan()}${W.puzzle()}${W.print13()}${W.pal('raccoon')}${W.blank()}${W.ball()}`,
  // take B: TENNIS switched for the racket
  coverB:()=>`${W.name13()}${W.now()}${W.hike()}${W.hit13()}${W.scan()}${W.puzzle()}${W.print13()}${W.pal('raccoon')}${W.blank()}${W.ball()}`,
};
return {SETS,HANDS};
})();
