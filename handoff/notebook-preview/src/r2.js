/* On a phone the book fills the screen, so a page that swings past the spine would leave the screen and vanish.
   There it tucks behind the left edge instead: past 90 degrees it narrows to a thin page edge in the gutter. */
function tuck(el,from,to,dur,ease){
  const k=[[-90,1],[-100,.34],[-120,.12],[-150,.07],[-180,.055]];
  const at=a=>{a=Math.max(-180,Math.min(0,a));if(a>=-90)return 1;for(let i=1;i<k.length;i++)if(a>=k[i][0]){const [a0,s0]=k[i-1],[a1,s1]=k[i];return s0+(s1-s0)*(a-a0)/(a1-a0)}return k[k.length-1][1]};
  const N=30,fr=[];for(let i=0;i<=N;i++){const a=from+(to-from)*i/N;fr.push({transform:`rotateY(${a}deg) scaleX(${at(a)})`})}
  el.style.transition='none';return el.animate(fr,{duration:dur,easing:ease,fill:'forwards'});
}
/* ================= ROUND 2 (real content from davidlybeck.com) ================= */
const R2=(()=>{
const esc=s=>String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;');
const PC=c=>`var(--p-${c})`;
const SECS=[
  {id:'me',tab:'Me',dial:'About',c:'lemon'},
  {id:'projects',tab:'Projects',dial:'Projects',c:'sky'},
  {id:'work',tab:'Work',dial:'Work',c:'mint'},
  {id:'school',tab:'School',dial:'School',c:'pink'},
  {id:'hobbies',tab:'Hobbies',dial:'Hobbies',c:'tangerine'},
  {id:'say',tab:'Say hi',dial:'Say hi',c:'note'},
];
const E={
  scribblescan:{sec:'projects',t:'ScribbleScan',k:'2025 to now',s:'Handwriting digitization, from a hosted product to an offline, privacy-first experiment.',star:1},
  site:{sec:'projects',t:'This website',k:'2022 to now',s:'You\'re looking at it! Four versions so far, and how each was made.'},
  nba:{sec:'projects',t:'NBA Prediction AI',k:'2024 · partner project',s:'A neural network that called the 2024 playoffs with only 2 mistakes.'},
  planner:{sec:'projects',t:'Digital Planner',k:'2022 · class team',s:'A calendar and to-do list built with a four-person class team.'},
  programs:{sec:'projects',t:'Programs',k:'2021 to 2024',s:'Software experiments and selected coursework, from sorts to a Connect 4 bot.'},
  printing:{sec:'hobbies',t:'3D printing',k:'Puzzles and models',s:'Puzzle boxes I designed, one with 45,000+ downloads. I bet you can\'t solve them.'},
  gaming:{sec:'hobbies',t:'Gaming',k:'Shorter games',s:'Some of my favorites. I\'ll race you in Mario Kart Wii.'},
  tennis:{sec:'hobbies',t:'Tennis',k:'Since middle school',s:'I\'ve played for as long as I remember. Let me know if you want to hit.'},
  college:{sec:'school',t:'College',k:'Class of 2025',s:'CS degree, math minor, tennis team.'},
  early:{sec:'school',t:'Early education',k:'Portland',s:'The classics.'},
};
const LISTS={projects:['scribblescan','site','nba','planner','programs'],hobbies:['printing','gaming','tennis'],school:['college','early']};
const JOBS=[
  {when:'Aug 2025 to now',t:'Innovation AI Developer',org:'Denali Advanced Integration',s:'Building internal AI tools and helping people across the company adopt AI in their own roles.'},
  {when:'Feb 2025 to Apr 2026',t:'Founder and developer',org:'ScribbleScan LLC',s:'Solo-built a handwriting-digitization service. The company has closed; a demo remains.'},
  {when:'Jun to Sep 2024',t:'Software engineering intern',org:'2nd Chair',s:'Researched ways to make AI document parsing more relevant and accurate.'},
  {when:'2022 to 2025',t:'Technology Services Assistant',org:'University of Puget Sound',s:'Answered calls and tickets from faculty, staff and students, then fixed or routed them.'},
  {when:'2022 to 2023',t:'Tennis coach',org:'Three clubs in Portland and Tacoma',s:'Group and private lessons for players from age 4 to adults.'},
];
const img=(src,w,h,alt,cap)=>`<figure><img src="img/${src}" width="${w}" height="${h}" alt="${esc(alt)}" loading="lazy" decoding="async">${cap?`<figcaption>${esc(cap)}</figcaption>`:''}</figure>`;
const head=(id)=>{const e=E[id];return `<div class="k">${esc(e.k)}</div><h2>${esc(e.t)}</h2><p class="lead">${esc(e.s)}</p>`};
const BODY={
  scribblescan:()=>`${head('scribblescan')}
    ${img('scribblescan.webp',1679,912,'ScribbleScan web app showing a digitized handwritten page','The finished hosted version, July 2025')}
    <p>It began as my 2025 capstone, grew into a hosted service and an LLC, and is now preserved as a demo. It digitized handwritten pages while keeping images and other non-text parts in the result.</p>
    <h4>Character accuracy, five sample pages</h4>
    <div class="bars"><div class="bar me"><span>ScribbleScan</span><i style="width:95.10%"></i><b>95.10%</b></div><div class="bar"><span>Pen to Print AI</span><i style="width:83.46%"></i><b>83.46%</b></div><div class="bar"><span>Baseline OCR</span><i style="width:74.39%"></i><b>74.39%</b></div></div>
    <figcaption>A small project comparison, not a general benchmark.</figcaption>
    <h4>How it grew</h4>
    <ul class="tl"><li><time>Jan 2025</time>Capstone proposal</li><li><time>Feb 7</time>First working version, results line by line</li><li><time>Mar 12</time>PDF export, corrections and accuracy scores</li><li><time>Apr 28</time>The version I presented for my capstone</li><li><time>Jun 25</time>ScribbleScan LLC: profiles, cloud database, paid tiers</li><li><time>Jul 1</time>Demo mode, and I called it finished</li></ul>
    <h4>What I'm exploring now</h4>
    <p>An offline, privacy-first mobile reader: on-device transcription, local correction, history and export. It's active research, not a finished product.</p>
    <span class="hn">still going</span>`,
  site:()=>`${head('site')}
    <h4>Versions</h4>
    <ul class="tl"><li><time>Dec 2022 · v1</time>A hand-coded static layout that grew into an exploratory map.</li><li><time>Jan 2025 · v2</time>The map became the website, so you explore pages without opening them.</li><li><time>Apr 2026 · v3</time>Handwritten notes pinned to a tabletop, then seven visual themes.</li><li><time>Nov 2026 · v4</time>This one, rebuilt on my own design system.</li></ul>
    <p>The idea that never changed: exploring the site should feel like exploring a place.</p>`,
  nba:()=>`${head('nba')}
    <p>A partner project: a convolutional neural network trained on a custom-made data set of NBA stats. We built it in PyTorch, and a very similar version in TensorFlow.</p>
    <p>It's good at picking the winner. The exact point differential is harder, as expected.</p>
    <div class="chips"><span>PyTorch</span><span>TensorFlow</span><span>Data through May 2024</span></div>`,
  planner:()=>`${head('planner')}
    <p>A web app built over two sprints for my Software Engineering course, using GitHub, Trello and daily stand-ups.</p>
    <h4>My part</h4>
    <ul class="tl"><li><time>Sprint 1 · Nov 2022</time>Making assignments show up correctly, and drag and drop onto the calendar.</li><li><time>Sprint 2 · Dec 2022</time>Events, different-length items without overlaps, and calendar scrolling.</li></ul>`,
  programs:()=>`${head('programs')}
    <dl class="dl"><dt>Negamax Connect 4 bot</dt><dd>2024 · Python</dd><dt>A* sliding puzzle solver</dt><dd>2024 · Python</dd><dt>Cat vs dog detector (CNN)</dt><dd>2024 · Python</dd><dt>Parallel matrix multiplication</dt><dd>2024 · C</dd><dt>Mini shell</dt><dd>2024 · C</dd><dt>Red-black tree search</dt><dd>2023 · Java</dd><dt>Evil Hangman</dt><dd>2023 · Haskell</dd><dt>Mass Covid test process</dt><dd>2023 · Prolog</dd></dl>`,
  printing:()=>`${head('printing')}
    <p>I always wanted more puzzle boxes to have around. So I started making them.</p>
    <h4>Puzzles</h4>
    <dl class="dl"><dt>My first puzzle box</dt><dd>45,000+ downloads</dd><dt>The couch puzzle box</dt><dd>3,000+</dd><dt>The gift puzzle box</dt><dd>800+</dd><dt>Simple block puzzle</dt><dd>600+</dd><dt>The sliding puzzle box</dt><dd>private</dd></dl>
    <h4>Other models</h4>
    <dl class="dl"><dt>Galaxy S20 FE case</dt><dd>2,500+</dd><dt>Pixel 3 case</dt><dd>300+</dd><dt>Tech accessory organizer</dt><dd>50+</dd></dl>`,
  gaming:()=>`${head('gaming')}
    <p>I tend to like shorter games, so I've cycled through a lot of them. A few I've really enjoyed:</p>
    <div class="covers">${[['OuterWilds','Outer Wilds'],['Portal2','Portal 2'],['Subnautica','Subnautica'],['Firewatch','Firewatch'],['Titanfall2','Titanfall 2'],['MKWii','Mario Kart Wii']].map(([f,a])=>`<img src="img/game-${f}.webp" width="300" height="450" alt="${a} cover art" loading="lazy" decoding="async">`).join('')}</div>
    <figcaption>Six of the twenty on my current list.</figcaption>`,
  tennis:()=>`${head('tennis')}
    ${img('forehand.webp',723,484,'David hitting a forehand')}
    <p>I've played competitively since middle school: four years on my high school's varsity team, four more on the University of Puget Sound team. Still hitting whenever I can.</p>`,
  college:()=>`${head('college')}
    ${img('ups-tennis.webp',710,326,'University of Puget Sound tennis')}
    <p>University of Puget Sound: a Bachelor of Science in Computer Science with a minor in Mathematics, finished May 2025.</p>
    <h4>A few of my classes</h4>
    <div class="chips"><span>Intro to AI</span><span>Algorithms and Data Structures</span><span>Operating Systems</span><span>Cryptography and Network Security</span><span>Databases</span><span>Capstone</span><span>Linear Algebra</span></div>
    <h4>Outside class</h4>
    <p>Four years on the tennis team, and about two years in the Maroon Society, which connects students and alumni.</p>`,
  early:()=>`${head('early')}
    <ul class="tl"><li><time>High school</time>Grant High School</li><li><time>Middle school</time>Beaumont Middle School</li><li><time>Elementary</time>Alameda Elementary School</li></ul>`,
};
const workHTML=(from=0,to=JOBS.length,title=true)=>`${title?`<div class="k">Work · ${JOBS.length} roles</div><h2>From coaching tennis to building AI tools</h2>`:''}<ul class="rows">${JOBS.slice(from,to).map(j=>`<li><span class="when">${esc(j.when)}</span><b>${esc(j.t)}</b><small>${esc(j.org)}. ${esc(j.s)}</small></li>`).join('')}</ul>`;
const aboutHTML=(logo)=>`<div class="me-row">${logo?`<img alt="" src="${LOGO}">`:''}<div><div class="k">Hi, I'm David</div><h1>David Lybeck</h1></div></div>
  <p class="lead">I build AI tools at Denali, and on my own time I make things like ScribbleScan, puzzle boxes and this website.</p>
  <ul class="facts"><li><span>Now</span><div>Innovation AI Developer at Denali</div></li><li><span>Studied</span><div>Computer science, University of Puget Sound, 2025</div></li><li><span>Made</span><div>ScribbleScan, from capstone to company</div></li><li><span>Plays</span><div>Tennis, since middle school</div></li></ul>`;
const sayHTML=()=>`<div class="k">Say hi</div><h2>Let me know if you want to hit</h2>
  <div class="contact"><div><b>GitHub</b><span>github.com/Dlybeck</span></div><div><b>Email</b><span class="todo">to add</span></div><div><b>LinkedIn</b><span class="todo">to add</span></div><div><b>Resume</b><span class="todo">new copy to add</span></div></div>`;
const detail=id=>`<div class="x">${BODY[id]()}</div>`;

/* ---------- shared sheet (same look as round 1) ---------- */
function sheetOn(root){
  const scrim=document.createElement('div');scrim.className='scrim';
  const sh=document.createElement('div');sh.className='sheet';sh.setAttribute('role','dialog');
  root.append(scrim,sh);
  const api={open(h){sh.innerHTML=`<button class="btn ghost close" data-close>Close</button>`+h;sh.scrollTop=0;scrim.classList.add('open');sh.classList.add('open')},close(){scrim.classList.remove('open');sh.classList.remove('open')}};
  scrim.onclick=api.close;sh.addEventListener('click',e=>{if(e.target.closest('[data-close]'))api.close()});
  return api;
}
const top=()=>`<header class="m-top"><button class="m-word" data-home><img alt="" src="${LOGO}">David Lybeck</button><button class="btn ghost" data-say>Say hi</button></header>`;

/* ---------- notebook engine ---------- */
const PH=['me','toc','projects','scribblescan','site','nba','planner','programs','work','school','hobbies','printing','gaming','tennis','say'];
const DK=['me','scribblescan','site','nba','planner','programs','work','school','printing','gaming','tennis','say'];
const secOf=id=>{id=String(id).split('+')[0];return id==='toc'?'me':SECS.some(s=>s.id===id)?id:E[id].sec};
let PGO=PH;const pg=id=>PGO.indexOf(id)+1;
function notebook(root,mode,{tabs=true,onView,hint}={}){
  const P=mode==='phone';
  const X=window.C14&&window.C14.order&&root.classList.contains('s17')?window.C14.order():null;PGO=X?X.ph:PH;
  const ORDER=X?(P?X.ph:X.dk):(P?PH:DK);
  const toc=(items,cur)=>`<ul class="toc">${items.map(id=>{const t=E[id]?E[id].t:SECS.find(s=>s.id===id).tab;const s=E[id]?E[id].s:'';return `<li><button data-open="${id}" class="${id===cur?'cur':''}"><span class="twol"><b>${esc(t)}</b>${s?`<small>${esc(s)}</small>`:''}</span><span class="dots"></span><span class="pg">p.${pg(id)}</span></button></li>`}).join('')}</ul>`;
  const contents=()=>`<div class="k">Contents</div><h2>What's inside</h2>${toc(['projects','work','school','hobbies','say'])}<span class="hn">${hint||(tabs?'pick a tab, or turn the page':'spin the dial, or turn the page')}</span>`;
  const list=(sec,cur)=>{const s=SECS.find(x=>x.id===sec);const lead={projects:'Personal projects I\'ve developed, and how they were made.',hobbies:'All my favorites! (Coding gets its own section.)',school:'Schools I\'ve gone to and classes I\'ve taken.'}[sec];
    return `<div class="k">${LISTS[sec].length} entries</div><h2>${s.tab}</h2><p>${lead}</p>${toc(LISTS[sec],cur)}`};
  const schoolBoth=()=>`<div class="k">School</div><h2>Schools I've gone to</h2>${BODY.college().replace(/<div class="k">.*?<\/h2>/s,'<h4>College · class of 2025</h4>')}${BODY.early().replace(/<div class="k">.*?<\/h2>/s,'<h4>Before that · the classics</h4>').replace(/<p class="lead">.*?<\/p>/s,'')}`;
  const wrap=h=>`<div class="x">${h}</div>`;
  /* every page is tagged with its id and half, and a later round may dress it (round 11 adds sticker accents) */
  function pages(id){return pages0(id).map((h,i)=>{h=h.replace('<div class="x"',`<div class="x" data-pg="${id}" data-half="${i}"`);return typeof window.PAGE_DECO==='function'?window.PAGE_DECO(root,id,i,h,P):h})}
  function pages0(id){
    if(window.C14&&root.classList.contains('c14'))return window.C14.pages(id,P,{toc,hint:hint||(tabs?'pick a tab, or turn the page':'spin the dial, or turn the page'),LOGO,root});
    if(P){
      if(id==='me') return [wrap(aboutHTML(true))];
      if(id==='toc') return [wrap(contents())];
      if(id==='projects'||id==='hobbies') return [wrap(list(id))];
      if(id==='work') return [wrap(workHTML())];
      if(id==='school') return [wrap(schoolBoth())];
      if(id==='say') return [wrap(sayHTML()+`<span class="hn" style="margin-top:14px">thanks for flipping through</span>`)];
      return [detail(id)];
    }
    if(id==='me') return [wrap(aboutHTML(true)),wrap(contents())];
    if(id==='work') return [wrap(workHTML(0,3)),wrap(`<h4>Earlier</h4>`+workHTML(3,5,false)+`<span class="hn" style="margin-top:12px">coaching taught me to explain things simply</span>`)];
    if(id==='school') return [detail('college'),detail('early')];
    if(id==='say') return [wrap(sayHTML()),wrap(`<div class="k">About this notebook</div><h2>How it's made</h2><p>Drawn with dlybeck design, my own design system. The pages that turn are the whole interface.</p><span class="hn">thanks for flipping through</span>`)];
    const s=E[id].sec;return [wrap(list(s,id)),detail(id)];
  }
  const norm=id=>(!P&&(id==='projects'||id==='hobbies'))?LISTS[id][0]:id;
  root.insertAdjacentHTML('beforeend',`${tabs?`<div class="nb-tabs" role="tablist">${SECS.slice(0,5).map(s=>`<button class="nb-tab" role="tab" data-sec="${s.id}" style="--pc:${PC(s.c)}">${s.tab}</button>`).join('')}</div>`:''}
   <div class="nb-book"><div class="nb-cover"></div>${P?`<div class="nb-page one"><div class="nb-in"></div></div>`:`<div class="nb-page l"><div class="nb-in"></div></div><div class="nb-page r"><div class="nb-in"></div></div><div class="nb-gutter"></div>`}
   <div class="nb-leaf"><div class="face front"></div><div class="face back"></div></div><div class="nb-band"></div>
   <span class="nb-pn lft"></span><span class="nb-pn rgt"></span>
   <button class="nb-ear prev" aria-label="Previous page"></button><button class="nb-ear next" aria-label="Next page"></button><span class="nb-flip">flip</span></div>`);
  const book=root.querySelector('.nb-book'),leaf=book.querySelector('.nb-leaf'),front=leaf.querySelector('.front'),back=leaf.querySelector('.back');
  const pL=book.querySelector('.nb-page .nb-in'),pR=P?null:book.querySelector('.nb-page.r .nb-in');
  const pnL=book.querySelector('.nb-pn.lft'),pnR=book.querySelector('.nb-pn.rgt'),prev=book.querySelector('.prev'),next=book.querySelector('.next'),flip=book.querySelector('.nb-flip');
  let cur='me',busy=false,pending=null,seq=0,flyN=0;const sideSeq={L:0,R:0};
  function paint(id){root.classList.toggle('nb-turned',ORDER.indexOf(id)>0);
    const [l,r]=pages(id);pL.innerHTML=l;pL.scrollTop=0;if(pR){pR.innerHTML=r;pR.scrollTop=0}
    const s=secOf(id);
    if(P) pnR.textContent=`p.${pg(id)} of ${PGO.length}`;
    else{pnL.textContent=SECS.find(x=>x.id===s).tab;pnR.textContent=`p.${pg(id)}`}
    const i=ORDER.indexOf(id);prev.disabled=i<=0;next.disabled=i>=ORDER.length-1;
    root.querySelectorAll('.nb-tab').forEach(t=>{const on=t.dataset.sec===s;t.toggleAttribute('aria-current',on);t.setAttribute('aria-selected',on)});
  }
  function go(id,{instant=false,silent=false}={}){
    id=norm(id);
    if(busy){pending=id;return}
    if(id===cur)return;
    const fwd=ORDER.indexOf(id)>ORDER.indexOf(cur);
    if(!silent&&onView) onView(id);
    if(instant||reduce){cur=id;paint(id);return}
    busy=true;flip.style.opacity=0;const g=++seq;sideSeq.L=sideSeq.R=g;
    const oldL=pL.innerHTML,oldR=pR?pR.innerHTML:null;const [nl,nr]=pages(id);
    const inner=h=>`<div class="nb-in">${h}</div>`;
    leaf.style.transition='none';front.className='face front';back.className='face back';
    if(P){leaf.style.left='0';leaf.style.right='0';leaf.style.transformOrigin='left center';
      if(fwd){front.innerHTML=inner(oldL);back.innerHTML='';leaf.style.transform='rotateY(0deg)';cur=id;paint(id)}
      else{front.innerHTML=inner(nl);back.innerHTML='';leaf.style.transform='rotateY(-180deg)'}}
    else if(fwd){leaf.style.left='50%';leaf.style.right='0';leaf.style.transformOrigin='left center';
      front.innerHTML=inner(oldR);front.classList.add('r-face');back.innerHTML=inner(nl);leaf.style.transform='rotateY(0deg)';pR.innerHTML=nr}
    else{leaf.style.left='0';leaf.style.right='50%';leaf.style.transformOrigin='right center';
      front.innerHTML=inner(oldL);back.innerHTML=inner(nr);back.classList.add('r-face');leaf.style.transform='rotateY(0deg)';pL.innerHTML=nl}
    leaf.classList.add('go');void leaf.offsetWidth;let an=null;
    if(P)an=tuck(leaf,fwd?0:-180,fwd?-180:0,720,'cubic-bezier(0.45,0.05,0.25,1)');
    else{leaf.style.transition='transform 720ms cubic-bezier(0.45,0.05,0.25,1)';
    leaf.style.transform=fwd?'rotateY(-180deg)':'rotateY(180deg)';}
    setTimeout(()=>{if(an)an.cancel();leaf.classList.remove('go');if(seq===g){cur=id;paint(id)}busy=false;
      if(pending&&pending!==cur){const p=pending;pending=null;go(p,{silent:true})}else pending=null},740);
  }
  /* riffle: one quick leaf per page, several can be in the air at once (used by the round 4 wheel) */
  function nav(id){const s=secOf(id),i=ORDER.indexOf(id);root.classList.toggle('nb-turned',i>0);prev.disabled=i<=0;next.disabled=i>=ORDER.length-1;
    root.querySelectorAll('.nb-tab').forEach(t=>{const on=t.dataset.sec===s;t.toggleAttribute('aria-current',on);t.setAttribute('aria-selected',on)})}
  function setSide(side,id){const [l,r]=pages(id);
    if(side==='L'){pL.innerHTML=l;pL.scrollTop=0;if(P)pnR.textContent=`p.${pg(id)} of ${PGO.length}`;else pnL.textContent=SECS.find(x=>x.id===secOf(id)).tab}
    else{pR.innerHTML=r;pR.scrollTop=0;pnR.textContent=`p.${pg(id)}`}}
  function riffle(id,{dur=420}={}){
    id=norm(id);if(id===cur)return;
    const fwd=ORDER.indexOf(id)>ORDER.indexOf(cur);flip.style.opacity=0;
    if(reduce||dur<=0||flyN>=8){cur=id;sideSeq.L=sideSeq.R=++seq;paint(id);return}
    const my=++seq,[nl,nr]=pages(id),inner=h=>`<div class="nb-in">${h}</div>`;
    const lf=document.createElement('div');lf.className='nb-leaf go rf-leaf';lf.innerHTML='<div class="face front"></div><div class="face back"></div>';
    const fr=lf.firstChild,bk=lf.lastChild;let startSide=null,landSide=null,from=0,to=-180;
    if(P){lf.style.left='0';lf.style.right='0';lf.style.transformOrigin='left center';
      if(fwd){fr.innerHTML=inner(pL.innerHTML);startSide='L'}else{fr.innerHTML=inner(nl);landSide='L';from=-180;to=0}}
    else if(fwd){lf.style.left='50%';lf.style.right='0';lf.style.transformOrigin='left center';fr.innerHTML=inner(pR.innerHTML);fr.classList.add('r-face');bk.innerHTML=inner(nl);startSide='R';landSide='L'}
    else{lf.style.left='0';lf.style.right='50%';lf.style.transformOrigin='right center';fr.innerHTML=inner(pL.innerHTML);bk.innerHTML=inner(nr);bk.classList.add('r-face');startSide='L';landSide='R';to=180}
    lf.style.zIndex=fwd?60-my%50:10+my%50;
    cur=id;nav(id);if(startSide){sideSeq[startSide]=my;setSide(startSide,id)}
    book.appendChild(lf);flyN++;lf.style.transform=`rotateY(${from}deg)`;void lf.offsetWidth;
    if(P)tuck(lf,from,to,dur,'cubic-bezier(0.4,0.1,0.3,1)');else{lf.style.transition=`transform ${dur}ms cubic-bezier(0.4,0.1,0.3,1)`;lf.style.transform=`rotateY(${to}deg)`;}
    setTimeout(()=>{if(landSide&&my>sideSeq[landSide]){sideSeq[landSide]=my;setSide(landSide,id)}lf.remove();flyN--},dur+30);
  }
  const step=d=>{const i=ORDER.indexOf(cur);if(ORDER[i+d])go(ORDER[i+d])};
  prev.onclick=()=>step(-1);next.onclick=()=>step(1);
  let sx=null,sy=0;
  book.addEventListener('pointerdown',e=>{sx=e.clientX;sy=e.clientY});
  book.addEventListener('pointerup',e=>{if(sx===null)return;const k=root.getBoundingClientRect().width/(P?390:1277);const dx=(e.clientX-sx)/k,dy=(e.clientY-sy)/k;sx=null;if(Math.abs(dx)>50&&Math.abs(dx)>Math.abs(dy)*1.3)step(dx<0?1:-1)});
  book.addEventListener('pointercancel',()=>{sx=null});
  root.addEventListener('click',e=>{
    const o=e.target.closest('.nb-book [data-open]');if(o)go(o.dataset.open);
    const t=e.target.closest('[data-sec]');if(t)go(t.dataset.sec);
  });
  paint('me');
  return {go,riffle,order:ORDER,get cur(){return cur},reset(){busy=false;pending=null;seq++;sideSeq.L=sideSeq.R=seq;book.querySelectorAll('.rf-leaf').forEach(x=>x.remove());flyN=0;leaf.classList.remove('go');cur='me';paint('me');flip.style.opacity=1}};
}

/* ---------- dial component ---------- */
function dial(root,mode,{small=false,onScrub,onSnap}={}){
  const P=mode==='phone';const n=SECS.length;
  const STEP=P?(small?44:48):36,R=P?(small?110:134):196;
  root.insertAdjacentHTML('beforeend',`<div class="dl-wrap ${small&&P?'small':''}"><div class="dl-pointer"></div><div class="dl-dial" role="slider" tabindex="0" aria-label="Section" aria-valuemin="0" aria-valuemax="${n-1}">${SECS.map((s,i)=>`<div class="dl-lab"><button data-i="${i}" tabindex="-1" style="--dot:${PC(s.c)}"><i></i>${s.dial}</button></div>`).join('')}</div></div>
    <div class="dl-arrows"><button type="button" aria-label="Previous section" data-step="-1">‹</button><button type="button" aria-label="Next section" data-step="1">›</button></div>`);
  const el=root.querySelector('.dl-dial'),labs=[...el.querySelectorAll('button')];
  const base=P?-90:0;
  labs.forEach((b,i)=>{const a=(base+i*STEP)*Math.PI/180;b.style.left=Math.cos(a)*R+'px';b.style.top=Math.sin(a)*R+'px';b.style.transform=`translate(-50%,-50%) rotate(${i*STEP}deg)`});
  let idx=0,rot=0,d=null;
  function render(r,drag){rot=r;el.style.rotate=r+'deg';const f=-r/STEP;const c=Math.max(0,Math.min(n-1,Math.round(f)));
    labs.forEach((b,i)=>{b.classList.toggle('cur',i===c);b.style.opacity=Math.max(.18,1-Math.max(0,Math.abs(i-f)-.5)*(P?.45:.3)).toFixed(2)});el.setAttribute('aria-valuenow',c);el.setAttribute('aria-valuetext',SECS[c].dial);onScrub&&onScrub(f,drag)}
  function to(i,{silent=false}={}){i=Math.max(0,Math.min(n-1,i));const changed=i!==idx;idx=i;el.classList.remove('drag');render(-i*STEP,false);if(!silent&&onSnap)onSnap(i,changed)}
  const ang=e=>{const r=el.getBoundingClientRect();return Math.atan2(e.clientY-(r.top+r.height/2),e.clientX-(r.left+r.width/2))*180/Math.PI};
  el.addEventListener('pointerdown',e=>{if(e.button)return;d={a:ang(e),r:rot,moved:false,t:e.target};try{el.setPointerCapture(e.pointerId)}catch(_){}});
  el.addEventListener('pointermove',e=>{if(!d)return;let da=ang(e)-d.a;if(da>180)da-=360;if(da<-180)da+=360;
    if(!d.moved&&Math.abs(da)>3){d.moved=true;el.classList.add('drag');root.dispatchEvent(new Event('dialgrab'))}
    if(d.moved){let r=d.r+da;const lo=-(n-1)*STEP;if(r>0)r*=.3;if(r<lo)r=lo+(r-lo)*.3;d.a=ang(e);d.r=r;render(r,true)}});
  const up=()=>{if(!d)return;const {moved,t}=d;d=null;if(moved)to(Math.round(-rot/STEP));else{const b=t.closest&&t.closest('button[data-i]');if(b)to(+b.dataset.i)}};
  el.addEventListener('pointerup',up);el.addEventListener('pointercancel',()=>{if(d){d=null;to(Math.round(-rot/STEP))}});
  el.addEventListener('keydown',e=>{if(e.key==='ArrowRight'||e.key==='ArrowDown'){e.preventDefault();to(idx+1)}if(e.key==='ArrowLeft'||e.key==='ArrowUp'){e.preventDefault();to(idx-1)}});
  root.addEventListener('click',e=>{const s=e.target.closest('[data-step]');if(s)to(idx+ +s.dataset.step)});
  el.classList.add('drag');render(0,true);requestAnimationFrame(()=>el.classList.remove('drag'));
  return {to,get idx(){return idx},instant(i){el.classList.add('drag');idx=i;render(-i*STEP,true);requestAnimationFrame(()=>el.classList.remove('drag'))}};
}

/* ---------- option A: notebook ---------- */
function mountNotebook(root,mode){
  root.innerHTML=top();
  const nb=notebook(root,mode,{tabs:true});
  root.addEventListener('click',e=>{if(e.target.closest('[data-home]'))nb.go('me');if(e.target.closest('[data-say]'))nb.go('say')});
  return {reset:nb.reset};
}

/* ---------- option B: the dial ---------- */
function mountDial(root,mode){
  const P=mode==='phone';
  const card=id=>{const e=E[id];return `<button class="dlo-card ${e.star?'star':''}" data-open="${id}" style="--pc:${PC(SECS.find(s=>s.id===e.sec).c)}"><span class="sw"></span><span class="kk">${esc(e.k)}</span><b>${esc(e.t)}</b><small>${esc(e.s)}</small></button>`};
  const panels={
    me:aboutHTML(false)+`<span class="hn" style="margin-top:12px">${P?'spin the dial with your thumb ↓':'← grab the dial and spin it'}</span>`,
    projects:`<div class="k">Projects · 5</div><h2>Things I've made</h2><p class="lead">Personal projects I've developed, and how they were made.</p><div class="dlo-cards five">${LISTS.projects.map(card).join('')}</div>`,
    work:workHTML(),
    school:`<div class="k">School</div><h2>Schools I've gone to</h2><p class="lead">And the classes I've taken.</p><div class="dlo-cards">${LISTS.school.map(card).join('')}</div>`,
    hobbies:`<div class="k">Hobbies · 3</div><h2>All my favorites</h2><p class="lead">Coding gets its own section.</p><div class="dlo-cards">${LISTS.hobbies.map(card).join('')}</div>`,
    say:sayHTML(),
  };
  root.innerHTML=top()+`<div class="dlo-strip">${SECS.map(s=>`<section class="dlo-panel x" data-p="${s.id}">${panels[s.id]}</section>`).join('')}</div>`;
  const strip=root.querySelector('.dlo-strip'),n=SECS.length;
  const dl=dial(root,mode,{onScrub(f,drag){strip.classList.toggle('drag',!!drag);strip.style.transform=`translateX(${-f*(100/n)}%)`}});
  root.addEventListener('dialgrab',()=>{const h=root.querySelector('.dlo-panel .hn');if(h)h.style.opacity=.35});
  const sheet=sheetOn(root);
  root.addEventListener('click',e=>{
    const o=e.target.closest('[data-open]');if(o)sheet.open(detail(o.dataset.open));
    if(e.target.closest('[data-home]')){sheet.close();dl.to(0)}
    if(e.target.closest('[data-say]')){sheet.close();dl.to(5)}
  });
  return {reset(){sheet.close();strip.classList.add('drag');dl.instant(0);requestAnimationFrame(()=>strip.classList.remove('drag'))}};
}

/* ---------- option C: notebook turned by the dial ---------- */
function mountMix(root,mode){
  root.classList.add('mix');
  root.innerHTML=top();
  let dl;
  const nb=notebook(root,mode,{tabs:false,onView(id){dl&&dl.to(SECS.findIndex(s=>s.id===secOf(id)),{silent:true})}});
  dl=dial(root,mode,{small:true,onSnap(i,changed){if(changed||secOf(nb.cur)!==SECS[i].id)nb.go(SECS[i].id,{silent:true})}});
  root.addEventListener('click',e=>{if(e.target.closest('[data-home]'))nb.go('me');if(e.target.closest('[data-say]'))nb.go('say')});
  return {reset(){nb.reset();dl.instant(0)}};
}
return {notebook:mountNotebook,dial:mountDial,mix:mountMix,lib:{notebook,secOf,SECS,E,pg,top,PC,esc,PH,DK}};
})();
