/* ---------- preview shell ---------- */
const ROUNDS={
  r17:{intro:'Round 17: from your note on the flowing pages. One longer page that scrolls is better, so each story is back on a single page: ScribbleScan, This website, Work, School and the rest each scroll top to bottom, with the same big pictures and short sections as round 16, split by a light rule instead of a page turn. Swipe stays only on the real rows of pictures: the snapshots of each version of this website, its seven themes, and the 3D models. On desktop the contents list stays on the left and the whole story scrolls on the right. The notebook is back to its normal length, so the wheel is roomy again. Every word and picture is the same.',
    covers:true,typists:false,pickCover:'kraft',
    dirs:[
      {id:'lp',num:'ONE PAGE PER STORY',name:'Each story scrolls on one page',line:'Big pictures and short sections; swipe only for site snapshots, themes and 3D models.',m:R7.make('cover13a','tr-worn tr-vinyl tr-r9 in-worn in-r12 in-r13 c14 s15b s16 s18'),
        why:['your call','You said one longer page beats flowing over several, and scrolling is fine. The roomy pictures and sections from round 16 stay; only the page turns between them are gone.']},
      {id:'fl2',num:'BEFORE',name:'Round 16, flowing pages',line:'Stories carry on over the next pages, to compare.',m:R7.make('cover13a','tr-worn tr-vinyl tr-r9 in-worn in-r12 in-r13 c14 s15b s16 s17'),
        why:['to compare','Round 16 as it was.']},
    ]},
  r16:{intro:'Round 16: from your notes on round 15. The swipe felt awkward in places, so it is gone except where a page is a real row of like things: the snapshots of each version of this website with its seven themes, and the 3D models. The tap-to-open shortcut felt forced, so it is gone too. Instead a long story simply carries on over the next pages of the notebook, a few big pictures at a time: ScribbleScan runs five pages, This website four, Work and School three or four, the rest two or three. Every word and picture from round 14 is still here. The notebook is longer (32 pages on a phone), so the wheel ticks sit closer together. Turn pages with the wheel, a swipe on the page, or the corners.',
    covers:true,typists:false,pickCover:'kraft',
    dirs:[
      {id:'fl',num:'FLOWING PAGES',name:'Stories carry on over the next pages',line:'No shortcut; swipe only for site snapshots, themes and 3D models.',m:R7.make('cover13a','tr-worn tr-vinyl tr-r9 in-worn in-r12 in-r13 c14 s15b s16 s17'),
        why:['the pick','A notebook already has a way to show more: the next page. Each page gets a few big pictures and a short stretch of text, and the story keeps going when you turn.']},
      {id:'b14',num:'BEFORE',name:'Round 14',line:'Everything on one long page per entry, to compare.',m:R7.make('cover13a','tr-worn tr-vinyl tr-r9 in-worn in-r12 in-r13 c14'),
        why:['to compare','Round 14 as it was.']},
    ]},
  r15:{intro:'Round 15: you liked the contents but some pages felt crowded, with tiny pictures and lots of text. Two ways to give them room, with the same content. Take A turns every long list into big cards you swipe through one at a time. Take B (my pick) keeps each page short: one big picture, the headline facts, and a button that opens the whole story on a full paper over the notebook. Both give the phone page back the strip the old bookmark band used to take. Before is round 14, to compare. Try ScribbleScan, This website, Work and 3D printing: they changed the most.',
    covers:true,typists:false,pickCover:'kraft',
    dirs:[
      {id:'sb',num:'TAKE B · MY PICK',name:'Short pages, tap for the story',line:'One big picture and the key facts per page; the full story opens on a bigger paper.',m:R7.make('cover13a','tr-worn tr-vinyl tr-r9 in-worn in-r12 in-r13 c14 s15b'),
        why:['my pick','The page stays calm and the pictures get big. Nothing is cut: every word and photo from round 14 is one tap away, and the paper it opens on is the whole notebook wide on desktop.']},
      {id:'sa',num:'TAKE A',name:'Swipe cards',line:'Long lists become big cards you swipe through one at a time.',m:R7.make('cover13a','tr-worn tr-vinyl tr-r9 in-worn in-r12 in-r13 c14 s15a'),
        why:['to compare','Everything stays on the page, but one card at a time, so each picture gets the full width. Swipe on a phone, arrows on desktop.']},
      {id:'s14',num:'BEFORE',name:'Round 14',line:'The full pages from round 14.',m:R7.make('cover13a','tr-worn tr-vinyl tr-r9 in-worn in-r12 in-r13 c14'),
        why:['to compare','Round 14 as it was.']},
    ]},
  r14:{intro:'Round 14: the pages inside. I went through every page of davidlybeck.com and put back what the notebook had dropped, in your own words: all eight jobs with their logos, every class, all twenty games, the full ScribbleScan story, the three earlier versions of the site, and the rankings links. The photos, the planner videos and the 3D puzzle models you can turn come over too. The headers are plain section names now. The cover is take A, your pick. Links show as link chips here and get wired up in the real build.',
    covers:true,typists:false,pickCover:'kraft',
    dirs:[
      {id:'ca',num:'NEW CONTENTS',name:'Everything from your site',line:'Every page filled back in, with photos, videos and 3D models, and plain headers.',m:R7.make('cover13a','tr-worn tr-vinyl tr-r9 in-worn in-r12 in-r13 c14'),
        why:['the pick','Your current site has a lot more on it than the notebook carried. Nothing here is new writing: it is your site\'s words, a little tightened in a few long spots.']},
      {id:'cb',num:'BEFORE',name:'Round 13 contents',line:'The shorter pages from round 13, to compare.',m:R7.make('cover13a','tr-worn tr-vinyl tr-r9 in-worn in-r12 in-r13'),
        why:['to compare','The same notebook with the round 13 pages.']},
    ]},
  r13:{intro:'Round 13: from your round 12 review. The printer keeps take A with no words on it; take B is gone. Tap the name tag and it wipes your name and writes it again in another hand, five in all. You weren\'t sure about TENNIS next to the ball, so here are both ways: take A drops TENNIS and lets the ball stand for tennis (my pick, the cover gets a little more room), take B switches it for a racket that asks "let\'s hit?", the line from your Say hi page. Inside is still the worn notebook.',
    covers:true,typists:false,pickCover:'kraft',
    dirs:[
      {id:'ta',num:'TAKE A · MY PICK',name:'No TENNIS',line:'The ball stands for tennis on its own; the raccoon moves up and the ball sits beside ScribbleScan.',m:R7.make('cover13a','tr-worn tr-vinyl tr-r9 in-worn in-r12 in-r13'),
        why:['my pick','Two tennis stickers said the same thing twice. The ball was one of your first favorites, and dropping the word gives the cover more room.']},
      {id:'tb',num:'TAKE B',name:'Racket: let\'s hit?',line:'A racket and a ball with the line from your Say hi page. Tap to swing.',m:R7.make('cover13b','tr-worn tr-vinyl tr-r9 in-worn in-r12 in-r13'),
        why:['switched up','Keeps tennis loud on the cover but says something new: an invitation instead of a label.']},
    ]},
  r12:{intro:'Round 12: from your round 10 cover review. You cut the octopus, so the raccoon takes its spot and your own sticker moves up. The now sticker\'s lines are shorter so every one fits. You asked "3d?" of the printer, so it comes in two takes that say 3D plainly: a printer you can tell is one, or just the printed piece. Inside is the worn notebook, my pick from round 11.',
    covers:true,typists:false,pickCover:'kraft',
    dirs:[
      {id:'pa',num:'TAKE A · MY PICK',name:'3D printer',line:'A printer with its frame, spool and nozzle, printing the logo in layers. Tap to print again.',m:R7.make('cover12a','tr-worn tr-vinyl tr-r9 in-worn in-r12'),
        why:['my pick','It keeps the printing you can watch, and the spool and rails make it read as a 3D printer at a glance.']},
      {id:'pb',num:'TAKE B',name:'3D printed piece',line:'Just the logo as a thick printed tile with layer lines. Tap to turn it.',m:R7.make('cover12b','tr-worn tr-vinyl tr-r9 in-worn in-r12'),
        why:['simpler','Shows what you made rather than the machine. Quieter, and smaller on the cover.']},
    ]},
  r11:{intro:'Round 11: the pages inside. The cover is settled, so these are three ways to carry it in. The words on every page stay as they are; only the paper, the labels, the photos and the band change, and a few of the cover stickers are stuck on the page they belong to (the trail on About, the octopus on ScribbleScan, the raccoon on Work, the puzzle on 3D printing, the ball on Tennis, the name tag on Say hi). Open the book and turn the pages. I picked the worn notebook: it is the same notebook as the cover from the outside in, keeps the paper light, and makes the stickers read as stickers on a page. Scrapbook and clean are one tap away.',
    covers:true,typists:false,pickCover:'kraft',
    dirs:[
      {id:'worn',num:'LOOK 1 · MY PICK',name:'Worn notebook',line:'Ruled paper with a red margin, the cover\'s dark band, cream label plates, a pen underline, photo corners.',m:R7.make('cover10','tr-worn tr-vinyl tr-r9 in-worn'),
        why:['closest to the cover','It reads like the same notebook from the outside in: the label plate from the cover becomes every page\'s label, and the dark elastic band carries through.']},
      {id:'scrap',num:'LOOK 2',name:'Scrapbook',line:'Dot paper, washi tape labels, highlighter headings, taped photos with handwritten captions.',m:R7.make('cover10','tr-worn tr-vinyl tr-r9 in-scrap'),
        why:['the most playful','Leans into the stickers: tape, highlighter and taped photos make each page feel collected, like the cover.']},
      {id:'clean',num:'LOOK 3',name:'Clean',line:'Plain warm paper, a kraft band like the cover color, the stickers as the only flourish.',m:R7.make('cover10','tr-worn tr-vinyl tr-r9 in-clean'),
        why:['the easiest to read','The cover does the talking; inside stays quiet and readable, with one sticker per page as the link back to it.']},
    ]},
  r10:{intro:'Round 10: the cover, settled. You kept all eleven round 9 stickers and picked the still name tag, so this is that one cover. I picked kraft for the color, the palest of the three, since light reads better to you; midnight and forest are below to compare.',
    covers:true,typists:false,pickCover:'kraft',
    dirs:[
      {id:'cover10',num:'THE COVER',name:'Everything you kept',line:'All eleven stickers, the still name tag, vinyl stickers on the worn notebook.',m:R7.make('cover10','tr-worn tr-vinyl tr-r9'),
        why:['the one you settled on','Throw the ball, slide the puzzle, write on ScribbleScan, tap the octopus or raccoon, and tap the round spot to make your own sticker. Turn the wheel or tap open to go inside.']},
    ]},
  r9:{intro:'Round 9: built from your sticker review. Cuts are gone; the trail lost its words, TENNIS lost the middle school line, the name tag writes itself in marker instead of cycling, the ball spins, the puzzle has a dark slot, ScribbleScan shows plain typed text under the lines with no character, the octopus and raccoon are stickers of their own, and the empty spot lets you draw a sticker or add a picture. Treatment: vinyl stickers on the worn notebook.',
    covers:true,typists:false,
    dirs:[
      {id:'kept',num:'SET 1',name:'Everything you kept',line:'Eleven: your favorites, plus now, the printer, TENNIS, the raccoon and your own sticker.',m:R7.make('kept','tr-worn tr-vinyl tr-r9'),
        why:['every keep, on one cover','Tap the name tag and it writes your name again. Throw the ball and watch it spin. Tap the octopus or raccoon to say hi. Tap the round spot to draw your own sticker or add a picture.']},
      {id:'fav9',num:'SET 2',name:'Just the favorites',line:'Seven: name, the trail, ScribbleScan, the octopus, the puzzle, the ball and your own sticker.',m:R7.make('fav9','tr-worn tr-vinyl tr-r9'),
        why:['fewer, bigger','The five you named, plus your name and the spot for your own sticker, with more cover showing.']},
    ]},
  r8:{intro:'Round 8: making them feel like stickers. Your favorites, ScribbleScan, the puzzle, the tennis ball and the trail climb to sunset, plus your name and AI, in three treatments. Mix any treatment with any cover, typist and ScribbleScan look below.',
    covers:true,pads:true,
    dirs:[
      {id:'vinyl',num:'TREATMENT A',name:'Vinyl',line:'A white die-cut edge that follows each shape, a soft lifted shadow, a gloss sweep, the name tag peeling at one corner, a little overlap.',m:R7.make('fav','tr-vinyl'),
        why:['real vinyl stickers','The edge, the shine and the lifted corner are what make a sticker read as a sticker.']},
      {id:'worn',num:'TREATMENT B',name:'Worn notebook',line:'The cover gets a cloth spine, scuffed corners, an elastic band and a label; the stickers go matte, like they have been there a while.',m:R7.make('fav','tr-worn'),
        why:['a notebook first','Most of the change is in the cover, so it reads as a notebook you carry around.']},
      {id:'bomb',num:'TREATMENT C',name:'Sticker bomb',line:'Everything piled up in one layered cluster with thick white edges, the rest of the cover plain with a label.',m:R7.make('fav','tr-bomb'),
        why:['the most overlap','Like the corner of a well-loved laptop: stickers on stickers.']},
    ]},
  r7:{intro:'Round 7: the live stickers, now with a way back. Scroll or spin the wheel back past page 1 and the book closes onto its cover; the logo at the top does it too. Pick a sticker set above, then a cover and a typist below, in any mix. The typist sits on the ScribbleScan pad and types out what it reads.',
    covers:true,
    dirs:[
      {id:'five',num:'SET 1',name:'Five stickers',line:'Name, AI, ScribbleScan, the puzzle box and a tennis ball. Calm, lots of cover.',m:R7.five,
        why:['the fewest, each one bigger','Who you are, what you do now, what you built, what you make and what you play.']},
      {id:'eight',num:'SET 2',name:'Eight stickers',line:'Adds the NBA model, a trail stamp and the 3D printer.',m:R7.eight,
        why:['the middle ground','Every project and hobby gets a sticker, with room to breathe.']},
      {id:'packed',num:'SET 3',name:'Thirteen, packed',line:'The round 6 set, edge to edge, on a notebook cover.',m:R7.packed,
        why:['the most to play with','Everything from round 6, including the Tacoma card, the campfire and an empty spot for a sticker you pick.']},
    ]},
  r6:{intro:'Round 6: the sticker cover, made live. The notebook keeps a true notebook shape on every screen, and every sticker does something tied to your pages. Play with the stickers; tap the empty cover, swipe it, tick a line on the planner or turn the wheel to open it.',
    dirs:[
      {id:'lid',num:'OPTION A',name:'Laptop lid',line:'Your laptop lid as a matched set: paired stickers, mirrored around the middle.',m:R6.lid,
        why:['made from your laptop stickers and your top 5','One palette, pairs tilted toward each other. Tap the trail stamp for a hike to sunset, the Tacoma card for night, the AI and basketball badges for a line from your pages, the slug to say hi. Throw the ball, slide the puzzle, write on ScribbleScan, stoke the fire. The dashed circle is a spot for a sticker you pick. All new art, no school logos.']},
      {id:'stickers',num:'OPTION B',name:'Live stickers',line:'Round 5 stickers, scattered and tilted, now all live.',m:R6.stickers,
        why:['closest to the cover you picked','Tap the name tag, throw the tennis ball around the cover, slide the puzzle, tap the pill for earlier jobs, or write on the ScribbleScan pad.']},
      {id:'grid',num:'OPTION C',name:'Widget grid',line:'The same ideas as tidy tiles, like a phone home screen.',m:R6.grid,
        why:['the most modern','Tidy tiles: name, ScribbleScan, the puzzle, a tennis court, the NBA scoreboard and a planner that opens the book.']},
      {id:'pad',num:'OPTION D',name:'Write on it',line:'One big ScribbleScan pad in the middle, stickers around it.',m:R6.pad,
        why:['ScribbleScan as the hero','The pad writes and scans words on its own. Draw on it and it scans your doodle too. The ball and puzzle still play.']},
    ]},
  r5:{intro:'Round 5: the first screen. The notebook now starts closed, with a real cover you open, in three looks. The fourth option tries a shelf of books instead of one. The pages and the wheel are the same as round 4.',
    dirs:[
      {id:'classic',num:'OPTION A',name:'Classic cover',line:'Blue cloth, a name plate and the elastic band.',m:R5.classic,
        why:['the notebook you already know','Tap the cover, swipe it, or turn the wheel to open it. On desktop the closed book slides to the middle as it opens.']},
      {id:'stickers',num:'OPTION B',name:'Sticker cover',line:'A dark cover covered in stickers of things inside.',m:R5.stickers,
        why:['the most personal','The stickers are things from your pages: ScribbleScan, tennis, puzzle boxes, AI. Tap or turn the wheel to open.']},
      {id:'spiral',num:'OPTION C',name:'Sketchbook',line:'A kraft spiral sketchbook with your name written on it.',m:R5.spiral,
        why:['handmade and warm','A wire spiral, your name in pen and a sticky note. Tap or turn the wheel to open.']},
      {id:'shelf',num:'OPTION D',name:'A shelf of books',line:'One book per section. Pick one and it opens there.',m:R5.shelf,
        why:['several books, to feel the difference','Pick a book to open it at that section. Tap your name at the top to put it back on the shelf.']},
    ]},
  r4:{intro:'Round 4: the wheel from round 3, now one click per page. Scroll over it, drag it or flick it. It coasts, slows down and settles, and every page it passes flips live.',
    dirs:[
      {id:'wheel',num:'THE WHEEL',name:'Page by page',line:'Scroll, drag or flick. Every page flips as it goes by.',m:R4.wheel,
        why:['riffle through the book','On desktop, scroll with the pointer over the wheel. On a phone, drag or flick it. Tap a dot to jump to a section.']},
    ]},
  r3:{intro:'Round 3: the notebook from the mix, with three ways to thumb through it. Pages and content are the same in all three, so the control is the only difference.',
    dirs:[
      {id:'wheel',num:'OPTION A',name:'The wheel',line:'The dial, shrunk and colored into the cover, with dots for sections.',m:R3.wheel,
        why:['closest to the mix you liked','Spin the wheel or tap a dot to flip to a section. The name above it says where you are.']},
      {id:'index',num:'OPTION B',name:'Thumb index',line:'Colored page edges down the side, like a dictionary.',m:R3.index,
        why:['the side of a real book','Slide your thumb down the colored edge, let go on a section, and the book opens there.']},
      {id:'riffle',num:'OPTION C',name:'Riffle',line:'Every page edge along the bottom. Slide across to flip through.',m:R3.riffle,
        why:['page by page, not section by section','Slide along the bottom edge and a bubble names each page as you pass it. Let go to open it.']},
    ]},
  r2:{intro:'Round 2: the notebook and the dial, taken further with your real text from the current site, plus a mix of the two. Every section is reachable, with an about and a Say hi. Tap around.',
    dirs:[
      {id:'notebook',num:'OPTION A',name:'Notebook',line:'Tabs, pages that really turn, and the contents page as your map.',m:R2.notebook,
        why:['the most intuitive','Tap a tab to jump to a section. Turn pages with the folded corner or a swipe. Page numbers in the contents are real.']},
      {id:'dial',num:'OPTION B',name:'The dial',line:'One knob under your thumb. Spin it and the whole page scrubs along.',m:R2.dial,
        why:['the one nobody else has','Drag the dial and the page slides with it, then clicks into place. Tap a label, or use the arrows on desktop.']},
      {id:'mix',num:'OPTION C',name:'Notebook + dial',line:'The notebook, with the dial in place of the tabs.',m:R2.mix,
        why:['a mix to try','Spin the dial to flip to a section. Corners and swipes still turn pages, and the dial follows along.']},
    ]},
  r1:{intro:'Round 1, kept for reference: the three first looks with sample text.',
    dirs:[
      {id:'board',num:'DIRECTION 1',name:'Pinned board',line:'Your current map, cleaned up.',m:R1.board,why:['closest to what you have now','Tap a note and the board slides over to it.']},
      {id:'book',num:'DIRECTION 2',name:'Notebook',line:'Tabs on the edge and pages that turn.',m:R1.book,why:['the most familiar object','Tabs jump, the corner turns the page.']},
      {id:'dial',num:'DIRECTION 3',name:'The dial',line:'No metaphor, one big knob.',m:R1.dial,why:['the toy is the navigation','Drag the dial and the page scrubs along.']},
    ]},
};
let round='r2',dir=null,inst={};
const store={get(k){try{return localStorage.getItem(k)}catch(_){return null}},set(k,v){try{localStorage.setItem(k,v)}catch(_){}}};
function setRound(r){
  round=r;store.set('pf-round',r);
  if(ROUNDS[r].pickCover&&!store.get('pf-cv-'+r)){R7.setCover(ROUNDS[r].pickCover);store.set('pf-cv-'+r,'1')}
  document.querySelectorAll('[data-rd]').forEach(b=>b.setAttribute('aria-pressed',b.dataset.rd===r));
  document.getElementById('intro').textContent=ROUNDS[r].intro;
  const pk=document.getElementById('picker');
  pk.innerHTML=ROUNDS[r].dirs.map(d=>`<button type="button" class="pick" id="pick-${r}-${d.id}" data-d="${d.id}"><span class="num">${d.num}</span><b>${d.name}</b><span>${d.line}</span></button>`).join('');
  pk.querySelectorAll('.pick').forEach(b=>b.onclick=()=>choose(b.dataset.d));
  const saved=store.get('pf-dir-'+r);
  choose(ROUNDS[r].dirs.some(d=>d.id===saved)?saved:ROUNDS[r].dirs[0].id);
}
function choose(id){
  dir=id;store.set('pf-dir-'+round,id);
  const d=ROUNDS[round].dirs.find(x=>x.id===id);
  document.querySelectorAll('.pick').forEach(b=>b.setAttribute('aria-pressed',b.dataset.d===id));
  const cr=document.getElementById('covrow'),cp=document.getElementById('cover-picker');
  if(ROUNDS[round].covers){cr.hidden=false;const pickCv=ROUNDS[round].pickCover,cvs=pickCv?[...R7.COVERS].sort((x,y)=>(y.id===pickCv)-(x.id===pickCv)):R7.COVERS;cp.innerHTML=cvs.map(c=>`<button type="button" data-cv="${c.id}" aria-pressed="${c.id===R7.cover}">${c.name}${c.id===pickCv?' (my pick)':''}</button>`).join('');
    cp.querySelectorAll('button').forEach(b=>b.onclick=()=>{R7.setCover(b.dataset.cv);choose(dir)});
    const showTy=ROUNDS[round].typists!==false;document.getElementById('typist-picker').hidden=document.getElementById('ty-k').hidden=!showTy;
    const tp=document.getElementById('typist-picker');tp.innerHTML=R7.TYPISTS.map(c=>`<button type="button" data-ty="${c.id}" aria-pressed="${c.id===R7.typist}">${c.name}</button>`).join('');
    tp.querySelectorAll('button').forEach(b=>b.onclick=()=>{R7.setTypist(b.dataset.ty);choose(dir)})}else cr.hidden=true;
  const pp=document.getElementById('pad-picker'),pk=document.getElementById('pad-k'),showPads=!!ROUNDS[round].pads;pp.hidden=pk.hidden=!showPads;
  if(showPads){pp.innerHTML=R7.PADS.map(c=>`<button type="button" data-pd="${c.id}" aria-pressed="${c.id===R7.pad}">${c.name}</button>`).join('');
    pp.querySelectorAll('button').forEach(b=>b.onclick=()=>{R7.setPad(b.dataset.pd);choose(dir)})}
  document.getElementById('why-note').textContent=d.why[0];document.getElementById('why-tip').textContent=d.why[1];
  for(const [elId,mode] of [['m-phone','phone'],['m-desk','desktop']]){
    const old=document.getElementById(elId),el=old.cloneNode(false);el.className='mock '+mode;old.replaceWith(el);
    inst[mode]=d.m(el,mode);
  }
}
document.querySelectorAll('[data-rd]').forEach(b=>b.onclick=()=>setRound(b.dataset.rd));
document.getElementById('reset-phone').onclick=()=>inst.phone&&inst.phone.reset();
document.getElementById('reset-desk').onclick=()=>inst.desktop&&inst.desktop.reset();
function theme(t){
  if(t) document.documentElement.setAttribute('data-theme',t);
  const isDark=t?t==='dark':matchMedia('(prefers-color-scheme: dark)').matches;
  document.getElementById('th-light').setAttribute('aria-pressed',!isDark);document.getElementById('th-dark').setAttribute('aria-pressed',isDark);
}
document.querySelectorAll('[data-th]').forEach(b=>b.onclick=()=>theme(b.dataset.th));
theme(document.documentElement.getAttribute('data-theme'));
function fit(){
  for(const id of ['fit-phone','fit-desk']){
    const w=document.getElementById(id),dv=w.firstElementChild;
    const s=Math.min(1,w.clientWidth/dv.offsetWidth);dv.style.transform=`scale(${s})`;w.style.height=dv.offsetHeight*s+'px';
  }
}
new ResizeObserver(fit).observe(document.querySelector('.stage'));
setRound('r17');fit();
if(document.fonts&&document.fonts.ready)document.fonts.ready.then(()=>{for(const m in inst)inst[m]&&inst[m].redraw&&inst[m].redraw()});
