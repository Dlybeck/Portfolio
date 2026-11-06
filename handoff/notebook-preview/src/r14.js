/* ================= ROUND 14: the contents ================= */
/* Every inside page checked against davidlybeck.com: what was cut comes back in your own words, with the site's photos,
   videos and 3D models, and the headers are plain section names. Only mounts with the c14 class use it. */
const R14=(()=>{
const {E,esc}=R2.lib;
const I=(f,w,h,alt,cap,cls='')=>`<figure class="${cls}"><img src="img/14/${f}" width="${w}" height="${h}" alt="${esc(alt)}" loading="lazy" decoding="async">${cap?`<figcaption>${cap}</figcaption>`:''}</figure>`;
// links on the live site; drawn as link chips here and wired up in the real build
const L=(...n)=>`<span class="lks">${n.map(x=>`<span class="lk">${esc(x)}</span>`).join('')}</span>`;
const head=(k,t,lead)=>`${k&&k!==t?`<div class="k">${k}</div>`:''}<h2>${t}</h2>${lead?`<p class="lead">${lead}</p>`:''}`;
const step=(when,f,w,h,alt,txt,more='')=>`<li><time>${when}</time>${f?I(f,w,h,alt,'','shot'):''}<p>${txt}</p>${more}</li>`;
// a 3D model you can turn; puzzles that open get a button that swaps in the open model
let mvAsked=false;
function askMV(){if(mvAsked||customElements.get('model-viewer'))return;mvAsked=true;const s=document.createElement('script');s.type='module';s.src='https://cdn.jsdelivr.net/npm/@google/model-viewer@3.5.0/dist/model-viewer.min.js';document.head.appendChild(s)}
const M=(name,dl,file,open,links,openWord='Open it')=>`<div class="m14"><div class="m14-v"><model-viewer src="img/14/m/${file}.json" data-a="img/14/m/${file}.json"${open?` data-b="img/14/m/${open}.json"`:''} alt="${esc(name)}, 3D model" camera-controls${reduce?'':' auto-rotate'} auto-rotate-delay="0" rotation-per-second="18deg" interaction-prompt="none" shadow-intensity=".8" exposure="1.05" loading="lazy" touch-action="pan-y"></model-viewer>${open?`<button type="button" class="m14-o" data-w="${openWord}">${openWord}</button>`:''}</div><div class="m14-t"><b>${esc(name)}</b><span>${dl}</span>${links.length?`<span class="m14-l">${links.join(' · ')}</span>`:''}</div></div>`;
const GAMES=[['Cyberpunk','Cyberpunk 2077'],['HighOnLife','High on Life'],['MKWii','Mario Kart Wii'],['Subnautica','Subnautica'],['SubnauticaBZ','Subnautica: Below Zero'],['EdithFinch','What Remains of Edith Finch'],['SoT','Sea of Thieves'],['Minecraft','Minecraft'],['NMS','No Man\'s Sky'],['Portal','Portal'],['Portal2','Portal 2'],['Trackmania','Trackmania'],['Valorant','Valorant'],['Apex','Apex Legends'],['Firewatch','Firewatch'],['OuterWilds','Outer Wilds'],['Titanfall','Titanfall'],['Titanfall2','Titanfall 2'],['road96','Road 96'],['ForeverSkies','Forever Skies']];
const JOBS=[
  ['denali',240,149,'Denali Advanced Integration','Innovation AI Developer','August 2025 to now','Building and deploying internal AI tools to make day-to-day work at Denali faster, including agents for workflow automation and helping individuals and teams across the company adopt AI in their own roles. Driving select external projects on edge and mobile AI and computer vision.'],
  ['scribblescan',240,45,'ScribbleScan LLC','Founder and developer','February 2025 to April 2026','I solo-developed a handwriting-digitization service that preserved images and other non-text elements in the resulting document. The company and original service have since closed, and a preserved demo remains.'],
  ['2ndchair',240,99,'2nd Chair','Software engineering intern','June to September 2024','Developed and researched software to improve AI document parsing, relevance and accuracy.'],
  ['tech',240,102,'University of Puget Sound','Technology Services Assistant II','August 2022 to May 2025','Answered phone calls and tickets from faculty, staff and incoming students about a range of technology issues, then either resolved them or routed them to the right team.'],
  ['tcgc',225,225,'Tacoma Country and Golf Club','Tennis instructor','July to August 2023','Coached group lessons for children ages 6 to 15 with a range of abilities, along with private lessons for players of all ages.'],
  ['gtc',240,240,'Galbraith Tennis Center','On court associate','July to August 2023','Coached group lessons for adults and children ages 5 to 18 with a range of abilities.'],
  ['ptc',240,117,'Portland Tennis Center','Assistant coach','June 2022 to January 2023','Helped coach group lessons for children ages 4 to 18 with a wide range of abilities.'],
  ['tech',240,102,'University of Puget Sound','Technology Services Assistant I','January to May 2022','Answered calls from faculty, staff and incoming students about technology issues, then either resolved them or routed them to the right team.'],
];
const job=j=>`<li class="j14"><span class="j14-l"><img src="img/14/w-${j[0]}.webp" width="${j[1]}" height="${j[2]}" alt="${esc(j[3])} logo" loading="lazy" decoding="async"></span><span class="j14-t"><span class="when">${j[5]}</span><b>${j[4]}</b><small>${j[3]}</small><span class="j14-s">${j[6]}</span></span></li>`;
const work=(a,b,title)=>`${title?head(`Work · ${JOBS.length} roles`,'Work','From coaching tennis to building AI tools.'):''}<ul class="rows j14s">${JOBS.slice(a,b).map(job).join('')}</ul>`;
const COURSES=[['Computer science',['Intro to Computer Science','Computer Science II','Software Engineering','Assembly Language and Computer Architecture','Programming Language Paradigms','Network Programming','Algorithms and Data Structures','Intro to Artificial Intelligence','Operating Systems','Principles of Database Systems','Cryptography and Network Security','Capstone in Computer Science']],
  ['Math',['Calculus 1','Calculus 2','Intro to Statistics','Discrete Math','Linear Algebra']],
  ['Business',['Principles of Management','Law and Ethics in Business']],
  ['Other',['Intermediate Spanish','Scientific Controversies','Medical Narratives','Markets and Macroeconomics','Astronomy','Intro to Anthropology','Modeling Earth\'s Climate','Survey of Western Music','Ancient Greek Philosophy']]];
const ARCHIVE=[['2024 · Python',['Negamax Connect 4 bot','A* sliding puzzle solver','Representative voting history by K-Means','CNN cat vs dog detector','Representative voting history by decision tree']],
  ['2024 · C',['Parallel matrix multiplication','Mini shell','ls command recreation','Hash map','Heap sort']],
  ['2023 · Java',['Red-black tree binary search','Digraph and topological sort for strings','Priority queue']],
  ['2023 · Haskell',['Evil Hangman']],['2023 · Prolog',['Mass Covid test process']],
  ['2022 · Java',['Selection sort','Quick sort','Insertion sort','Heap sort']],['2021 · Java',['Bubble sort','Bitwise to hash']]];
const VERS=[
  ['Version 1','December 2022 to June 2023','v1',[[1,444,'December 23rd 2022','This is what I considered to be the first base model of my website. None of the buttons worked. I was just trying to test out the rough idea and color scheme for how it should look.'],
    [2,450,'January 5th 2023','At this point I had added working buttons and transitions between pages, as well as a new background image to see the scrolling from the transition effect.'],
    [3,450,'January 6th 2023','For this change I had simply settled on a new background image to use throughout the website.'],
    [4,450,'January 10th 2023','I wanted my website to have something unique that stood out from other websites. So I decided to mess with the standard of menus and try this "radial" navigation menu that changes page to page.'],
    [5,450,'January 12th 2023','Here I had finalized the placement of the menu and menu button (currently a checkbox).'],
    [6,449,'January 13th 2023','I added the animated menu button along with the old home button, and moved the page links into the new menu and made it functional.'],
    [7,451,'June 13th 2023','My first functional version of the map idea. Testing with friends and family, the new menu proved a bit confusing. With the rough map, people understood that the menu was "taking them somewhere", and the map subtly encouraged them to explore the entire website.'],
    [8,450,'June 18th 2023','Close to the final version of the map and menu. I moved the map to the center of the menu to save space, moved the home button to the top so it\'s always visible, and added a "current location" marker and names for every discovered location.']]],
  ['Version 2','January 2025','v2',[[1,428,'January 4th 2025','Two big changes in mind. 1: Removing the previous map. It was big, slow, and broke the mobile experience. 2: Keep the feeling of exploring the website like it is a place. So instead of a large map taking up half the page, I made the map the website!'],
    [2,427,'January 5th 2025','The navbar size is drastically reduced, to make the blue less overwhelming and give tiles more space on mobile. The home button became a house shape.'],
    [3,428,'January 6th 2025','I changed the background from white paper to sand, for a bit more depth without overwhelming the tiles. The home button moved into the navbar and hides when you are already home.'],
    [4,427,'January 8th 2025','This is when links were added. The url now changes depending on the tiles viewed, so people can jump straight to what they want to see.'],
    [5,428,'January 10th 2025','The mini windows got their full functionality, opening and closing seamlessly. They load a separate page and just change based on the tile clicked.'],
    [6,428,'January 11th 2025','Very close to the finished v2: a back button to navigate the mini windows, and cleaned up versions of all the pages.']]],
  ['Version 3','April to September 2026','v3',[[1,500,'April 22nd 2026','v3 threw out the tile grid and replaced it with a wall of handwritten notes pinned to a wood tabletop. Every tile is its own paper scrap, so the wall reads as a real, hand-built collection instead of a generated UI.'],
    [2,500,'April 23rd 2026','Opening a tile slides a cream paper in from the side. The close button turns into a back button when you\'ve gone deeper, and tapping outside the paper closes it: one contextual button, no menu hamburger.'],
    [3,500,'April 25th 2026','The cream paper now slides up to close, like lifting it off the table, runs larger on desktop, and gets pushed down on mobile so the navbar and close button don\'t overlap it.'],
    [0,0,'September 8th 2026','I kept the same map and rebuilt its visual layer into seven switchable worlds. The difficult part was not adding skins; it was preserving the same navigation, direct links, keyboard behavior and document flow across every theme.']]],
];
const THEMES=[['original','Original'],['clouds','Clouds'],['islands','Islands'],['lily-pads','Lily pads'],['planets','Planets'],['postcards','Postcards'],['vinyl','Vinyl']];
const BODY={
  scribblescan:()=>`${head('2025 to now','ScribbleScan','Handwriting digitization, from a hosted product to an offline, privacy-first experiment.')}
    ${I('ss-jul1.webp',900,489,'ScribbleScan web app showing a digitized handwritten page','The finished hosted version, July 2025')}
    <p>ScribbleScan began as my 2025 capstone, grew into a hosted handwriting-digitization service and LLC, and is now preserved as a demo. It digitized handwritten pages while keeping images and other non-text elements in the resulting document.</p>
    ${L('View the preserved demo')}
    <h4>Character accuracy, five sample pages</h4>
    <div class="bars"><div class="bar me"><span>ScribbleScan</span><i style="width:95.10%"></i><b>95.10%</b></div><div class="bar"><span>Pen to Print AI</span><i style="width:83.46%"></i><b>83.46%</b></div><div class="bar"><span>Baseline OCR</span><i style="width:74.39%"></i><b>74.39%</b></div></div>
    <figcaption>A small project comparison, not a general benchmark.</figcaption>
    <h4>What I'm exploring now</h4>
    <p>I'm rebuilding the idea around an offline, privacy-first mobile reader: on-device transcription, preserving non-text visuals as source crops, and local correction, history and export. It is active R&amp;D, not a finished product.</p>
    <h4>How it grew</h4>
    <ul class="tl tl14">
      ${step('January 2025 · proposal','',0,0,'','The initial proposal I submitted for my capstone. It\'s interesting to see what I stuck with (like the export options) and what I changed (target audience, some features).',L('Read the proposal'))}
      ${step('February 7th 2025','ss-feb7.webp',900,489,'First working version of ScribbleScan','The first working version. The results split each line into a section and showed them line by line. Rough, but it matched the design I had in mind, and I was very happy with it at the time.')}
      ${step('February 8th 2025','ss-feb8.webp',900,488,'ScribbleScan a day later with larger tiles','Only a day later, but big UI improvements: much larger tiles, and the digitize button hides once clicked. That stayed in every later version.')}
      ${step('March 12th 2025','ss-mar12.webp',900,489,'ScribbleScan with export and corrections','A month after the proof of concept: PDF export, copy to clipboard, corrections and accuracy scores. The focus shifted from a demo to a usable tool.')}
      ${step('April 28th 2025','ss-apr28.webp',900,489,'ScribbleScan as presented for the capstone','The version I presented for my capstone: a batch page limit, Google sign-in and a toned down UI. Not a full product, but a finished tool.')}
      ${step('June 25th 2025','ss-jun25.webp',900,489,'ScribbleScan as a hosted product','After graduating, ScribbleScan LLC full time: profiles and support, a cloud-hosted database, paid tiers and many smaller features. A complete product.')}
      ${step('July 1st 2025','ss-jul1.webp',900,489,'ScribbleScan with demo mode','A week later I called it finished. The big addition was a demo mode, so anyone could try pre-calculated pages of tough handwriting without costing the service.')}
    </ul>`,
  site:()=>`${head('2022 to now','This website','You\'re looking at it! Four versions so far, and how each was made.')}
    <ul class="tl"><li><time>Dec 2022 · v1</time>A hand-coded static layout that grew into an exploratory map.</li><li><time>Jan 2025 · v2</time>The map became the website, so you explore pages without opening them.</li><li><time>Apr 2026 · v3</time>Handwritten notes pinned to a tabletop, then seven visual themes.</li><li><time>Nov 2026 · v4</time>This one, rebuilt on my own design system.</li></ul>
    ${VERS.map(([n,when,v,steps],i)=>`<details class="v14"${i===2?' open':''}><summary><b>${n}</b><span>${when} · ${steps.length} snapshots</span></summary><ul class="tl tl14">${steps.map(([k,h,d,t])=>step(d,k?`${v}-${k}.webp`:'',800,h,`${n}, ${d}`,t)).join('')}</ul>${v==='v3'?`<div class="th14">${THEMES.map(([f,n])=>I(`th-${f}.webp`,420,262,`The ${n} theme`,n)).join('')}</div>`:''}</details>`).join('')}`,
  nba:()=>`${head('2024 · partner project','NBA Prediction AI','A neural network that called the 2024 playoffs with only 2 mistakes.')}
    <div class="nba14" aria-hidden="true"><span class="nba14-k">Live predictor</span><div class="nba14-r"><span>Home team</span><i>▾</i></div><div class="nba14-r"><span>Away team</span><i>▾</i></div><b>Predict</b><small>The live predictor comes over in the real build. Data through May 2024.</small></div>
    <p>A partner project I worked on starting April 28th: a convolutional neural network trained on a custom-made data set of NBA stats. This model was built with PyTorch, and we also made a very similar version with TensorFlow.</p>
    <p>From our testing it's pretty good at predicting the win or loss, and as expected it has a bit of trouble with the exact point differential. It predicted the 2024 NBA Playoffs with high accuracy, making only 2 mistakes while predicting multiple upsets.</p>
    <div class="chips"><span>PyTorch</span><span>TensorFlow</span><span>Data through May 2024</span></div>${L('Try the demo','View the repository')}`,
  planner:()=>`${head('2022 · class team','Digital Planner','A calendar and to-do list built with a four-person class team.')}
    <p>A web app four other people and I built for our Software Engineering course over just over two months, split into two sprints. It taught us to code as a team with GitHub, Trello and daily meetings. The "final" product wasn't close to done, but we were happy with it, and I think of it as a proof of concept.</p>
    <h4>End of sprint 1 · November 1st 2022</h4>
    <figure class="vid"><video src="img/14/dp-old.mp4" poster="img/14/dp-thumb.webp" width="720" height="406" muted loop playsinline controls preload="none"></video></figure>
    <p>I made assignments show up correctly when created, while a teammate built the add assignment menu. I also figured out and built drag and drop for assignments onto the calendar.</p>
    <h4>End of sprint 2 · December 15th 2022</h4>
    <figure class="vid"><video src="img/14/dp-new.mp4" poster="img/14/dp-new-poster.webp" width="720" height="402" muted loop playsinline controls preload="none"></video></figure>
    <p>Much more drag and drop: events alongside assignments, the calendar adjusting for different-length items without overlaps, calendar scrolling, and many smaller fixes.</p>`,
  programs:()=>`${head('2021 to 2024','Programs','Software projects, experiments, and selected coursework.')}
    <h4>Coursework archive</h4>
    <div class="ar14">${ARCHIVE.map(([y,list])=>`<div><span class="when">${y}</span><ul>${list.map(n=>`<li>${esc(n)}</li>`).join('')}</ul></div>`).join('')}</div>
    <figcaption>Most have their code or a demo on the live site.</figcaption>`,
  printing:()=>`${head('Puzzles and models','3D printing','Here\'s some 3D models I\'ve designed and printed for fun.')}
    <p>I always wanted more puzzle boxes to have around. So I started making them. I bet you can't solve them. Drag any model to turn it.</p>
    <h4>Puzzles</h4>
    <div class="m14s">${M('My first puzzle box','45,000+ downloads','FirstPuzzle','FirstPuzzle_Open',['Printables','Thingiverse','MyMiniFactory','Cults'])}${M('The couch puzzle box','3,000+ downloads','CouchPuzzle','CouchPuzzle_Open',['Printables','Thingiverse','Cults'])}${M('The gift puzzle box','800+ downloads','GiftPuzzle','GiftPuzzle_Open',['Printables','Cults'])}${M('Simple block puzzle','600+ downloads','BlockPuzzle','BlockPuzzle_Solved',['Printables','Thingiverse','MyMiniFactory','Cults'],'Solve it')}${M('The sliding puzzle box','Private for now','SlidingPuzzle','SlidingPuzzle_Open',[])}</div>
    <h4>Other models</h4>
    <div class="m14s">${M('Galaxy S20 FE case','2,500+ downloads','S20FECase','',['Printables','Thingiverse','MyMiniFactory','Cults'])}${M('Pixel 3 case','300+ downloads','PixelCase','',['Thingiverse','Cults'])}${M('Tech accessory organizer','50+ downloads','ChargerOrganizer','',['Cults'])}${M('Jewelry box','Private for now','JewelryBox','JewelryBox_Open',[])}</div>`,
  gaming:()=>`${head('Shorter games','Gaming','Check out some of my favorite video games! I\'ll race you in Mario Kart Wii.')}
    <p>When I have free time, video games are another thing I enjoy. I tend to like shorter games, so over the past few years I've cycled through a lot of them. Here's a list of games I've really enjoyed:</p>
    <div class="covers c14g">${GAMES.map(([f,a])=>`<img src="img/14/g-${f.toLowerCase()}.webp" width="260" height="390" alt="${esc(a)} cover art" title="${esc(a)}" loading="lazy" decoding="async">`).join('')}</div>`,
  tennis:()=>`${head('Since middle school','Tennis','I\'ve played for as long as I remember. Let me know if you want to hit.')}
    <div class="pair14">${I('spin.webp',800,1327,'David putting spin on a tennis ball')}${I('../forehand.webp',723,484,'David hitting a forehand')}</div>
    <p>I've played competitively since middle school: four years on my high school's varsity team, four more on the University of Puget Sound team. Still hitting whenever I can.</p>
    <h4>Current rankings and profiles</h4>${L('Puget Sound tennis profile','World Tennis Number','Universal Tennis Rating')}`,
  college:()=>`${head('Class of 2025','College','CS degree, math minor, tennis team.')}
    ${I('e-upscampus.webp',800,449,'University of Puget Sound campus')}
    <p>As of May 2025 I hold a Bachelor of Science in Computer Science with a minor in Mathematics from the University of Puget Sound.</p>
    <h4>Classes taken</h4>
    ${COURSES.map(([g,list])=>`<div class="cl14"><span class="when">${g} · ${list.length}</span><div class="chips">${list.map(c=>`<span>${esc(c)}</span>`).join('')}</div></div>`).join('')}
    <p class="ag14"><b>Agile management report</b> A report from my 2024 management class on agile management strategies, why they work and why they might not.</p>${L('View the report')}
    <h4>Clubs and activities</h4>
    <div class="club14">${I('../ups-tennis.webp',710,326,'University of Puget Sound tennis')}<p><b>Tennis</b> I played all 4 years on the UPS tennis team, 2021 to 2025.</p></div>
    <div class="club14">${I('e-maroonsociety.webp',583,584,'Maroon Society logo','','sq')}<p><b>Maroon Society</b> A university organization that connects students and alumni, mostly through events around campus. I was a part of it for about 2 years, 2021 to 2024.</p></div>`,
  early:()=>`${head('Portland','Early education','Where it all started.')}
    <div class="sch14">${[['ghs',336,'Grant High School','High school'],['bms',451,'Beaumont Middle School','Middle school'],['aes',533,'Alameda Elementary School','Elementary']].map(([f,h,n,k])=>`<figure><img src="img/14/e-${f}.webp" width="800" height="${h}" alt="${n}" loading="lazy" decoding="async"><figcaption><span class="when">${k}</span>${n}</figcaption></figure>`).join('')}</div>`,
};
const detail=id=>`<div class="x">${BODY[id]()}</div>`;
const wrap=h=>`<div class="x">${h}</div>`;
const aboutHTML=(logo,LOGO)=>`<div class="me-row">${logo?`<img alt="" src="${LOGO}">`:''}<div><div class="k">Hi, I'm David</div><h1>David Lybeck</h1></div></div>
  <p class="lead">I build AI tools at Denali, and on my own time I make things like ScribbleScan, puzzle boxes and this website.</p>
  <ul class="facts"><li><span>Now</span><div>Innovation AI Developer at Denali</div></li><li><span>Studied</span><div>Computer science, University of Puget Sound, 2025</div></li><li><span>Made</span><div>ScribbleScan, from capstone to company</div></li><li><span>Plays</span><div>Tennis, since middle school</div></li></ul>`;
const say=()=>`${head('Say hi','Say hi','')}<div class="contact"><div><b>GitHub</b><span>github.com/Dlybeck</span></div><div><b>Email</b><span class="todo">to add</span></div><div><b>LinkedIn</b><span class="todo">to add</span></div><div><b>Resume</b><span class="todo">new copy to add</span></div></div>`;
const LEAD={projects:'Personal projects I\'ve developed, and how they were made.',hobbies:'All my favorites! (Coding gets its own section.)',school:'Schools I\'ve gone to and classes I\'ve taken.'};
const LISTS={projects:['scribblescan','site','nba','planner','programs'],hobbies:['printing','gaming','tennis'],school:['college','early']};
function pages(id,P,{toc,hint,LOGO}){
  const list=(sec,cur)=>`<div class="k">${LISTS[sec].length} entries</div><h2>${{projects:'Projects',hobbies:'Hobbies',school:'School'}[sec]}</h2><p>${LEAD[sec]}</p>${toc(LISTS[sec],cur)}`;
  const contents=()=>`<h2>Contents</h2>${toc(['projects','work','school','hobbies','say'])}<span class="hn">${hint}</span>`;
  const schoolBoth=()=>`<h2>School</h2><p>${LEAD.school}</p>${BODY.college().replace(/<div class="k">.*?<\/p>/s,'<h4>College · class of 2025</h4>')}${BODY.early().replace(/<div class="k">.*?<\/p>/s,'<h4>Early education · where it all started</h4>')}`;
  if(id==='printing')askMV();
  if(P){
    if(id==='me')return [wrap(aboutHTML(true,LOGO))];
    if(id==='toc')return [wrap(contents())];
    if(id==='projects'||id==='hobbies')return [wrap(list(id))];
    if(id==='work')return [wrap(work(0,JOBS.length,true))];
    if(id==='school')return [wrap(schoolBoth())];
    if(id==='say')return [wrap(say())];
    return [detail(id)];
  }
  if(id==='me')return [wrap(aboutHTML(true,LOGO)),wrap(contents())];
  if(id==='work')return [wrap(work(0,4,true)),wrap(`<h4>Earlier</h4>`+work(4,JOBS.length,false))];
  if(id==='school')return [detail('college'),detail('early')];
  if(id==='say')return [wrap(say()),wrap(`<div class="k">About this notebook</div><h2>How it's made</h2><p>Drawn with dlybeck design, my own design system. The pages that turn are the whole interface.</p>`)];
  const s=E[id].sec;return [wrap(list(s,id)),detail(id)];
}
// open or close a puzzle; works on any page, including the copies on a turning leaf
document.addEventListener('click',e=>{const b=e.target.closest('.m14-o');if(!b)return;const mv=b.parentElement.querySelector('model-viewer');if(!mv)return;
  const open=mv.getAttribute('src')===mv.dataset.a;mv.setAttribute('src',open?mv.dataset.b:mv.dataset.a);b.textContent=open?'Close it':b.dataset.w;b.classList.toggle('on',open)});
window.C14={pages};
return {BODY,pages,M,JOBS,job,I,L,head,step,VERS,THEMES,COURSES,ARCHIVE,GAMES};
})();
