/* ================= ROUND 4: the wheel, page by page ================= */
/* One wheel detent per page. Drag, flick or scroll it; it coasts, eases to a stop and settles on a page.
   Every page it passes flips live, so a fast spin riffles through the book. */
const R4=(()=>{
const {notebook,secOf,SECS,E,pg,top,PC}=R2.lib;
function mountWheel(root,mode,opt={}){
  const P=mode==='phone';
  root.classList.add('v3','v3a','v4');root.innerHTML=top();
  let ctl=null;
  const nb=notebook(root,mode,{tabs:false,hint:P?'spin the wheel, or turn the page':'scroll or spin the wheel',onView(id){ctl&&ctl.sync(id)}});
  root.addEventListener('click',e=>{if(opt.gate&&opt.gate(e.target.closest('[data-home]')?'home':'header'))return;if(e.target.closest('[data-home]'))nb.go('me');if(e.target.closest('[data-say]'))nb.go('say')});
  const order=nb.order,N=order.length,STEP=Math.min(P?16:14,300/N),R=P?100:196,TR=P?112:212,b0=P?-90:0,LO=opt.cover?-1:0;
  const first=SECS.map(s=>order.findIndex(id=>secOf(id)===s.id));
  root.insertAdjacentHTML('beforeend',`<div class="kb-wrap"><div class="kb-pointer"></div>
    <div class="kb-dial" role="slider" tabindex="0" aria-label="Page" aria-valuemin="1" aria-valuemax="${N}">
      ${order.map((_,i)=>`<i class="kb-tick" style="--a:${b0+i*STEP}deg;--tr:${TR}px"></i>`).join('')}${LO<0?`<div class="kb-dot kb-cv"><button type="button" data-p="-1" data-k="-1" tabindex="-1" aria-label="Cover"><i></i></button></div>`:''}
      ${SECS.map((s,k)=>first[k]<0?'':`<div class="kb-dot"><button type="button" data-p="${first[k]}" data-k="${k}" tabindex="-1" aria-label="${s.dial}" style="--dot:${PC(s.c)}"><i></i></button></div>`).join('')}
    </div><div class="kb-name"><b></b><small></small></div></div>`);
  const wrap=root.querySelector('.kb-wrap'),el=wrap.querySelector('.kb-dial'),dots=[...el.querySelectorAll('button')],nm=wrap.querySelector('.kb-name b'),sm=wrap.querySelector('.kb-name small');
  dots.forEach(b=>{const a=(b0+(+b.dataset.p)*STEP)*Math.PI/180;b.style.left=Math.cos(a)*R+'px';b.style.top=Math.sin(a)*R+'px'});
  const clamp=(v,a,b)=>Math.max(a,Math.min(b,v)),near=p=>clamp(Math.round(p),LO,N-1);
  // physics, in pages: pos (float), vel (pages/s)
  let pos=LO,vel=0,target=null,drag=null,raf=0,last=0,shown=LO,quiet=false,lastIn=0,acc=0,samples=[];
  const K=150,C=2*Math.sqrt(K),FRICTION=3.2,DIRECT=.004,GAIN=.024,VMAX=26;
  function render(){
    el.style.rotate=(-pos*STEP)+'deg';
    const i=near(pos);
    if(i<0){dots.forEach(b=>b.classList.toggle('cur',b.dataset.k==='-1'));nm.textContent='Cover';sm.textContent='';el.setAttribute('aria-valuenow',0);el.setAttribute('aria-valuetext','Cover');return}
    const id=order[i],k=SECS.findIndex(s=>s.id===secOf(id));
    dots.forEach(b=>b.classList.toggle('cur',+b.dataset.k===k));
    const ov=opt.name&&opt.name();nm.textContent=ov||SECS[k].dial;sm.textContent=ov?'':`p.${pg(id)}`;
    el.setAttribute('aria-valuenow',i+1);el.setAttribute('aria-valuetext',`${E[id]?E[id].t:SECS[k].dial}, page ${pg(id)}`);
  }
  function turn(){
    const i=near(pos);if(i===shown)return;
    if(quiet){shown=i;return}
    const speed=Math.abs(vel),dur=clamp(700-speed*38,230,700),d=i>shown?1:-1;
    while(shown!==i){shown+=d;
      if(shown<0){opt.close&&opt.close();continue}
      if(shown===0&&d>0&&LO<0&&opt.isClosed&&opt.isClosed()){opt.open&&opt.open();continue}
      nb.riffle(order[shown],{dur})}
  }
  function frame(t){
    const dt=Math.min(.05,(t-last)/1000||.016);last=t;
    if(drag){/* position follows the finger */}
    else if(target!==null){
      if(reduce){pos=target;vel=0}else{const a=-K*(pos-target)-C*vel;vel+=a*dt;pos+=vel*dt}
      if(Math.abs(pos-target)<.003&&Math.abs(vel)<.03){pos=target;vel=0;target=null;quiet=false}
    }else{
      vel*=Math.exp(-FRICTION*dt);pos+=vel*dt;
      if(pos<LO||pos>N-1){target=near(pos)}
      else if(Math.abs(vel)<1.4&&t-lastIn>140){target=near(pos+vel*.08)}
    }
    render();turn();
    if(drag||target!==null||Math.abs(vel)>.01)raf=requestAnimationFrame(frame);else raf=0;
  }
  const kick=()=>{if(!raf){last=performance.now();raf=requestAnimationFrame(frame)}};
  const take=()=>{if(quiet){quiet=false;shown=opt.isClosed&&opt.isClosed()?-1:Math.max(0,order.indexOf(nb.cur))}};
  // scroll over the wheel turns it, and keeps the page still
  wrap.addEventListener('wheel',e=>{
    e.preventDefault();if(opt.gate&&opt.gate('wheel'))return;take();
    let d=Math.abs(e.deltaY)>=Math.abs(e.deltaX)?e.deltaY:e.deltaX;d*=e.deltaMode===1?33:e.deltaMode===2?400:1;
    if(reduce){acc+=d;if(Math.abs(acc)>=70){target=near(Math.round(pos)+Math.sign(acc));acc=0;kick()}return}
    target=null;lastIn=performance.now();pos=clamp(pos+d*DIRECT,LO-.4,N-.6);vel=clamp(vel+d*GAIN,-VMAX,VMAX);kick();
  },{passive:false});
  // drag and flick
  const ang=e=>{const r=el.getBoundingClientRect();return Math.atan2(e.clientY-(r.top+r.height/2),e.clientX-(r.left+r.width/2))*180/Math.PI};
  const rubber=p=>p<LO?LO+(p-LO)*.3:p>N-1?N-1+(p-(N-1))*.3:p;
  el.addEventListener('pointerdown',e=>{if(e.button)return;if(opt.gate&&opt.gate('down'))return;take();drag={a:ang(e),raw:pos,moved:false,t:e.target};target=null;vel=0;samples=[[performance.now(),pos]];try{el.setPointerCapture(e.pointerId)}catch(_){}kick()});
  el.addEventListener('pointermove',e=>{if(!drag)return;let da=ang(e)-drag.a;if(da>180)da-=360;if(da<-180)da+=360;
    if(!drag.moved&&Math.abs(da)>3){drag.moved=true;el.classList.add('drag')}
    if(!drag.moved)return;
    drag.a=ang(e);drag.raw-=da/STEP;pos=rubber(drag.raw);const now=performance.now();samples.push([now,pos]);while(samples.length>2&&now-samples[0][0]>90)samples.shift()});
  const up=()=>{if(!drag)return;const {moved,t}=drag;drag=null;el.classList.remove('drag');
    if(moved){const [t0,p0]=samples[0],now=performance.now();vel=reduce?0:clamp(now-t0>8?(pos-p0)/((now-t0)/1000):0,-VMAX,VMAX);lastIn=0;
      if(reduce||Math.abs(vel)<1.4)target=near(pos+vel*.08)}
    else{const b=t.closest&&t.closest('button[data-p]');target=b?+b.dataset.p:near(pos)}
    kick()};
  el.addEventListener('pointerup',up);el.addEventListener('pointercancel',up);
  el.addEventListener('keydown',e=>{const k={ArrowRight:1,ArrowDown:1,PageDown:1,ArrowLeft:-1,ArrowUp:-1,PageUp:-1}[e.key];
    if(k){e.preventDefault();if(opt.gate&&opt.gate('key'))return;take();target=near((target??Math.round(pos))+k);vel=0;kick()}});
  // something else turned the page (corner, swipe, contents): glide the wheel there without flipping again
  ctl={sync(id){const i=id==='cover'?LO:order.indexOf(id);if(i<LO)return;quiet=true;shown=i;target=i;vel=0;kick()}};
  render();
  return {nb,ctl,refresh:render,reset(){nb.reset();if(raf)cancelAnimationFrame(raf);raf=0;pos=LO;vel=0;target=null;drag=null;shown=LO;quiet=false;render()}};
}
return {wheel:mountWheel};
})();
