/* ================= ROUND 12: from your round 10 cover review ================= */
/* Loads after round 9 and before round 7. You cut the octopus, said some of the "now" text doesn't fit, and asked "3d?"
   of the printer, so the printer comes in two takes that say 3D plainly. */
const R12=(()=>{
const L=R6.lib,W=L.W,baseWire=L.wire;
// take A: a 3D printer you can tell is one: frame, rails, spool, nozzle, and the logo printed in layers
W.print12a=()=>`<div class="wd wd-p12 p12a" role="button" tabindex="0" aria-label="3D printer. Tap to print again."><div class="p12-m"><i class="p12-sp" aria-hidden="true"></i><i class="p12-fil" aria-hidden="true"></i><i class="p12-rl"></i><i class="p12-rr"></i><i class="p12-top"></i><div class="p12-o" style="--logo:url('${LOGO}')"></div><i class="p12-g"><i class="p12-n"></i></i><i class="p12-bed"></i></div><span class="p12-k">3D printer</span></div>`;
// take B: just the printed piece, a thick logo tile with layer lines, tipped so it reads as solid
W.print12b=()=>`<div class="wd wd-p12 p12b" role="button" tabindex="0" aria-label="A 3D printed logo. Tap to turn it."><div class="p12-t"><div class="p12-tile" style="--logo:url('${LOGO}')"><i class="p12-face"></i></div></div><span class="p12-k">3D printed</span></div>`;

function wire12(face){
  const tap=(el,fn)=>{el.addEventListener('click',fn);el.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();fn(e)}})};
  const alive=()=>face.isConnected;
  face.querySelectorAll('.p12a').forEach(el=>{const run=()=>{el.classList.remove('go','done');void el.offsetWidth;if(reduce){el.classList.add('done');return}el.classList.add('go');setTimeout(()=>{if(alive())el.classList.add('done')},3300)};
    setTimeout(()=>alive()&&run(),700);tap(el,run)});
  face.querySelectorAll('.p12b').forEach(el=>tap(el,()=>{if(reduce)return;el.classList.remove('spin');void el.offsetWidth;el.classList.add('spin')}));
}
L.wire=function(face,ctx){baseWire(face,ctx);wire12(face)};

const base=()=>`${W.name9('still')}${W.now()}${W.hike()}${W.ten()}${W.scan()}${W.puzzle()}`;
const SETS={
  coverA:()=>`${base()}${W.print12a()}${W.pal('raccoon')}${W.blank()}${W.ball()}`,
  coverB:()=>`${base()}${W.print12b()}${W.pal('raccoon')}${W.blank()}${W.ball()}`,
};
return {SETS};
})();
