/* ================= ROUND 7: live stickers, back to the cover ================= */
/* The wheel now has a cover detent before page 1: scroll or spin back past page 1 and the book closes.
   Two choices to mix: which sticker set (5, 8 or 13) and which cover. */
const R7=(()=>{
const {W,wire,shape,LAYOUTS}=R6.lib;
const SETS={
  five:()=>`${W.name()}${W.ai()}${W.scan()}${W.puzzle()}${W.ball()}`,
  eight:()=>`${W.name()}${W.ai()}${W.hoop()}${W.scan()}${W.hike()}${W.puzzle()}${W.print()}${W.ball()}`,
  packed:()=>LAYOUTS.lid().replace(W.slug(),''),
  // round 8: your favorites so far, plus who you are
  fav:()=>`${W.hike()}${W.name()}${W.ai()}${W.scan()}${W.puzzle()}${W.ball()}`,
  // round 9: what you kept from the sticker review
  kept:()=>R9.SETS.kept(),fav9:()=>R9.SETS.fav(),cover10:()=>R9.SETS.cover(),cover12a:()=>R12.SETS.coverA(),cover12b:()=>R12.SETS.coverB(),cover13a:()=>R13.SETS.coverA(),cover13b:()=>R13.SETS.coverB(),
};
const COVERS=[{id:'midnight',name:'Midnight'},{id:'forest',name:'Forest'},{id:'kraft',name:'Kraft'}];
/* the little typist who sits on the ScribbleScan pad and types out what it reads (it takes the banana slug's place) */
const KB=`<rect class="ty-kb" x="5" y="28" width="38" height="7" rx="1.6"/><path class="ty-ks" d="M8 30.6h32M8 32.8h32" />`;
const TYPISTS=[
 {id:'octopus',name:'Octopus',svg:`<g class="ty-hd"><path class="ty-tn" d="M14 21q-7 3-9 10M34 21q7 3 9 10" fill="none" stroke-width="3.4" stroke-linecap="round"/>
   <ellipse class="ty-c1" cx="24" cy="13.5" rx="11" ry="10"/><circle class="ty-c2" cx="17.5" cy="8.5" r="1.3"/><circle class="ty-c2" cx="30" cy="7" r="1"/><circle class="ty-c2" cx="31.5" cy="18" r="1.1"/>
   <g class="ty-eye"><circle cx="20" cy="14" r="2.7" fill="#fff"/><circle cx="20.4" cy="14.4" r="1.35" class="ty-pu"/><circle cx="28" cy="14" r="2.7" fill="#fff"/><circle cx="28.4" cy="14.4" r="1.35" class="ty-pu"/></g></g>
   ${KB}<path class="ty-a ty-c1s" d="M19 21q-.5 5-3 8.5" fill="none" stroke-width="3.6" stroke-linecap="round"/><path class="ty-b ty-c1s" d="M29 21q.5 5 3 8.5" fill="none" stroke-width="3.6" stroke-linecap="round"/>`},
 {id:'orca',name:'Orca',svg:`<g class="ty-hd"><path class="ty-c1" d="M26.5 9C27 4.5 29 1.5 32.5 0C31 3.5 31 6.5 32 10Z"/><ellipse class="ty-c1" cx="24" cy="19" rx="15.5" ry="12"/>
   <ellipse class="ty-c2" cx="24" cy="27" rx="10" ry="5.5"/><path d="M19.5 22.5q4.5 2.6 9 0" fill="none" stroke="#f4f4f2" stroke-width="1.1" stroke-linecap="round"/>
   <g class="ty-eye"><ellipse class="ty-c2" cx="16.6" cy="15.2" rx="3.6" ry="2.1" transform="rotate(-18 16.6 15.2)"/><ellipse class="ty-c2" cx="31.4" cy="15.2" rx="3.6" ry="2.1" transform="rotate(18 31.4 15.2)"/>
   <circle cx="17.6" cy="15.8" r="1.15" class="ty-pu"/><circle cx="30.4" cy="15.8" r="1.15" class="ty-pu"/></g></g>
   ${KB}<ellipse class="ty-a ty-c1" cx="14.5" cy="28.6" rx="3.4" ry="2.1" transform="rotate(25 14.5 28.6)"/><ellipse class="ty-b ty-c1" cx="33.5" cy="28.6" rx="3.4" ry="2.1" transform="rotate(-25 33.5 28.6)"/>`},
 {id:'robot',name:'Robot',svg:`<g class="ty-hd"><path d="M24 2.5v4" class="ty-c2s" stroke-width="1.4"/><circle class="ty-led" cx="24" cy="2.6" r="2"/>
   <rect class="ty-c1" x="13" y="6" width="22" height="15" rx="4"/><rect class="ty-sc" x="16" y="9" width="16" height="9" rx="2"/>
   <g class="ty-eye"><rect class="ty-ey" x="19" y="11.5" width="3" height="3.4" rx="1"/><rect class="ty-ey" x="26" y="11.5" width="3" height="3.4" rx="1"/></g>
   <rect class="ty-c2" x="17" y="20.5" width="14" height="8" rx="2"/></g>
   ${KB}<path class="ty-a ty-c1s" d="M18 23l-5 6.5" stroke-width="2.6" stroke-linecap="round"/><path class="ty-b ty-c1s" d="M30 23l5 6.5" stroke-width="2.6" stroke-linecap="round"/>`},
 {id:'raccoon',name:'Raccoon',svg:`<g class="ty-hd"><circle class="ty-c1" cx="15" cy="6.5" r="4"/><circle class="ty-c1" cx="33" cy="6.5" r="4"/><circle class="ty-c3" cx="15" cy="6.5" r="1.8"/><circle class="ty-c3" cx="33" cy="6.5" r="1.8"/>
   <ellipse class="ty-c1" cx="24" cy="15" rx="12" ry="10"/><ellipse class="ty-c2" cx="24" cy="19" rx="7.5" ry="5.5"/><path class="ty-c3" d="M12.6 13.5q5.4-4.5 11.4-.4q6-4.1 11.4.4q-2.6 4.2-6.8 3.2q-2.8-.8-4.6-.8t-4.6.8q-4.2 1-6.8-3.2Z"/>
   <g class="ty-eye"><circle cx="19" cy="13.3" r="1.5" fill="#fff"/><circle cx="29" cy="13.3" r="1.5" fill="#fff"/></g><circle class="ty-c3" cx="24" cy="19.2" r="1.6"/></g>
   ${KB}<ellipse class="ty-a ty-c1" cx="17" cy="29" rx="2.8" ry="2.2"/><ellipse class="ty-b ty-c1" cx="31" cy="29" rx="2.8" ry="2.2"/>`},
];
let typist='octopus';
try{const t=localStorage.getItem('pf-r7-typist');if(TYPISTS.some(x=>x.id===t))typist=t}catch(_){}
function setTypist(t){typist=t;try{localStorage.setItem('pf-r7-typist',t)}catch(_){}}
const typer=(id)=>{const t=TYPISTS.find(x=>x.id===(id||typist));return `<span class="ty ty-${t.id}" role="button" tabindex="0" aria-label="${t.name}. It types out what ScribbleScan reads. Tap to say hi."><svg viewBox="0 0 48 36" aria-hidden="true">${t.svg}</svg></span>`};
let cover='midnight';
try{const c=localStorage.getItem('pf-r7-cover');if(COVERS.some(x=>x.id===c))cover=c}catch(_){}
function setCover(c){cover=c;try{localStorage.setItem('pf-r7-cover',c)}catch(_){}}
/* three takes on the ScribbleScan sticker (round 8): same live pad, different object */
const PADS=[{id:'ruled',name:'Ruled card'},{id:'sticky',name:'Sticky note'},{id:'phone',name:'Phone scan'}];
let pad='ruled';
try{const t=localStorage.getItem('pf-r8-pad');if(PADS.some(x=>x.id===t))pad=t}catch(_){}
function setPad(t){pad=t;try{localStorage.setItem('pf-r8-pad',t)}catch(_){}}
// finishing touches every sticker gets in round 8: a sheen layer, and a lifted corner on the name tag
function dress(face){face.querySelectorAll('.wd').forEach(w=>{if(!w.querySelector(':scope > .wd-sh'))w.insertAdjacentHTML('beforeend','<i class="wd-sh" aria-hidden="true"></i>')});
  face.querySelectorAll('.wd-name').forEach(w=>w.insertAdjacentHTML('beforeend','<i class="wd-curl" aria-hidden="true"></i>'))}
function wireTypers(scope){scope.querySelectorAll('.ty').forEach(t=>{const hi=e=>{e.stopPropagation();t.classList.remove('hi');void t.offsetWidth;t.classList.add('hi')};
  t.addEventListener('click',hi);t.addEventListener('pointerdown',e=>e.stopPropagation());t.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();hi(e)}})})}

function mount(set,extra=''){return (root,mode)=>{
  const P=mode==='phone';let closed=true,cv=null,w=null,tm=0;
  const scale=()=>{const r=root.getBoundingClientRect();return r.width/root.offsetWidth||1};
  function build(fromOpen){
    const book=root.querySelector('.nb-book');
    cv=document.createElement('div');cv.className=`nb-leaf go cv cv-stickers cv6 cv7 cv7-${set}${set==='packed'?' cv6-lid':''} cv7c-${cover}${extra?' '+extra:''}`;
    cv.innerHTML=`<div class="face front cv-front"><i class="cv7-stitch"></i>${SETS[set]()}<span class="cv7-name">David Lybeck</span><i class="cv7-band"></i><button type="button" class="cv-open">open</button></div><div class="face back">${P?'':`<div class="nb-in">${root.querySelector('.nb-page.l .nb-in').innerHTML}</div>`}</div>`;
    if(!/\btr-r9\b/.test(extra))cv.querySelectorAll('.wd-scan .sc-out').forEach(o=>o.insertAdjacentHTML('beforeend',typer()));
    if(extra)dress(cv.querySelector('.cv-front'));
    book.appendChild(cv);wireTypers(cv);
    wire(cv.querySelector('.cv-front'),{open:t=>open(t),scale});
    let sx=null;
    cv.addEventListener('pointerdown',e=>{e.stopPropagation();sx=e.clientX});
    cv.addEventListener('pointerup',e=>{e.stopPropagation();if(sx!==null&&e.clientX-sx<-30){sx=null;open();return}sx=null});
    cv.addEventListener('click',e=>{e.stopPropagation();if(e.target.closest('.wd'))return;open()});
    if(fromOpen&&!reduce){if(P){const an=tuck(cv,-180,0,900,'cubic-bezier(0.45,0.05,0.25,1)');an.onfinish=()=>an.cancel()}else{cv.style.transform='rotateY(-180deg)';void cv.offsetWidth;cv.style.transition='transform 900ms cubic-bezier(0.45,0.05,0.25,1)';cv.style.transform='';}}
  }
  // open: from a tap (the wheel glides to the page) or from the wheel itself (it is already there)
  function open(target,fromWheel){
    if(!closed)return;closed=false;clearTimeout(tm);
    if(target&&target!=='me')w.nb.go(target,{instant:true,silent:true});
    root.classList.remove('closed');
    if(!fromWheel)w.ctl.sync(w.nb.cur);
    const c=cv;cv=null;if(reduce){c.remove();return}
    if(P)tuck(c,0,-180,950,'cubic-bezier(0.45,0.05,0.25,1)');else{c.style.transition='transform 950ms cubic-bezier(0.45,0.05,0.25,1)';c.style.transform='rotateY(-180deg)';}
    tm=setTimeout(()=>c.remove(),980);
  }
  // close: the cover swings back over page 1
  function close(fromWheel){
    if(closed)return;closed=true;clearTimeout(tm);
    if(w.nb.cur!=='me')w.nb.go('me',{instant:true,silent:true});
    root.querySelectorAll('.nb-book > .cv').forEach(x=>x.remove());
    root.classList.add('closed');build(true);
    if(!fromWheel)w.ctl.sync('cover');
  }
  root.classList.add('cvr','cvr-stickers','r6','r7','r7c-'+cover,'closed');if(extra)root.classList.add('r8','sv-'+pad,...extra.split(' '));
  // the logo takes you back to the cover; Say hi opens the book there
  root.addEventListener('click',e=>{
    if(e.target.closest('[data-home]')){e.stopPropagation();e.preventDefault();if(!closed)close();return}
    if(closed&&e.target.closest('[data-say]')){e.stopPropagation();e.preventDefault();open('say')}
  },true);
  w=R4.wheel(root,mode,{cover:true,isClosed:()=>closed,open:()=>open(null,true),close:()=>close(true)});
  shape(root,P);new ResizeObserver(()=>shape(root,P)).observe(root);
  build(false);w.refresh();
  return {reset(){w.reset();root.querySelectorAll('.nb-book > .cv').forEach(x=>x.remove());closed=true;root.classList.add('closed');build(false);w.refresh()}};
};}
return {COVERS,TYPISTS,PADS,get cover(){return cover},get typist(){return typist},get pad(){return pad},setCover,setTypist,setPad,typer,dress,wireTypers,make:mount,SETS,five:mount('five'),eight:mount('eight'),packed:mount('packed')};
})();
