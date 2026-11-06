/* ================= ROUND 5: the first screen ================= */
/* A, B, C: the same notebook and wheel, closed, with a real cover you open. D: a shelf of books, one per section. */
const R5=(()=>{
const {SECS,secOf,pg,PC,esc}=R2.lib;
const LOGO_IMG=()=>`<img alt="" src="${LOGO}">`;
const COVERS={
  classic:()=>`<div class="cv-plate"><div class="cv-k">Notebook</div><div class="cv-name">${LOGO_IMG()}David Lybeck</div><div class="cv-secs">Projects · Work · School · Hobbies</div></div><span class="cv-open">open</span>`,
  stickers:()=>`<div class="st st-tag"><b>HELLO</b><small>my name is</small><span>David</span></div>
    <div class="st st-logo">${LOGO_IMG()}</div>
    <div class="st st-ss">ScribbleScan</div>
    <div class="st st-ball"></div>
    <div class="st st-box"><i></i><i></i><i></i></div>
    <div class="st st-wheel">AI</div>
    <span class="cv-open">open</span>`,
  spiral:()=>`<div class="sp-rings">${'<i></i>'.repeat(14)}</div><div class="sp-title">David Lybeck</div><div class="sp-line"></div><div class="sp-note">${LOGO_IMG()}<span>about me<br>inside</span></div><span class="cv-open">open</span>`,
};
function mountCover(kind){return (root,mode)=>{
  const P=mode==='phone';let closed=true,cv=null,w=null;
  const name=()=>closed?'Cover':null;
  function build(){
    const book=root.querySelector('.nb-book');
    cv=document.createElement('div');cv.className=`nb-leaf go cv cv-${kind}`;cv.setAttribute('role','button');cv.setAttribute('tabindex','0');cv.setAttribute('aria-label','Open the notebook');
    cv.innerHTML=`<div class="face front cv-front">${COVERS[kind]()}</div><div class="face back">${P?'':`<div class="nb-in">${root.querySelector('.nb-page.l .nb-in').innerHTML}</div>`}</div>`;
    book.appendChild(cv);
    const stop=e=>e.stopPropagation();
    cv.addEventListener('pointerdown',stop);cv.addEventListener('pointerup',stop);
    cv.addEventListener('click',e=>{e.stopPropagation();open()});
    cv.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();open()}});
    let sx=null;cv.addEventListener('pointerdown',e=>{sx=e.clientX});cv.addEventListener('pointerup',e=>{if(sx!==null&&e.clientX-sx<-30)open();sx=null});
  }
  function open(){
    if(!closed)return;closed=false;root.classList.remove('closed');w&&w.refresh();
    const c=cv;if(reduce){c.remove();return}
    c.style.transition='transform 950ms cubic-bezier(0.45,0.05,0.25,1)';c.style.transform='rotateY(-180deg)';
    setTimeout(()=>c.remove(),980);
  }
  root.classList.add('cvr','cvr-'+kind,'closed');
  w=R4.wheel(root,mode,{name,gate(kind){if(!closed)return false;open();return kind!=='header'}});
  build();w.refresh();
  return {reset(){w.reset();if(cv)cv.remove();closed=true;root.classList.add('closed');build();w.refresh()}};
};}

/* D: a shelf of books */
function mountShelf(root,mode){
  const P=mode==='phone';
  root.classList.add('shelfmode','on-shelf');
  const w=R4.wheel(root,mode,{gate(k){if(k==='home'&&!root.classList.contains('on-shelf')){toShelf();return true}return root.classList.contains('on-shelf')}});
  const nb=w.nb,ph=['me','toc','projects','scribblescan','site','nba','planner','programs','work','school','hobbies','printing','gaming','tennis','say'];
  const range=sid=>{const ps=ph.filter(id=>secOf(id)===sid).map(pg);const a=Math.min(...ps),b=Math.max(...ps);return a===b?`p.${a}`:`p.${a} to ${b}`};
  const looks=[{id:'me',t:'David Lybeck',c:'var(--brand)',ink:'#fff',h:92,wd:94},{id:'projects',h:84,wd:78},{id:'work',h:78,wd:66},{id:'school',h:72,wd:58},{id:'hobbies',h:86,wd:72},{id:'say',h:68,wd:54,lean:1}];
  const books=looks.map((b,i)=>{const s=SECS.find(x=>x.id===b.id);return {...b,t:b.t||s.tab,c:b.c||PC(s.c),ink:b.ink||'var(--ink-fixed)',r:range(b.id),i}});
  const html=`<div class="shelf"><div class="sh-row">${books.map(b=>`<button type="button" class="bk${b.lean?' lean':''}" data-book="${b.id}" style="--bc:${b.c};--bi:${b.ink};--h:${b.h}%;--w:${b.wd}px;--o:${(b.i%3-1)*10}px">
      <span class="bk-t">${b.id==='me'?`<img alt="" src="${LOGO}">`:''}${esc(b.t)}</span><span class="bk-r">${b.r}</span></button>`).join('')}</div>
      <div class="sh-plank"></div><span class="sh-hint">pick a book</span></div>`;
  root.insertAdjacentHTML('beforeend',html);
  const shelf=root.querySelector('.shelf'),cover=root.querySelector('.nb-cover');
  shelf.addEventListener('click',e=>{const b=e.target.closest('.bk');if(!b||!root.classList.contains('on-shelf'))return;
    const sid=b.dataset.book,bk=books.find(x=>x.id===sid);b.classList.add('picked');
    setTimeout(()=>{cover.style.background=bk.c;nb.go(sid,{instant:true});w.ctl.sync(nb.cur);root.classList.remove('on-shelf');w.refresh()},reduce?0:420);
  });
  function toShelf(){root.classList.add('on-shelf');shelf.querySelectorAll('.picked').forEach(x=>x.classList.remove('picked'))}
  return {reset(){w.reset();cover.style.background='';toShelf()}};
}
return {classic:mountCover('classic'),stickers:mountCover('stickers'),spiral:mountCover('spiral'),shelf:mountShelf};
})();
