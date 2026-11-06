/* ================= ROUND 3 ================= */
const R3=(()=>{
const {notebook,secOf,SECS,E,pg,top,PC,esc}=R2.lib;
const secIdx=id=>SECS.findIndex(s=>s.id===secOf(id));
const titleOf=id=>E[id]?E[id].t:(id==='me'?'About me':id==='toc'?'Contents':SECS.find(s=>s.id===id).tab);
function base(root,mode,cls,hint){
  root.classList.add('v3',cls);root.innerHTML=top();
  const box={ctl:null};
  box.nb=notebook(root,mode,{tabs:false,hint,onView(id){box.ctl&&box.ctl.sync(id)}});
  root.addEventListener('click',e=>{if(e.target.closest('[data-home]'))box.nb.go('me');if(e.target.closest('[data-say]'))box.nb.go('say')});
  return box;
}
const scale=(root,mode)=>root.getBoundingClientRect().width/(mode==='phone'?390:1277)||1;

/* A. the wheel */
function mountWheel(root,mode){
  const P=mode==='phone',n=SECS.length,STEP=P?38:30,R=P?100:196;
  const box=base(root,mode,'v3a','spin the wheel, or turn the page');
  root.insertAdjacentHTML('beforeend',`<div class="kb-wrap"><div class="kb-pointer"></div><div class="kb-dial" role="slider" tabindex="0" aria-label="Section" aria-valuemin="0" aria-valuemax="${n-1}">${SECS.map((s,i)=>`<div class="kb-dot"><button type="button" data-i="${i}" tabindex="-1" aria-label="${s.dial}" style="--dot:${PC(s.c)}"><i></i></button></div>`).join('')}</div><div class="kb-name"></div></div>`);
  const el=root.querySelector('.kb-dial'),dots=[...el.querySelectorAll('button')],name=root.querySelector('.kb-name');
  const b0=P?-90:0;
  dots.forEach((b,i)=>{const a=(b0+i*STEP)*Math.PI/180;b.style.left=Math.cos(a)*R+'px';b.style.top=Math.sin(a)*R+'px'});
  let idx=0,rot=0,d=null;
  function render(r){rot=r;el.style.rotate=r+'deg';const c=Math.max(0,Math.min(n-1,Math.round(-r/STEP)));dots.forEach((b,i)=>b.classList.toggle('cur',i===c));name.textContent=SECS[c].dial;el.setAttribute('aria-valuenow',c);el.setAttribute('aria-valuetext',SECS[c].dial)}
  function to(i,silent){i=Math.max(0,Math.min(n-1,i));idx=i;el.classList.remove('drag');render(-i*STEP);if(!silent)box.nb.go(SECS[i].id,{silent:true})}
  const ang=e=>{const r=el.getBoundingClientRect();return Math.atan2(e.clientY-(r.top+r.height/2),e.clientX-(r.left+r.width/2))*180/Math.PI};
  el.addEventListener('pointerdown',e=>{if(e.button)return;d={a:ang(e),r:rot,moved:false,t:e.target};try{el.setPointerCapture(e.pointerId)}catch(_){}});
  el.addEventListener('pointermove',e=>{if(!d)return;let da=ang(e)-d.a;if(da>180)da-=360;if(da<-180)da+=360;
    if(!d.moved&&Math.abs(da)>3){d.moved=true;el.classList.add('drag')}
    if(d.moved){let r=d.r+da;const lo=-(n-1)*STEP;if(r>0)r*=.3;if(r<lo)r=lo+(r-lo)*.3;d.a=ang(e);d.r=r;render(r)}});
  const up=()=>{if(!d)return;const {moved,t}=d;d=null;if(moved)to(Math.round(-rot/STEP));else{const b=t.closest&&t.closest('button[data-i]');if(b)to(+b.dataset.i)}};
  el.addEventListener('pointerup',up);el.addEventListener('pointercancel',()=>{if(d){d=null;to(Math.round(-rot/STEP))}});
  el.addEventListener('keydown',e=>{if(e.key==='ArrowRight'||e.key==='ArrowDown'){e.preventDefault();to(idx+1)}if(e.key==='ArrowLeft'||e.key==='ArrowUp'){e.preventDefault();to(idx-1)}});
  const inst=()=>{el.classList.add('drag');render(-idx*STEP);requestAnimationFrame(()=>el.classList.remove('drag'))};
  box.ctl={sync(id){idx=secIdx(id);render(-idx*STEP)}};
  inst();
  return {reset(){box.nb.reset();idx=0;inst()}};
}

/* B. thumb index along the page edge */
function mountIndex(root,mode){
  const n=SECS.length;
  const box=base(root,mode,'v3b','slide your thumb down the edge');
  root.insertAdjacentHTML('beforeend',`<div class="ti" role="tablist" aria-label="Sections">${SECS.map((s,i)=>`<button type="button" class="ti-seg" role="tab" data-i="${i}" style="--pc:${PC(s.c)}">${s.tab}</button>`).join('')}<div class="bubble"></div></div>`);
  const ti=root.querySelector('.ti'),segs=[...ti.querySelectorAll('.ti-seg')],bub=ti.querySelector('.bubble');
  let d=null,hov=-1;
  const at=e=>{const r=ti.getBoundingClientRect();return Math.max(0,Math.min(n-1,Math.floor((e.clientY-r.top)/r.height*n)))};
  function show(i,e){if(i===hov)return;hov=i;segs.forEach((s,j)=>s.classList.toggle('hover',j===i));
    const r=ti.getBoundingClientRect(),k=scale(root,mode);const y=((i+.5)/n)*r.height/k;
    bub.innerHTML=`${SECS[i].dial}<small>p.${pg(SECS[i].id)}</small>`;bub.style.top=(y-22)+'px';bub.classList.add('on')}
  function hide(){hov=-1;segs.forEach(s=>s.classList.remove('hover'));bub.classList.remove('on')}
  ti.addEventListener('pointerdown',e=>{if(e.button)return;d=true;try{ti.setPointerCapture(e.pointerId)}catch(_){}show(at(e),e)});
  ti.addEventListener('pointermove',e=>{if(d)show(at(e),e)});
  ti.addEventListener('pointerup',e=>{if(!d)return;d=null;const i=at(e);hide();box.nb.go(SECS[i].id,{silent:true});sync(SECS[i].id)});
  ti.addEventListener('pointercancel',()=>{d=null;hide()});
  ti.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){const b=e.target.closest('.ti-seg');if(b){e.preventDefault();box.nb.go(SECS[+b.dataset.i].id,{silent:true});sync(SECS[+b.dataset.i].id)}}});
  function sync(id){const c=secIdx(id);segs.forEach((s,j)=>{s.toggleAttribute('aria-current',j===c);s.setAttribute('aria-selected',j===c)})}
  box.ctl={sync};sync('me');
  return {reset(){box.nb.reset();hide();sync('me')}};
}

/* C. riffle along the bottom edge */
function mountRiffle(root,mode){
  const box=base(root,mode,'v3c','slide along the bottom edge');
  const order=box.nb.order,n=order.length;
  // section spans for the labels under the edge
  const spans=[];order.forEach(id=>{const s=secOf(id);const last=spans[spans.length-1];if(last&&last.s===s)last.c++;else spans.push({s,c:1})});
  root.insertAdjacentHTML('beforeend',`<div class="rf" role="slider" tabindex="0" aria-label="Page" aria-valuemin="1" aria-valuemax="${n}">
    <div class="rf-edges">${order.map(id=>`<i style="--pc:${PC(SECS[secIdx(id)].c)}"></i>`).join('')}</div>
    <div class="rf-secs">${spans.map(x=>{const nm=SECS.find(s=>s.id===x.s).tab;return `<span style="flex:${x.c} 1 0" title="${nm}">${x.c/n<(mode==='phone'?.12:.07)?nm[0]:nm}</span>`}).join('')}</div>
    <div class="rf-mark"></div><div class="bubble"></div></div>`);
  const rf=root.querySelector('.rf'),mark=rf.querySelector('.rf-mark'),bub=rf.querySelector('.bubble');
  let d=null,cur=0;
  const at=e=>{const r=rf.getBoundingClientRect();return Math.max(0,Math.min(n-1,Math.floor((e.clientX-r.left)/r.width*n)))};
  const pos=i=>((i+.5)/n*100)+'%';
  function show(i){mark.style.left=pos(i);bub.style.left=pos(i);bub.innerHTML=`${esc(titleOf(order[i]))}<small>p.${pg(order[i])} · ${SECS[secIdx(order[i])].tab}</small>`;bub.classList.add('on')}
  rf.addEventListener('pointerdown',e=>{if(e.button)return;d=true;rf.classList.add('drag');try{rf.setPointerCapture(e.pointerId)}catch(_){}show(at(e))});
  rf.addEventListener('pointermove',e=>{if(d)show(at(e))});
  rf.addEventListener('pointerup',e=>{if(!d)return;d=null;rf.classList.remove('drag');bub.classList.remove('on');const i=at(e);box.nb.go(order[i],{silent:true});sync(order[i])});
  rf.addEventListener('pointercancel',()=>{d=null;rf.classList.remove('drag');bub.classList.remove('on');sync(order[cur])});
  rf.addEventListener('keydown',e=>{const k={ArrowRight:1,ArrowLeft:-1}[e.key];if(k){e.preventDefault();const i=Math.max(0,Math.min(n-1,cur+k));box.nb.go(order[i],{silent:true});sync(order[i])}});
  function sync(id){cur=Math.max(0,order.indexOf(id));mark.style.left=pos(cur);rf.setAttribute('aria-valuenow',cur+1);rf.setAttribute('aria-valuetext',`${titleOf(id)}, page ${pg(id)}`)}
  box.ctl={sync};sync('me');
  return {reset(){box.nb.reset();sync('me')}};
}
return {wheel:mountWheel,index:mountIndex,riffle:mountRiffle};
})();
