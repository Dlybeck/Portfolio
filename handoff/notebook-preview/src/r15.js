/* ================= ROUND 15: roomier pages ================= */
/* Two ways to give the crowded pages bigger pictures and fewer words at a time, with the same content:
   s15a  swipe cards: long lists become a row of big cards you swipe through, one at a time
   s15b  short pages: each page keeps one big picture and the headline facts; "the whole story" opens a full paper over the notebook
   Both also give the phone page back the room the old bookmark band took. */
(()=>{
if(!window.C14)return;
const base=window.C14.pages,{BODY}=R14,{esc}=R2.lib;
const I=(f,w,h,alt,cap,cls='')=>`<figure class="${cls}"><img src="img/14/${f}" width="${w}" height="${h}" alt="${esc(alt)}" loading="lazy" decoding="async">${cap?`<figcaption>${cap}</figcaption>`:''}</figure>`;
const head=(k,t,lead)=>`${k&&k!==t?`<div class="k">${k}</div>`:''}<h2>${t}</h2>${lead?`<p class="lead">${lead}</p>`:''}`;
const btn=(id,label)=>`<button type="button" class="st15-b" data-story="${id}">${label}<span aria-hidden="true">→</span></button>`;
const bars=`<div class="bars"><div class="bar me"><span>ScribbleScan</span><i style="width:95.10%"></i><b>95.10%</b></div><div class="bar"><span>Pen to Print AI</span><i style="width:83.46%"></i><b>83.46%</b></div><div class="bar"><span>Baseline OCR</span><i style="width:74.39%"></i><b>74.39%</b></div></div>`;
const GAMES6=[['outerwilds','Outer Wilds'],['portal2','Portal 2'],['subnautica','Subnautica'],['firewatch','Firewatch'],['titanfall2','Titanfall 2'],['mkwii','Mario Kart Wii']];
const JOBS=[['denali','Innovation AI Developer','Denali Advanced Integration','2025 to now'],['scribblescan','Founder and developer','ScribbleScan LLC','2025 to 2026'],['2ndchair','Software engineering intern','2nd Chair','2024'],['tech','Technology Services Assistant II','University of Puget Sound','2022 to 2025'],
  ['tcgc','Tennis instructor','Tacoma Country and Golf Club','2023'],['gtc','On court associate','Galbraith Tennis Center','2023'],['ptc','Assistant coach','Portland Tennis Center','2022 to 2023'],['tech','Technology Services Assistant I','University of Puget Sound','2022']];
const jobRow=j=>`<li class="jr15"><span class="j14-l"><img src="img/14/w-${j[0]}.webp" alt="${esc(j[2])} logo" loading="lazy" decoding="async"></span><span><b>${j[1]}</b><small>${j[2]}</small></span><span class="when">${j[3]}</span></li>`;
const ARCH=[['2024','Python',5],['2024','C',5],['2023','Java',3],['2023','Haskell',1],['2023','Prolog',1],['2022','Java',4],['2021','Java',2]];
/* short pages: one big picture, the headline facts, and a way into the whole story */
const SHORT={
  scribblescan:()=>`${head('2025 to now','ScribbleScan','Handwriting digitization, from a hosted product to an offline, privacy-first experiment.')}
    ${I('ss-jul1.webp',900,489,'ScribbleScan web app showing a digitized handwritten page','The finished hosted version, July 2025','big15')}
    <p>Began as my 2025 capstone, grew into a hosted service and an LLC, and is now preserved as a demo.</p>
    <h4>Character accuracy, five sample pages</h4>${bars}
    ${btn('scribblescan','How it grew · 7 snapshots')}`,
  site:()=>`${head('2022 to now','This website','You\'re looking at it! Four versions so far, and how each was made.')}
    ${I('v3-1.webp',800,500,'Version 3: handwritten notes pinned to a tabletop','Version 3, April 2026','big15')}
    <ul class="tl"><li><time>2022 · v1</time>A static layout that grew into a map.</li><li><time>2025 · v2</time>The map became the website.</li><li><time>2026 · v3</time>Notes on a tabletop, seven themes.</li><li><time>2026 · v4</time>This notebook.</li></ul>
    ${btn('site','Every version · 17 snapshots')}`,
  nba:()=>`${head('2024 · partner project','NBA Prediction AI','A neural network that called the 2024 playoffs with only 2 mistakes.')}
    <div class="nba14 big15" aria-hidden="true"><span class="nba14-k">Live predictor</span><div class="nba14-r"><span>Home team</span><i>▾</i></div><div class="nba14-r"><span>Away team</span><i>▾</i></div><b>Predict</b><small>The live predictor comes over in the real build.</small></div>
    <div class="chips"><span>PyTorch</span><span>TensorFlow</span><span>Data through May 2024</span></div>
    ${btn('nba','How it works')}`,
  planner:()=>`${head('2022 · class team','Digital Planner','A calendar and to-do list built with a four-person class team.')}
    <figure class="vid big15"><video src="img/14/dp-new.mp4" poster="img/14/dp-new-poster.webp" width="720" height="402" muted loop playsinline controls preload="none"></video><figcaption>End of sprint 2, December 2022</figcaption></figure>
    <p>Two sprints, one semester, built with GitHub, Trello and daily meetings.</p>
    ${btn('planner','Both sprints and my part')}`,
  programs:()=>`${head('2021 to 2024','Programs','Software projects, experiments, and selected coursework.')}
    <div class="yr15">${ARCH.map(([y,l,n])=>`<div><span class="when">${y}</span><b>${l}</b><small>${n} program${n>1?'s':''}</small></div>`).join('')}</div>
    ${btn('programs','The whole archive · 21 programs')}`,
  printing:()=>`${head('Puzzles and models','3D printing','I always wanted more puzzle boxes to have around, so I started making them. I bet you can\'t solve them.')}
    <div class="m14s one15">${R14.M('My first puzzle box','45,000+ downloads','FirstPuzzle','FirstPuzzle_Open',['Printables','Thingiverse','MyMiniFactory','Cults'])}</div>
    ${btn('printing','All 9 models')}`,
  gaming:()=>`${head('Shorter games','Gaming','I\'ll race you in Mario Kart Wii.')}
    <div class="covers g15">${GAMES6.map(([f,a])=>`<img src="img/14/g-${f}.webp" width="260" height="390" alt="${esc(a)} cover art" title="${esc(a)}" loading="lazy" decoding="async">`).join('')}</div>
    ${btn('gaming','All 20 games')}`,
  college:()=>`${head('Class of 2025','College','CS degree, math minor, tennis team.')}
    ${I('e-upscampus.webp',800,449,'University of Puget Sound campus','University of Puget Sound','big15')}
    <p>Bachelor of Science in Computer Science with a minor in Mathematics, May 2025.</p>
    ${btn('college','Classes and clubs')}`,
};
const TITLE={scribblescan:'ScribbleScan',site:'This website',nba:'NBA Prediction AI',planner:'Digital Planner',programs:'Programs',printing:'3D printing',gaming:'Gaming',college:'College',work:'Work'};
const workShort=(a,b,title)=>`${title?head('Work · 8 roles','Work','From coaching tennis to building AI tools.'):'<h4>Earlier</h4>'}<ul class="rows jr15s">${JOBS.slice(a,b).map(jobRow).join('')}</ul>${b===8?btn('work','What I did in each role'):''}`;
const wrap=h=>`<div class="x">${h}</div>`;
function closeStory(root){root&&root.querySelectorAll('.st15').forEach(s=>s.remove())}
function pages(id,P,o){
  const root=o.root;closeStory(root);
  if(!root||!root.classList.contains('s15b'))return base(id,P,o);
  if(id==='printing')base(id,P,o); // loads the 3D viewer
  if(P){
    if(SHORT[id])return [wrap(SHORT[id]())];
    if(id==='work')return [wrap(workShort(0,8,true))];
    if(id==='school')return [wrap(`<h2>School</h2><p>Schools I've gone to and classes I've taken.</p>${SHORT.college().replace(/<div class="k">.*?<\/p>/s,'<h4>College · class of 2025</h4>')}${BODY.early().replace(/<div class="k">.*?<\/p>/s,'<h4>Early education · where it all started</h4>')}`)];
    return base(id,P,o);
  }
  if(id==='work')return [wrap(workShort(0,4,true)),wrap(workShort(4,8,false))];
  if(id==='school')return [wrap(SHORT.college()),base(id,P,o)[1]];
  const b=base(id,P,o);if(SHORT[id]&&b.length===2)return [b[0],wrap(SHORT[id]())];
  return b;
}
window.C14.pages=pages;
/* the whole story: a full paper slides up over the notebook */
function openStory(btnEl){
  const root=btnEl.closest('.c14'),book=root&&root.querySelector('.nb-book');if(!book)return;
  const id=btnEl.dataset.story;closeStory(root);
  const body=id==='work'?`${head('Work · 8 roles','Work','From coaching tennis to building AI tools.')}<ul class="rows j14s">${R14.JOBS.map(R14.job).join('')}</ul>`:BODY[id]();
  const st=document.createElement('div');st.className='nb-page st15';st.setAttribute('role','dialog');st.setAttribute('aria-label',TITLE[id]||'');
  st.innerHTML=`<div class="st15-bar"><span>${esc(TITLE[id]||'')}</span><button type="button" class="st15-x">Close</button></div><div class="nb-in st15-in"><div class="x">${body}</div></div>`;
  book.appendChild(st);requestAnimationFrame(()=>st.classList.add('on'));st.querySelector('.st15-x').focus({preventScroll:true});
}
document.addEventListener('click',e=>{
  const b=e.target.closest('.st15-b');if(b){e.stopPropagation();openStory(b);return}
  const x=e.target.closest('.st15-x');if(x){const st=x.closest('.st15');st.classList.remove('on');setTimeout(()=>st.remove(),260)}
},true);
document.addEventListener('keydown',e=>{if(e.key==='Escape')document.querySelectorAll('.st15').forEach(s=>s.remove())});
/* swipe cards: long rows scroll sideways; a counter and arrows sit under each row */
const ROWS='.s15a .nb-in .tl14, .s15a .nb-in .m14s, .s15a .nb-in .j14s, .s15a .nb-in .th14, .s15a .nb-in .ar14, .s15b .st15 .th14, .s16 .nb-in [data-sw16] :is(.tl14,.m14s,.j14s,.th14,.ar14)';
function deco(row){
  if(row.dataset.sw)return;row.dataset.sw='1';const n=row.children.length;if(n<2)return;
  row.addEventListener('pointerdown',e=>e.stopPropagation()); // a sideways swipe here moves the cards, not the page
  const nav=document.createElement('div');nav.className='sw15';nav.innerHTML=`<button type="button" aria-label="Previous card">‹</button><span>1 of ${n} · swipe</span><button type="button" aria-label="Next card">›</button>`;
  row.after(nav);const [pv,lab,nx]=[nav.children[0],nav.children[1],nav.children[2]];
  const at=()=>{const kids=[...row.children],x=row.scrollLeft;let i=0,best=1e9;kids.forEach((k,j)=>{const d=Math.abs(k.offsetLeft-row.firstElementChild.offsetLeft-x);if(d<best){best=d;i=j}});return i};
  const show=()=>{const i=at();lab.textContent=`${i+1} of ${n}${i?'':' · swipe'}`;pv.disabled=i===0;nx.disabled=i===n-1};
  const to=i=>{const k=row.children[Math.max(0,Math.min(n-1,i))];row.scrollTo({left:k.offsetLeft-row.firstElementChild.offsetLeft,behavior:reduce?'auto':'smooth'})};
  pv.onclick=e=>{e.stopPropagation();to(at()-1)};nx.onclick=e=>{e.stopPropagation();to(at()+1)};
  let t=0;row.addEventListener('scroll',()=>{cancelAnimationFrame(t);t=requestAnimationFrame(show)},{passive:true});show();
}
new MutationObserver(ms=>{for(const m of ms)for(const nd of m.addedNodes){if(nd.nodeType!==1)continue;if(nd.matches&&nd.matches(ROWS))deco(nd);nd.querySelectorAll&&nd.querySelectorAll(ROWS).forEach(deco)}})
  .observe(document.body,{childList:true,subtree:true});
})();
