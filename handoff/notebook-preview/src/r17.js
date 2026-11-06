/* ================= ROUND 17: stories that flow onto the next page ================= */
/* From his notes on round 15: the swipe felt awkward in places and the tap-to-open shortcut felt forced.
   So no shortcut: a long story simply carries on over the next pages of the notebook, a few big pictures per page.
   Swipe stays only where a page is a real row of like things: the snapshots of each site version, the site themes, the 3D models.
   Same words and pictures as round 14. Only mounts with the s17 class. */
(()=>{
if(!window.C14)return;
const prev=window.C14.pages,base=R14.pages;
const {I,L,head,step,M,VERS,THEMES,JOBS,job,COURSES,ARCHIVE,GAMES}=R14,{esc}=R2.lib;
const cont=(t,k,n)=>`<div class="k">${t} · ${k} of ${n}</div>`;
const bars=`<div class="bars"><div class="bar me"><span>ScribbleScan</span><i style="width:95.10%"></i><b>95.10%</b></div><div class="bar"><span>Pen to Print AI</span><i style="width:83.46%"></i><b>83.46%</b></div><div class="bar"><span>Baseline OCR</span><i style="width:74.39%"></i><b>74.39%</b></div></div>`;
const cover=([f,a])=>`<img src="img/14/g-${f.toLowerCase()}.webp" width="260" height="390" alt="${esc(a)} cover art" title="${esc(a)}" loading="lazy" decoding="async">`;
const vstep=(n,v)=>([k,h,d,t])=>step(d,k?`${v}-${k}.webp`:'',800,h,`${n}, ${d}`,t);
/* each entry is a list of pages; [html, swipe?] */
const CH={
  scribblescan:[
    [`${head('2025 to now','ScribbleScan','Handwriting digitization, from a hosted product to an offline, privacy-first experiment.')}
      ${I('ss-jul1.webp',900,489,'ScribbleScan web app showing a digitized handwritten page','The finished hosted version, July 2025')}
      <p>ScribbleScan began as my 2025 capstone, grew into a hosted handwriting-digitization service and LLC, and is now preserved as a demo. It digitized handwritten pages while keeping images and other non-text elements in the resulting document.</p>${L('View the preserved demo')}`],
    [`<h2>How well it read</h2><h4>Character accuracy, five sample pages</h4>${bars}<figcaption>A small project comparison, not a general benchmark.</figcaption>
      <h2 class="h17">What I'm exploring now</h2><p>I'm rebuilding the idea around an offline, privacy-first mobile reader: on-device transcription, preserving non-text visuals as source crops, and local correction, history and export. It is active R&amp;D, not a finished product.</p>`],
    [`<h2>How it grew</h2><ul class="tl tl14">
      ${step('January 2025 · proposal','',0,0,'','The initial proposal I submitted for my capstone. It\'s interesting to see what I stuck with (like the export options) and what I changed (target audience, some features).',L('Read the proposal'))}
      ${step('February 7th 2025','ss-feb7.webp',900,489,'First working version of ScribbleScan','The first working version. The results split each line into a section and showed them line by line. Rough, but it matched the design I had in mind, and I was very happy with it at the time.')}
      ${step('February 8th 2025','ss-feb8.webp',900,488,'ScribbleScan a day later with larger tiles','Only a day later, but big UI improvements: much larger tiles, and the digitize button hides once clicked. That stayed in every later version.')}</ul>`],
    [`<h2>From tool to product</h2><ul class="tl tl14">
      ${step('March 12th 2025','ss-mar12.webp',900,489,'ScribbleScan with export and corrections','A month after the proof of concept: PDF export, copy to clipboard, corrections and accuracy scores. The focus shifted from a demo to a usable tool.')}
      ${step('April 28th 2025','ss-apr28.webp',900,489,'ScribbleScan as presented for the capstone','The version I presented for my capstone: a batch page limit, Google sign-in and a toned down UI. Not a full product, but a finished tool.')}</ul>`],
    [`<h2>A complete product</h2><ul class="tl tl14">
      ${step('June 25th 2025','ss-jun25.webp',900,489,'ScribbleScan as a hosted product','After graduating, ScribbleScan LLC full time: profiles and support, a cloud-hosted database, paid tiers and many smaller features. A complete product.')}
      ${step('July 1st 2025','ss-jul1.webp',900,489,'ScribbleScan with demo mode','A week later I called it finished. The big addition was a demo mode, so anyone could try pre-calculated pages of tough handwriting without costing the service.')}</ul>`],
  ],
  site:[
    [`${head('2022 to now','This website','You\'re looking at it! Four versions so far, and how each was made.')}
      ${I('v3-1.webp',800,500,'Version 3: handwritten notes pinned to a tabletop','Version 3, April 2026')}
      <ul class="tl"><li><time>Dec 2022 · v1</time>A hand-coded static layout that grew into an exploratory map.</li><li><time>Jan 2025 · v2</time>The map became the website, so you explore pages without opening them.</li><li><time>Apr 2026 · v3</time>Handwritten notes pinned to a tabletop, then seven visual themes.</li><li><time>Nov 2026 · v4</time>This one, rebuilt on my own design system.</li></ul>`],
    ...VERS.map(([n,when,v,steps])=>[`<h2>${n}</h2><p class="when">${when} · ${steps.length} snapshots</p><ul class="tl tl14">${steps.filter(s=>s[0]).map(vstep(n,v)).join('')}</ul>
      ${steps.filter(s=>!s[0]).map(([,,d,t])=>`<h2 class="h17">Seven themes</h2><p><span class="when">${d}</span>${t}</p><div class="th14">${THEMES.map(([f,nm])=>I(`th-${f}.webp`,420,262,`The ${nm} theme`,nm)).join('')}</div>`).join('')}`,true]),
  ],
  nba:[
    [`${head('2024 · partner project','NBA Prediction AI','A neural network that called the 2024 playoffs with only 2 mistakes.')}
      <div class="nba14" aria-hidden="true"><span class="nba14-k">Live predictor</span><div class="nba14-r"><span>Home team</span><i>▾</i></div><div class="nba14-r"><span>Away team</span><i>▾</i></div><b>Predict</b><small>The live predictor comes over in the real build. Data through May 2024.</small></div>
      <div class="chips"><span>PyTorch</span><span>TensorFlow</span><span>Data through May 2024</span></div>${L('Try the demo','View the repository')}`],
    [`<h2>How it works</h2><p>A partner project I worked on starting April 28th: a convolutional neural network trained on a custom-made data set of NBA stats. This model was built with PyTorch, and we also made a very similar version with TensorFlow.</p>
      <p>From our testing it's pretty good at predicting the win or loss, and as expected it has a bit of trouble with the exact point differential. It predicted the 2024 NBA Playoffs with high accuracy, making only 2 mistakes while predicting multiple upsets.</p>`],
  ],
  planner:[
    [`${head('2022 · class team','Digital Planner','A calendar and to-do list built with a four-person class team.')}
      <p>A web app four other people and I built for our Software Engineering course over just over two months, split into two sprints. It taught us to code as a team with GitHub, Trello and daily meetings. The "final" product wasn't close to done, but we were happy with it, and I think of it as a proof of concept.</p>`],
    [`<h2>End of sprint 1</h2><p class="when">November 1st 2022</p>
      <figure class="vid"><video src="img/14/dp-old.mp4" poster="img/14/dp-thumb.webp" width="720" height="406" muted loop playsinline controls preload="none"></video></figure>
      <p>I made assignments show up correctly when created, while a teammate built the add assignment menu. I also figured out and built drag and drop for assignments onto the calendar.</p>`],
    [`<h2>End of sprint 2</h2><p class="when">December 15th 2022</p>
      <figure class="vid"><video src="img/14/dp-new.mp4" poster="img/14/dp-new-poster.webp" width="720" height="402" muted loop playsinline controls preload="none"></video></figure>
      <p>Much more drag and drop: events alongside assignments, the calendar adjusting for different-length items without overlaps, calendar scrolling, and many smaller fixes.</p>`],
  ],
  programs:[
    [`${head('2021 to 2024','Programs','Software projects, experiments, and selected coursework.')}<h4>Coursework archive · 2024</h4>
      <div class="ar14">${ARCHIVE.slice(0,2).map(([y,list])=>`<div><span class="when">${y}</span><ul>${list.map(n=>`<li>${esc(n)}</li>`).join('')}</ul></div>`).join('')}</div>`],
    [`<h2>Earlier coursework</h2><div class="ar14">${ARCHIVE.slice(2).map(([y,list])=>`<div><span class="when">${y}</span><ul>${list.map(n=>`<li>${esc(n)}</li>`).join('')}</ul></div>`).join('')}</div>
      <figcaption>Most have their code or a demo on the live site.</figcaption>`],
  ],
  printing:[
    [`${head('Puzzles and models','3D printing','Here\'s some 3D models I\'ve designed and printed for fun.')}
      <p>I always wanted more puzzle boxes to have around. So I started making them. I bet you can't solve them. Drag any model to turn it.</p>
      <h4>Puzzles · 5</h4><div class="m14s">${M('My first puzzle box','45,000+ downloads','FirstPuzzle','FirstPuzzle_Open',['Printables','Thingiverse','MyMiniFactory','Cults'])}${M('The couch puzzle box','3,000+ downloads','CouchPuzzle','CouchPuzzle_Open',['Printables','Thingiverse','Cults'])}${M('The gift puzzle box','800+ downloads','GiftPuzzle','GiftPuzzle_Open',['Printables','Cults'])}${M('Simple block puzzle','600+ downloads','BlockPuzzle','BlockPuzzle_Solved',['Printables','Thingiverse','MyMiniFactory','Cults'],'Solve it')}${M('The sliding puzzle box','Private for now','SlidingPuzzle','SlidingPuzzle_Open',[])}</div>`,true],
    [`<h2>Other models</h2><p>Cases and organizers I needed, and a jewelry box. Drag any model to turn it.</p>
      <div class="m14s">${M('Galaxy S20 FE case','2,500+ downloads','S20FECase','',['Printables','Thingiverse','MyMiniFactory','Cults'])}${M('Pixel 3 case','300+ downloads','PixelCase','',['Thingiverse','Cults'])}${M('Tech accessory organizer','50+ downloads','ChargerOrganizer','',['Cults'])}${M('Jewelry box','Private for now','JewelryBox','JewelryBox_Open',[])}</div>`,true],
  ],
  gaming:[
    [`${head('Shorter games','Gaming','Check out some of my favorite video games! I\'ll race you in Mario Kart Wii.')}
      <p>When I have free time, video games are another thing I enjoy. I tend to like shorter games, so over the past few years I've cycled through a lot of them. Here's a list of games I've really enjoyed:</p>
      <div class="covers c17">${GAMES.slice(0,9).map(cover).join('')}</div>`],
    [`<h2>More favorites</h2><div class="covers c17">${GAMES.slice(9).map(cover).join('')}</div>`],
  ],
  work:[
    [`${head('Work · 8 roles','Work','From coaching tennis to building AI tools.')}<ul class="rows j14s">${JOBS.slice(0,2).map(job).join('')}</ul>`],
    [`<h2>Before Denali</h2><ul class="rows j14s">${JOBS.slice(2,5).map(job).join('')}</ul>`],
    [`<h2>Earlier</h2><ul class="rows j14s">${JOBS.slice(5).map(job).join('')}</ul>`],
  ],
  school:[
    [`${head('Class of 2025','College','CS degree, math minor, tennis team.')}
      ${I('e-upscampus.webp',800,449,'University of Puget Sound campus')}
      <p>As of May 2025 I hold a Bachelor of Science in Computer Science with a minor in Mathematics from the University of Puget Sound.</p>`],
    [`<h2>Classes taken</h2>${COURSES.map(([g,list])=>`<div class="cl14"><span class="when">${g} · ${list.length}</span><div class="chips">${list.map(c=>`<span>${esc(c)}</span>`).join('')}</div></div>`).join('')}`],
    [`<h2>Clubs and activities</h2>
      <div class="club14">${I('../ups-tennis.webp',710,326,'University of Puget Sound tennis')}<p><b>Tennis</b> I played all 4 years on the UPS tennis team, 2021 to 2025.</p></div>
      <div class="club14">${I('e-maroonsociety.webp',583,584,'Maroon Society logo','','sq')}<p><b>Maroon Society</b> A university organization that connects students and alumni, mostly through events around campus. I was a part of it for about 2 years, 2021 to 2024.</p></div>
      <h4>Agile management report</h4><p>A report from my 2024 management class on agile management strategies, why they work and why they might not.</p>${L('View the report')}`],
    [R14.BODY.early()],
  ],
};
const NAME={scribblescan:'ScribbleScan',site:'This website',nba:'NBA Prediction AI',planner:'Digital Planner',programs:'Programs',printing:'3D printing',gaming:'Gaming',work:'Work',school:'School'};
const LISTED=new Set(['scribblescan','site','nba','planner','programs','printing','gaming']);
const wrap=([h,sw],k,n,t)=>`<div class="x"${sw?' data-sw16="1"':''}>${k>1?cont(t,k,n):''}${h}</div>`;
const NEXT={site:'NBA Prediction AI',nba:'Digital Planner',planner:'Programs',programs:'Work',work:'School',school:'3D printing',printing:'Gaming',gaming:'Tennis'};
const endPage=(id,t)=>`<div class="x x17-end"><span>end of ${t}</span>${NEXT[id]?`<button type="button" class="x17-next">Next: ${NEXT[id]} <b aria-hidden="true">→</b></button>`:''}</div>`;
document.addEventListener('click',e=>{const b=e.target.closest('.x17-next');if(!b)return;e.stopPropagation();const r=b.closest('.device')||b.closest('.c14');const n=r&&r.querySelector('.nb-ear.next');n&&n.click()},true);
/* desktop: a spread is two of [contents list?, page 1, page 2, ...] */
function seqD(id,P,o){const ch=CH[id],t=NAME[id];const s=ch.map((c,i)=>wrap(c,i+1,ch.length,t));return LISTED.has(id)?[base(id,P,o)[0],...s]:s}
function order(){
  const ph=[],dk=[];
  for(const id of R2.lib.PH){ph.push(id);if(CH[id])for(let k=2;k<=CH[id].length;k++)ph.push(`${id}+${k}`)}
  for(const id of R2.lib.DK){dk.push(id);if(CH[id]){const n=Math.ceil(((LISTED.has(id)?1:0)+CH[id].length)/2);for(let k=2;k<=n;k++)dk.push(`${id}+${k}`)}}
  return {ph,dk};
}
function pages(id,P,o){
  const root=o.root;
  if(!root||!root.classList.contains('s17'))return prev(id,P,o);
  const [b,kS]=String(id).split('+'),k=+(kS||1);
  if(!CH[b])return base(id,P,o);
  if(b==='printing')base('printing',P,o); // loads the 3D viewer
  if(P)return [wrap(CH[b][k-1],k,CH[b].length,NAME[b])];
  const s=seqD(b,P,o);return [s[2*k-2],s[2*k-1]||endPage(b,NAME[b])];
}
window.C17={CH,NAME,LISTED};window.C14.pages=pages;window.C14.order=order;
})();
