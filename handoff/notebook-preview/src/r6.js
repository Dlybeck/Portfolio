/* ================= ROUND 6: a live sticker cover ================= */
/* The notebook keeps a real notebook shape (5 by 8, like a hardcover notebook) on every screen.
   The stickers on the cover are live: each one does something, and each one is something from the pages. */
const R6=(()=>{
const RATIO=5/8;
const LOGO_IMG=()=>`<img alt="" src="${LOGO}">`;
const NOW=[['now','AI tools at Denali',1],['2025','ScribbleScan LLC'],['2024','2nd Chair intern'],['2022','tennis coach']];
const NAMES=['David','a builder','a tennis coach','a puzzle maker'];
const WORDS=['hello','notes','ideas','hi there'];

/* ---------- the widgets ---------- */
const W={
  name:()=>`<div class="wd wd-name" role="button" tabindex="0" aria-label="Name tag. Tap to change it."><b>HELLO</b><small>my name is</small><span class="nm">David</span></div>`,
  logo:()=>`<div class="wd wd-logo" role="button" tabindex="0" aria-label="Logo sticker">${LOGO_IMG()}</div>`,
  scan:(big)=>`<div class="wd wd-scan${big?' big':''}"><div class="sc-pad"><svg viewBox="0 0 220 64" aria-hidden="true"><text x="12" y="46" class="sc-w"></text></svg><canvas aria-label="Write here"></canvas><i class="sc-bar"></i>${big?'<span class="sc-try">write anything</span>':''}</div>
    <div class="sc-out"><span class="sc-k">ScribbleScan</span><code class="sc-t" aria-live="polite"></code></div></div>`,
  ball:()=>`<div class="wd wd-ball" role="button" tabindex="0" aria-label="Tennis ball. Tap to bounce it, or throw it."></div>`,
  court:()=>`<div class="wd wd-court"><span class="ct-k">tennis</span><span class="ct-n">0 taps</span><div class="wd-ball in" role="button" tabindex="0" aria-label="Tennis ball. Tap to bounce it."></div></div>`,
  puzzle:()=>`<div class="wd wd-puzzle"><div class="pz" role="group" aria-label="Sliding puzzle">${[0,1,2,3,4,5,6,7].map(i=>`<button type="button" class="pz-t" data-i="${i}" aria-label="Tile ${i+1}"></button>`).join('')}</div><span class="pz-k">puzzle box</span></div>`,
  now:()=>`<div class="wd wd-now" role="button" tabindex="0" aria-label="What I'm doing. Tap for earlier."><i class="dot"></i><b></b><span></span></div>`,
  nba:()=>`<div class="wd wd-nba" role="button" tabindex="0" aria-label="NBA Prediction AI. Tap to run it again."><span class="nb-k">NBA prediction AI</span><span class="nb-n">2</span><span class="nb-s">misses in the<br>2024 playoffs</span></div>`,
  mtn:()=>`<div class="wd wd-mtn" role="button" tabindex="0" aria-label="Mountain badge. Tap to go for a hike."><svg viewBox="0 0 100 100" aria-hidden="true">
    <rect class="m-sky" width="100" height="100"/><circle class="m-sun" cx="62" cy="34" r="14"/>
    <path class="m-far" d="M-5 74 L22 46 L38 60 L56 32 L78 56 L105 40 L105 100 L-5 100Z"/><path class="m-snow" d="M50 39.5 L56 32 L62 39 L58.5 37.5 L56 40.5 L53 38Z"/>
    <path class="m-trail" d="M30 96 C44 88 26 80 40 72 S48 58 56 40" fill="none"/><g class="m-hiker"><circle r="2.2" cy="-5.5"/><rect x="-1.6" y="-3.6" width="3.2" height="5" rx="1"/><rect x="-3.4" y="-3.2" width="2" height="3.6" rx=".6" class="pack"/></g><path class="m-tree" d="M10 86 L18 58 L26 86Z M78 88 L86 54 L94 88Z M68 90 L74 70 L80 90Z"/><rect class="m-lake" y="84" width="100" height="16"/></svg></div>`,
  stamp:()=>`<div class="wd wd-stamp" role="button" tabindex="0" aria-label="Stamp. Tap to postmark it."><div class="sp-in"><span class="sp-t">CS · 2025</span>
    <svg viewBox="0 0 60 44" aria-hidden="true"><rect width="60" height="44" class="s-sky"/><circle cx="16" cy="11" r="6" class="s-sun"/><path d="M0 26 L14 16 L22 21 L36 6 L48 17 L60 12 L60 30 L0 30Z" class="s-mtn"/><path d="M33 9.5 L36 6 L39 9.6 L37 9 L36 10.4 L34.6 9Z" class="s-snow"/><path d="M0 28 Q10 24 20 27 T44 25 T60 26 V32 H0Z" class="s-for"/><rect y="31" width="60" height="13" class="s-mead"/><path d="M24 44 C30 40 20 37 28 34 S34 32 36 31" class="s-path"/></svg>
    <span class="sp-b">TACOMA, WA</span></div><i class="pm" aria-hidden="true"><b>CLASS OF</b>2025</i></div>`,
  ten:()=>`<div class="wd wd-ten" role="button" tabindex="0" aria-label="Tennis sticker"><b>TENNIS</b><small>since middle school</small></div>`,
  mfa:()=>`<div class="wd wd-mfa" role="button" tabindex="0" aria-label="Two-factor code. Tap for a new one."><span class="mf-k">2FA</span><code class="mf-c">482 913</code><i class="mf-r"></i><small>never share this code</small></div>`,
  print:()=>`<div class="wd wd-print" role="button" tabindex="0" aria-label="3D printer. Tap to print again."><div class="pr-fr"><i class="pr-g"><i class="pr-n"></i></i><div class="pr-o" style="background-image:url('${LOGO}')"></div><i class="pr-b"></i></div><span class="pr-k">printing</span></div>`,
  fire:()=>`<div class="wd wd-fire" role="button" tabindex="0" aria-label="Campfire. Tap to stoke it."><div class="fi-f"><i></i><i></i><i></i></div><div class="fi-s"><i></i><i></i><i></i><i></i></div><div class="fi-l"></div></div>`,
  hike:()=>`<div class="wd wd-mtn wd-hike" role="button" tabindex="0" aria-label="Stamp of a mountain trail. Tap to go for a hike."><svg viewBox="0 0 120 72" aria-hidden="true">
    <rect class="m-sky" width="120" height="72"/><rect class="m-band" y="12" width="120" height="4"/><circle class="m-sun" cx="28" cy="24" r="9"/>
    <path class="m-far" d="M0 48 L20 32 L32 40 L56 12 L74 34 L88 26 L120 44 V72 H0Z"/><path class="m-snow" d="M50 19 L56 12 L62 18.5 L59 17.5 L56 20.5 L53 18Z"/>
    <rect class="m-mead" y="54" width="120" height="18"/><path class="m-trail" d="M66 72 C82 64 52 60 68 52 S74 36 57 15" fill="none"/>
    <g class="m-hiker"><circle r="2" cy="-5"/><rect x="-1.5" y="-3.4" width="3" height="4.6" rx="1"/><rect x="-3.2" y="-3" width="1.9" height="3.4" rx=".6" class="pack"/></g>
    <path class="m-tree" d="M4 66 L11 40 L18 66Z M16 68 L22 50 L28 68Z M96 68 L104 42 L112 68Z"/>
    <text x="60" y="69" class="c-t">THE TRAIL</text></svg></div>`,
  card:()=>`<div class="wd wd-card" role="button" tabindex="0" aria-label="Postcard of the Tacoma waterfront. Tap for night."><svg viewBox="0 0 120 72" aria-hidden="true">
    <rect class="c-sky" width="120" height="72"/><rect class="c-band" y="10" width="120" height="5"/><rect class="c-band b2" y="19" width="120" height="4"/>
    <circle class="c-sun" cx="92" cy="30" r="9"/><g class="c-stars"><circle cx="14" cy="10" r=".9"/><circle cx="40" cy="6" r=".7"/><circle cx="62" cy="14" r=".9"/><circle cx="104" cy="8" r=".7"/><circle cx="80" cy="18" r=".6"/></g>
    <path class="c-hill" d="M0 40 Q20 30 42 38 T86 34 T120 36 V48 H0Z"/>
    <path class="c-bridge" d="M58 40 V24 M74 40 V24 M44 40 Q66 26 88 40" fill="none"/><rect class="c-water" y="44" width="120" height="28"/>
    <path class="c-shine" d="M84 50 H100 M88 55 H98 M90 60 H96"/>
    <g class="c-piers"><rect x="10" y="40" width="2.4" height="22"/><rect x="18" y="42" width="2.4" height="20"/><rect x="26" y="40" width="2.4" height="24"/><rect x="34" y="43" width="2.4" height="18"/><rect x="42" y="41" width="2.4" height="22"/></g>
    <g class="c-lights"><circle cx="58" cy="25" r="1"/><circle cx="74" cy="25" r="1"/><circle cx="6" cy="38" r=".8"/><circle cx="110" cy="35" r=".8"/></g>
    <text x="60" y="69" class="c-t">TACOMA</text></svg></div>`,
  slug:()=>`<div class="wd wd-slug" role="button" tabindex="0" aria-label="Banana slug. Tap to say hi."><div class="sl-body"><i class="sl-e"></i><i class="sl-e b"></i><i class="sl-sp"></i></div><span class="sl-say">hi!</span></div>`,
  ai:()=>`<div class="wd wd-ai wd-round" role="button" tabindex="0" aria-label="AI sticker. Tap it."><svg viewBox="0 0 40 40" aria-hidden="true"><path class="ai-st" d="M20 5 C21.5 15 25 18.5 35 20 C25 21.5 21.5 25 20 35 C18.5 25 15 21.5 5 20 C15 18.5 18.5 15 20 5Z"/><path class="ai-st s2" d="M31 6 C31.5 9 32.5 10 35.5 10.5 C32.5 11 31.5 12 31 15 C30.5 12 29.5 11 26.5 10.5 C29.5 10 30.5 9 31 6Z"/></svg><b>AI</b><span class="pop" aria-live="polite"></span></div>`,
  hoop:()=>`<div class="wd wd-hoop wd-round" role="button" tabindex="0" aria-label="NBA Prediction AI sticker. Tap it."><svg viewBox="0 0 40 40" aria-hidden="true"><g class="hp-b"><circle cx="20" cy="20" r="13"/><path d="M7 20 H33 M20 7 V33 M11 10 C17 16 17 24 11 30 M29 10 C23 16 23 24 29 30"/></g></svg><span class="pop" aria-live="polite"></span></div>`,
  blank:()=>`<div class="wd wd-blank wd-round" role="button" tabindex="0" aria-label="Empty spot for a sticker to come"><span>your<br>sticker<br>here</span></div>`,
  plan:()=>`<div class="wd wd-plan"><span class="pl-k">today</span>
    <button type="button" class="pl-i done" disabled><i></i>make this notebook</button>
    <button type="button" class="pl-i" data-go="me"><i></i>open it</button>
    <button type="button" class="pl-i" data-go="say"><i></i>say hi</button></div>`,
};

/* behaviours. ctx: {face, open(target), scale()} */
function wire(face,ctx){
  const stopAll=el=>['pointerdown','pointerup','click','keydown'].forEach(t=>el.addEventListener(t,e=>{if(t!=='keydown'||e.key==='Enter'||e.key===' ')e.stopPropagation()}));
  const tap=(el,fn)=>{el.addEventListener('click',fn);el.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();fn(e)}})};
  face.querySelectorAll('.wd').forEach(stopAll);
  const alive=()=>face.isConnected;

  // name tag: tap to rewrite the line
  face.querySelectorAll('.wd-name:not(.n9)').forEach(el=>{let i=0;const nm=el.querySelector('.nm');
    tap(el,()=>{i=(i+1)%NAMES.length;nm.textContent=NAMES[i];nm.classList.remove('wr');void nm.offsetWidth;nm.classList.add('wr')})});
  // logo: a little peel and wiggle
  face.querySelectorAll('.wd-logo').forEach(el=>tap(el,()=>{el.classList.remove('peel');void el.offsetWidth;el.classList.add('peel')}));

  // now / then
  face.querySelectorAll('.wd-now').forEach(el=>{let i=0;const show=()=>{const [k,t,live]=NOW[i];el.querySelector('b').textContent=k;el.querySelector('span').textContent=t;el.classList.toggle('live',!!live)};show();
    tap(el,()=>{i=(i+1)%NOW.length;show();el.classList.remove('flip');void el.offsetWidth;el.classList.add('flip')})});

  // NBA: the digits roll and land on the real number
  face.querySelectorAll('.wd-nba').forEach(el=>{const n=el.querySelector('.nb-n');let tm=0;
    tap(el,()=>{clearInterval(tm);if(reduce){n.textContent='2';return}let k=0;tm=setInterval(()=>{n.textContent=k<12?String(Math.floor(Math.random()*10)):'2';if(++k>12)clearInterval(tm)},55)})});


  // round badges that say one line from the pages when tapped
  const say=(el,lines)=>{const pop=el.querySelector('.pop');let i=0,tm=0;tap(el,()=>{clearTimeout(tm);el.classList.add('think');pop.textContent='…';
    tm=setTimeout(()=>{if(!alive())return;el.classList.remove('think');pop.textContent=lines[i%lines.length];i++;el.classList.add('said');tm=setTimeout(()=>el.classList.remove('said'),2600)},reduce?0:650)})};
  face.querySelectorAll('.wd-ai').forEach(el=>say(el,['I build AI tools at Denali','and help people use AI in their own roles']));
  face.querySelectorAll('.wd-hoop').forEach(el=>say(el,['called the 2024 playoffs','with only 2 mistakes']));
  face.querySelectorAll('.wd-blank:not(.wd-mine)').forEach(el=>tap(el,()=>{el.classList.remove('peel');void el.offsetWidth;el.classList.add('peel')}));
  // postcard: night falls on the waterfront
  face.querySelectorAll('.wd-card').forEach(el=>tap(el,()=>el.classList.toggle('night')));
  // banana slug: crawls along, says hi when tapped
  face.querySelectorAll('.wd-slug').forEach(el=>tap(el,()=>{el.classList.remove('hi');void el.offsetWidth;el.classList.add('hi')}));
  // mountain: a hike to the top, then sunset. Tap again for morning
  face.querySelectorAll('.wd-mtn').forEach(el=>{const tr=el.querySelector('.m-trail'),hk=el.querySelector('.m-hiker');if(!tr||!hk)return;
    const L=tr.getTotalLength(),put=f=>{const a=tr.getPointAtLength(L*f);hk.setAttribute('transform',`translate(${a.x} ${a.y})`)};put(0);let busy=false;
    tap(el,()=>{if(busy)return;if(el.classList.contains('dusk')){el.classList.remove('dusk');put(0);return}
      if(reduce){put(1);el.classList.add('dusk');return}busy=true;const t0=performance.now(),D=2200;
      const step=t=>{if(!alive())return;const f=Math.min(1,(t-t0)/D),e=f<.5?2*f*f:1-Math.pow(-2*f+2,2)/2;put(e);if(f<1)requestAnimationFrame(step);else{el.classList.add('dusk');busy=false}};requestAnimationFrame(step)})});
  // stamp: postmark it
  face.querySelectorAll('.wd-stamp').forEach(el=>tap(el,()=>{el.classList.remove('mk');void el.offsetWidth;el.classList.add('mk')}));
  // tennis sticker: kicks the ball if there is one
  face.querySelectorAll('.wd-ten').forEach(el=>tap(el,()=>{el.classList.remove('peel');void el.offsetWidth;el.classList.add('peel')}));
  // 2FA: a code that turns over every 30 seconds, or when tapped
  face.querySelectorAll('.wd-mfa').forEach(el=>{const c=el.querySelector('.mf-c'),r=el.querySelector('.mf-r');let t0=Date.now();
    const code=()=>{const n=String(Math.floor(Math.random()*1e6)).padStart(6,'0');c.textContent=n.slice(0,3)+' '+n.slice(3);t0=Date.now();el.classList.remove('new');void el.offsetWidth;el.classList.add('new')};
    const tick=()=>{if(!alive()){clearInterval(iv);return}const left=1-((Date.now()-t0)/30000);if(left<=0)code();r.style.setProperty('--p',Math.max(0,left)*100)};
    const iv=setInterval(tick,reduce?1000:250);tick();tap(el,code)});
  // 3D printer: prints the logo layer by layer
  face.querySelectorAll('.wd-print').forEach(el=>{const k=el.querySelector('.pr-k');
    const run=()=>{el.classList.remove('go','done');void el.offsetWidth;k.textContent='printing';if(reduce){el.classList.add('done');k.textContent='printed';return}el.classList.add('go');setTimeout(()=>{if(alive()){el.classList.add('done');k.textContent='printed'}},3300)};
    setTimeout(()=>alive()&&run(),700);tap(el,run)});
  // campfire: stoke it
  face.querySelectorAll('.wd-fire').forEach(el=>tap(el,()=>{el.classList.remove('stoke');void el.offsetWidth;el.classList.add('stoke')}));
  // planner: ticking a line does it
  face.querySelectorAll('.pl-i[data-go]').forEach(b=>b.addEventListener('click',()=>{b.classList.add('done');setTimeout(()=>ctx.open(b.dataset.go),reduce?0:420)}));

  // sliding puzzle with the logo on it
  face.querySelectorAll('.wd-puzzle').forEach(el=>{
    const tiles=[...el.querySelectorAll('.pz-t')];let cells=[0,1,2,3,4,5,6,7,8];// cells[pos]=tile, 8 = gap
    el.querySelector('.pz').style.setProperty('--logo-img',`url("${LOGO}")`);tiles.forEach(t=>{const i=+t.dataset.i;t.style.backgroundImage=`url("${LOGO}")`;t.style.backgroundPosition=`${(i%3)*50}% ${Math.floor(i/3)*50}%`});
    const adj=(a,b)=>Math.abs(a%3-b%3)+Math.abs(Math.floor(a/3)-Math.floor(b/3))===1;
    let seed=7;const rnd=()=>(seed=(seed*16807)%2147483647)/2147483647;
    let prev=-1;for(let k=0;k<7;k++){const g=cells.indexOf(8),opts=[0,1,2,3,4,5,6,7,8].filter(p=>adj(p,g)&&p!==prev),p=opts[Math.floor(rnd()*opts.length)];[cells[g],cells[p]]=[cells[p],cells[g]];prev=g}
    const place=()=>{cells.forEach((t,p)=>{if(t<8)tiles[t].style.translate=`${(p%3)*100}% ${Math.floor(p/3)*100}%`});
      const solved=cells.every((t,p)=>t===p);el.classList.toggle('solved',solved);el.querySelector('.pz-k').textContent=solved?'solved!':'puzzle box'};
    tiles.forEach(t=>t.addEventListener('click',()=>{const p=cells.indexOf(+t.dataset.i),g=cells.indexOf(8);if(!adj(p,g))return;[cells[g],cells[p]]=[cells[p],cells[g]];place()}));
    place();
  });

  // tennis ball: tap to bounce, drag to throw. Loose balls roam the whole cover; a court ball stays in its tile.
  face.querySelectorAll('.wd-ball').forEach(ball=>{
    const box=ball.classList.contains('in')?ball.parentElement:face,cnt=box.querySelector('.ct-n');let taps=0;
    let x=0,y=0,vx=0,vy=0,raf=0,last=0,drag=null,rot=0,w=0;const G=1500,E=.72,R=()=>size()/2;
    const size=()=>ball.offsetWidth,bw=()=>box.clientWidth,bh=()=>box.clientHeight-(box===face?0:0);
    const home=()=>{const r=ball.getBoundingClientRect(),b=box.getBoundingClientRect(),s=ctx.scale();x=(r.left-b.left)/s;y=(r.top-b.top)/s;ball.style.left='0';ball.style.top='0';ball.style.right='auto';ball.style.bottom='auto';ball.classList.add('free');put()};
    const put=()=>{ball.style.translate=`${x}px ${y}px`;ball.style.rotate=`${rot}deg`;const sh=ball.querySelector(':scope > .wd-sh');if(sh)sh.style.rotate=`${-rot}deg`};
    let homed=false;const ensure=()=>{if(!homed){home();homed=true}};
    function step(t){const dt=Math.min(.033,(t-last)/1000||.016);last=t;if(!alive()){raf=0;return}
      if(!drag){vy+=G*dt;x+=vx*dt;y+=vy*dt;const mx=bw()-size(),my=bh()-size();
        rot+=w*dt;w*=Math.pow(.75,dt);
        if(x<0){x=0;vx=-vx*E;w=-w*.5+vy*.2}if(x>mx){x=mx;vx=-vx*E;w=-w*.5-vy*.2}if(y<0){y=0;vy=-vy*E}
        if(y>my){y=my;vy=-vy*E;const r=R(),om=w*Math.PI/180,v=(5*vx+2*om*r)/7;vx=v*.92;w=vx/r*180/Math.PI;if(Math.abs(vy)<60)vy=0}}
      put();
      if(drag||Math.abs(vx)>4||Math.abs(vy)>0||Math.abs(w)>8||y<bh()-size()-.5)raf=requestAnimationFrame(step);else{raf=0;vx=0;w=0}}
    const go=()=>{if(!raf){last=performance.now();raf=requestAnimationFrame(step)}};
    const kick=()=>{ensure();if(reduce){ball.classList.remove('hop');void ball.offsetWidth;ball.classList.add('hop');return}vy=-(box===face?720:520);vx=(Math.random()-.5)*(box===face?420:220);w=(Math.random()<.5?-1:1)*(800+Math.random()*900);go();taps++;if(cnt)cnt.textContent=taps===1?'1 tap':taps+' taps'};
    ball.addEventListener('pointerdown',e=>{if(e.button)return;e.stopPropagation();ensure();drag={sx:e.clientX,sy:e.clientY,ox:x,oy:y,moved:false,s:[[performance.now(),x,y]]};try{ball.setPointerCapture(e.pointerId)}catch(_){}vx=vy=0;ball.classList.add('held')});
    ball.addEventListener('pointermove',e=>{if(!drag)return;const s=ctx.scale(),dx=(e.clientX-drag.sx)/s,dy=(e.clientY-drag.sy)/s;if(!drag.moved&&Math.hypot(dx,dy)>4)drag.moved=true;if(!drag.moved)return;
      x=Math.max(0,Math.min(bw()-size(),drag.ox+dx));y=Math.max(0,Math.min(bh()-size(),drag.oy+dy));put();const now=performance.now();drag.s.push([now,x,y]);while(drag.s.length>2&&now-drag.s[0][0]>80)drag.s.shift()});
    const up=e=>{if(!drag)return;e&&e.stopPropagation();const d=drag;drag=null;ball.classList.remove('held');
      if(d.moved){if(reduce){vx=vy=0;return}const [t0,x0,y0]=d.s[0],dt=Math.max(.016,(performance.now()-t0)/1000);vx=Math.max(-1600,Math.min(1600,(x-x0)/dt));vy=Math.max(-1600,Math.min(1600,(y-y0)/dt));w=vx*2.4+(Math.random()-.5)*300;go()}
      else kick()};
    ball.addEventListener('pointerup',up);ball.addEventListener('pointercancel',up);
    ball.addEventListener('click',e=>e.stopPropagation());
    ball.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();kick()}});
  });

  // ScribbleScan: it writes a word, scans it and types it out. Write your own and it scans that too.
  face.querySelectorAll('.wd-scan').forEach(el=>{
    const txt=el.querySelector('.sc-w'),bar=el.querySelector('.sc-bar'),out=el.querySelector('.sc-t'),cv=el.querySelector('canvas'),pad=el.querySelector('.sc-pad'),hint=el.querySelector('.sc-try');
    let wi=0,timers=[],busyDraw=false;const later=(f,ms)=>timers.push(setTimeout(()=>{if(alive())f()},ms));const clear=()=>{timers.forEach(clearTimeout);timers=[]};
    function type(s,then){out.textContent='';if(reduce){out.textContent=s;then&&then();return}let k=0;el.classList.add('typing');const tick=()=>{out.textContent=s.slice(0,++k);if(k<s.length)later(tick,55);else{later(()=>el.classList.remove('typing'),200);if(then)then()}};tick()}
    function sweep(then){if(reduce){then();return}bar.classList.remove('go');void bar.offsetWidth;bar.classList.add('go');later(then,620)}
    function demo(){clear();if(busyDraw)return;const w=WORDS[wi%WORDS.length];wi++;
      txt.textContent=w;txt.classList.remove('wr');void txt.getBBox;void el.offsetWidth;txt.classList.add('wr');out.textContent='';
      later(()=>sweep(()=>type(w,()=>later(demo,2600))),reduce?0:1500)}
    // drawing
    const g=cv.getContext('2d');let pen=null,inked=false;
    const fitCv=()=>{const s=2;cv.width=cv.clientWidth*s;cv.height=cv.clientHeight*s;g.setTransform(s,0,0,s,0,0);g.lineCap=g.lineJoin='round';g.lineWidth=2.6;g.strokeStyle='#0b4f9c'};
    const at=e=>{const r=cv.getBoundingClientRect(),s=ctx.scale();return [(e.clientX-r.left)/s,(e.clientY-r.top)/s]};
    cv.addEventListener('pointerdown',e=>{e.stopPropagation();if(e.button)return;if(!cv.width||!inked)fitCv();clear();el.classList.remove('typing');busyDraw=true;txt.classList.remove('wr');txt.textContent='';out.textContent='';hint&&hint.classList.add('gone');
      pen=at(e);inked=true;try{cv.setPointerCapture(e.pointerId)}catch(_){}});
    cv.addEventListener('pointermove',e=>{if(!pen)return;const p=at(e);g.beginPath();g.moveTo(...pen);g.lineTo(...p);g.stroke();pen=p});
    const lift=e=>{if(!pen)return;e&&e.stopPropagation();pen=null;clear();
      later(()=>sweep(()=>type('1 doodle, saved',()=>later(()=>{g.clearRect(0,0,cv.width,cv.height);inked=false;busyDraw=false;hint&&hint.classList.remove('gone');demo()},2200))),700)};
    cv.addEventListener('pointerup',lift);cv.addEventListener('pointercancel',lift);
    pad.addEventListener('keydown',e=>{if(e.key==='Enter'){busyDraw=false;demo()}});
    demo();
  });
}

/* ---------- three layouts ---------- */
const LAYOUTS={
  // D: built from the stickers on your laptop lid: one palette, paired stickers mirrored around the middle, every one live
  lid:()=>`${W.ai()}${W.name()}${W.hoop()}${W.card()}${W.hike()}${W.scan()}${W.slug()}${W.puzzle()}${W.ten()}${W.print()}${W.plan()}${W.blank()}${W.fire()}${W.ball()}`,
  // A: the round 5 stickers, now live, still scattered and tilted
  stickers:()=>`${W.name()}${W.logo()}${W.scan()}${W.puzzle()}${W.now()}${W.plan()}${W.ball()}`,
  // B: the same ideas as tidy widget tiles, like a phone home screen
  grid:()=>`<div class="g6">${W.name()}${W.scan()}${W.puzzle()}${W.court()}${W.nba()}${W.plan()}</div>`,
  // C: one big ScribbleScan pad you can write on, with a few stickers around it
  pad:()=>`${W.name()}${W.now()}${W.scan(true)}${W.puzzle()}${W.plan()}${W.ball()}`,
};

/* ---------- size the book to a real notebook shape ---------- */
function shape(root,P){
  const book=root.querySelector('.nb-book');
  const W0=root.offsetWidth,H0=root.offsetHeight;if(!W0||!H0)return;
  let w,h,l,t;
  if(P){const top=70,bot=104,availH=H0-top-bot,availW=W0-50;w=Math.min(availW,availH*RATIO);h=w/RATIO;l=Math.round((W0-w)/2)-4;t=Math.round(top+(availH-h)/2)}
  else{const top=96,bot=92;h=H0-top-bot;const pw=h*RATIO;w=pw*2;const lo=300;l=Math.round(lo+Math.max(0,(W0-lo-40-w)/2));t=top;root.style.setProperty('--pw',pw+'px')}
  Object.assign(book.style,{left:l+'px',top:t+'px',width:Math.round(w)+'px',height:Math.round(h)+'px',right:'auto',bottom:'auto',marginLeft:'0'});
}

function mount(kind){return (root,mode)=>{
  const P=mode==='phone';let closed=true,cv=null,w=null;
  const name=()=>closed?'Cover':null;
  const scale=()=>{const r=root.getBoundingClientRect();return r.width/root.offsetWidth||1};
  function build(){
    const book=root.querySelector('.nb-book');
    cv=document.createElement('div');cv.className=`nb-leaf go cv cv-stickers cv6 cv6-${kind}`;
    cv.innerHTML=`<div class="face front cv-front">${LAYOUTS[kind]()}<button type="button" class="cv-open">open</button></div><div class="face back">${P?'':`<div class="nb-in">${root.querySelector('.nb-page.l .nb-in').innerHTML}</div>`}</div>`;
    book.appendChild(cv);
    const face=cv.querySelector('.cv-front');
    wire(face,{open,scale});
    // the cover opens from its empty space, its open button, or a swipe to the left
    let sx=null;
    cv.addEventListener('pointerdown',e=>{e.stopPropagation();sx=e.clientX});
    cv.addEventListener('pointerup',e=>{e.stopPropagation();if(sx!==null&&e.clientX-sx<-30){sx=null;open();return}sx=null});
    cv.addEventListener('click',e=>{e.stopPropagation();if(e.target.closest('.wd'))return;open()});
  }
  function open(target){
    if(!closed)return;closed=false;
    if(target&&target!=='me')w.nb.go(target,{instant:true});
    root.classList.remove('closed');w.refresh();
    const c=cv;if(reduce){c.remove();return}
    c.style.transition='transform 950ms cubic-bezier(0.45,0.05,0.25,1)';c.style.transform='rotateY(-180deg)';
    setTimeout(()=>c.remove(),980);
  }
  root.classList.add('cvr','cvr-stickers','cvr6-'+kind,'r6','closed');
  w=R4.wheel(root,mode,{name,gate(k){if(!closed)return false;open();return k!=='header'}});
  shape(root,P);
  const ro=new ResizeObserver(()=>shape(root,P));ro.observe(root);
  build();w.refresh();
  return {reset(){w.reset();if(cv)cv.remove();closed=true;root.classList.add('closed');build();w.refresh()}};
};}
return {lib:{W,wire,shape,LAYOUTS},lid:mount('lid'),stickers:mount('stickers'),grid:mount('grid'),pad:mount('pad')};
})();
