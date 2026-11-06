/* ================= ROUND 9: built from your sticker review notes ================= */
/* Loads after round 6 and before round 7, so the stickers it changes are the ones every later round uses. */
const R9=(()=>{
const L=R6.lib,W=L.W,baseWire=L.wire;
const hike0=W.hike;

/* the trail, without the words on it */
W.hike=()=>hike0().replace(/\s*<text[^>]*>THE TRAIL<\/text>/,'');
/* TENNIS, without "since middle school": just the word, with a ball's path under it */
W.ten=()=>`<div class="wd wd-ten wd-ten9" role="button" tabindex="0" aria-label="Tennis sticker"><b>TENNIS</b><svg class="t9-arc" viewBox="0 0 100 14" aria-hidden="true"><path d="M4 11 Q50 -3 88 8" fill="none"/><circle cx="92" cy="9" r="4.2"/></svg></div>`;
/* name tag, two takes: it writes your name in marker, or it just sits there */
W.name9=(v='write')=>`<div class="wd wd-name n9 n9-${v}" role="button" tabindex="0" aria-label="Name tag: David"><b>HELLO</b><small>my name is</small><span class="nm"><span class="nm-w"><span class="nm-i">David</span>${v==='write'?'<i class="nm-pen" aria-hidden="true"></i>':''}</span></span></div>`;
/* the typists, now stickers of their own */
const PALS={octopus:'A giant Pacific octopus at a keyboard. Tap to say hi.',raccoon:'A raccoon at a keyboard. Tap to say hi.'};
W.pal=(id)=>{const t=R7.TYPISTS.find(x=>x.id===id);return `<div class="wd wd-pal wd-pal-${id}" role="button" tabindex="0" aria-label="${PALS[id]||t.name}"><span class="pty ty-${id}"><svg viewBox="0 0 48 36" aria-hidden="true">${t.svg}</svg></span><span class="pal-say" aria-hidden="true"></span></div>`};
/* your sticker: draw one or add a picture; it stays in this browser */
W.blank=()=>`<div class="wd wd-blank wd-round wd-mine" role="button" tabindex="0" aria-label="Your sticker. Tap to draw one or add a picture."><span class="mn-t">your<br>sticker<br>here</span><i class="mn-img" aria-hidden="true"></i></div>`;

const store={get(k){try{return localStorage.getItem(k)}catch(_){return null}},set(k,v){try{v==null?localStorage.removeItem(k):localStorage.setItem(k,v)}catch(_){}}};
let mine=store.get('pf-r9-mine');
function paintMine(scope){(scope||document).querySelectorAll('.wd-mine').forEach(el=>{el.classList.toggle('has',!!mine);el.querySelector('.mn-img').style.backgroundImage=mine?`url("${mine}")`:'';
  el.setAttribute('aria-label',mine?'Your sticker. Tap to change it.':'Your sticker. Tap to draw one or add a picture.')})}

/* the sticker maker */
let dlg=null,cv,g,ink='#1b2436',size=6,last=null,dirty=false;
const N=400;
function blankCanvas(){g.setTransform(1,0,0,1,0,0);g.fillStyle='#fff';g.fillRect(0,0,N,N);dirty=false}
function makeDialog(){
  dlg=document.createElement('dialog');dlg.className='mk9';dlg.setAttribute('aria-labelledby','mk9-h');
  dlg.innerHTML=`<form method="dialog" class="mk9-in">
    <h2 id="mk9-h">Make your sticker</h2>
    <p class="mk9-p">Draw on the circle, or add a picture and draw on top. It stays in this browser only.</p>
    <div class="mk9-st"><canvas width="${N}" height="${N}" aria-label="Drawing area"></canvas></div>
    <div class="mk9-tools">
      <div class="mk9-sw" role="group" aria-label="Pen color">${['#1b2436','#0062cc','#c8372d','#2e8b57','#f2b705'].map((c,i)=>`<button type="button" data-c="${c}" aria-label="Pen color ${i+1}" aria-pressed="${i===0}" style="--c:${c}"></button>`).join('')}</div>
      <label class="mk9-btn">Add a picture<input type="file" accept="image/*" hidden></label>
      <button type="button" class="mk9-btn" data-a="clear">Clear</button>
    </div>
    <div class="mk9-foot">
      <button type="button" class="mk9-btn quiet" data-a="off">Take it off</button>
      <span class="mk9-sp"></span>
      <button type="button" class="mk9-btn" data-a="cancel">Cancel</button>
      <button type="button" class="mk9-btn primary" data-a="done">Stick it on</button>
    </div></form>`;
  document.body.appendChild(dlg);
  cv=dlg.querySelector('canvas');g=cv.getContext('2d');
  const at=e=>{const r=cv.getBoundingClientRect();return [(e.clientX-r.left)*N/r.width,(e.clientY-r.top)*N/r.height]};
  cv.addEventListener('pointerdown',e=>{if(e.button)return;e.preventDefault();last=at(e);try{cv.setPointerCapture(e.pointerId)}catch(_){}g.fillStyle=ink;g.beginPath();g.arc(last[0],last[1],size/2,0,7);g.fill();dirty=true});
  cv.addEventListener('pointermove',e=>{if(!last)return;const p=at(e);g.strokeStyle=ink;g.lineWidth=size;g.lineCap=g.lineJoin='round';g.beginPath();g.moveTo(...last);g.lineTo(...p);g.stroke();last=p});
  const up=()=>{last=null};cv.addEventListener('pointerup',up);cv.addEventListener('pointercancel',up);
  dlg.querySelectorAll('.mk9-sw button').forEach(b=>b.onclick=()=>{ink=b.dataset.c;dlg.querySelectorAll('.mk9-sw button').forEach(x=>x.setAttribute('aria-pressed',x===b))});
  dlg.querySelector('input[type=file]').addEventListener('change',e=>{const f=e.target.files&&e.target.files[0];e.target.value='';if(!f||!/^image\//.test(f.type))return;
    const url=URL.createObjectURL(f),im=new Image();im.onload=()=>{blankCanvas();const s=Math.max(N/im.width,N/im.height),w=im.width*s,h=im.height*s;g.drawImage(im,(N-w)/2,(N-h)/2,w,h);URL.revokeObjectURL(url);dirty=true};
    im.onerror=()=>URL.revokeObjectURL(url);im.src=url});
  dlg.addEventListener('click',e=>{const a=e.target.closest('[data-a]');if(!a)return;const k=a.dataset.a;
    if(k==='clear')blankCanvas();
    else if(k==='cancel')dlg.close();
    else if(k==='off'){mine=null;store.set('pf-r9-mine',null);paintMine();dlg.close()}
    else if(k==='done'){if(dirty){mine=cv.toDataURL('image/jpeg',.86);store.set('pf-r9-mine',mine);paintMine()}dlg.close()}});
}
function openMaker(){
  if(!dlg)makeDialog();
  blankCanvas();
  dlg.querySelector('[data-a="off"]').hidden=!mine;
  if(mine){const im=new Image();im.onload=()=>{g.drawImage(im,0,0,N,N);dirty=false};im.src=mine}
  if(dlg.showModal)dlg.showModal();else dlg.setAttribute('open','');
}

function wire9(face,ctx){
  const tap=(el,fn)=>{el.addEventListener('click',fn);el.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();fn(e)}})};
  const alive=()=>face.isConnected;
  // name tag: writes "David" in marker once it shows, and again when tapped
  face.querySelectorAll('.n9-write').forEach(el=>{const run=()=>{el.classList.remove('go');void el.offsetWidth;el.classList.add('go')};
    if(!reduce)setTimeout(()=>alive()&&run(),600);tap(el,()=>{if(!reduce)run()})});
  face.querySelectorAll('.n9-still').forEach(el=>tap(el,()=>{el.classList.remove('press');void el.offsetWidth;el.classList.add('press')}));
  face.querySelectorAll('.wd-ten9').forEach(el=>tap(el,()=>{el.classList.remove('hit');void el.offsetWidth;el.classList.add('hit')}));
  // the typists: tap and they type a quick hello
  face.querySelectorAll('.wd-pal').forEach(el=>{const say=el.querySelector('.pal-say');let tm=0,k=0;const words=['hi!','hello','hey there'];
    tap(el,()=>{clearTimeout(tm);el.classList.add('typing');say.textContent='';const w=words[k++%words.length];let i=0;
      const step=()=>{if(!alive())return;say.textContent=w.slice(0,++i);if(i<w.length)tm=setTimeout(step,reduce?0:110);else tm=setTimeout(()=>{el.classList.remove('typing');tm=setTimeout(()=>{say.textContent=''},1300)},300)};
      el.classList.add('saying');step()})});
  // your sticker
  face.querySelectorAll('.wd-mine').forEach(el=>tap(el,()=>openMaker()));
  paintMine(face);
}
L.wire=function(face,ctx){baseWire(face,ctx);wire9(face,ctx)};

/* the round 9 cover sets */
const SETS={
  kept:()=>`${W.name9('write')}${W.now()}${W.hike()}${W.ten()}${W.scan()}${W.pal('octopus')}${W.puzzle()}${W.print()}${W.pal('raccoon')}${W.blank()}${W.ball()}`,
  fav:()=>`${W.name9('write')}${W.hike()}${W.scan()}${W.pal('octopus')}${W.puzzle()}${W.blank()}${W.ball()}`,
  // round 10: everything you kept in round 9, with the still name tag you picked
  cover:()=>`${W.name9('still')}${W.now()}${W.hike()}${W.ten()}${W.scan()}${W.pal('octopus')}${W.puzzle()}${W.print()}${W.pal('raccoon')}${W.blank()}${W.ball()}`,
};
return {SETS,openMaker,paintMine};
})();
