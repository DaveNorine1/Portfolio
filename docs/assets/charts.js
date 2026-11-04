//small dependency-free chart helpers. every chart gets hover values and a data table.
(function(){
const NS='http://www.w3.org/2000/svg';
const el=(n,a={},p)=>{const e=document.createElementNS(NS,n);for(const k in a)e.setAttribute(k,a[k]);if(p)p.appendChild(e);return e};
const nice=(lo,hi,n=4)=>{const s=(hi-lo)/n,m=Math.pow(10,Math.floor(Math.log10(s))),f=s/m,st=(f<1.5?1:f<3?2:f<7?5:10)*m,t=[];for(let v=Math.ceil(lo/st)*st;v<=hi+1e-9;v+=st)t.push(+v.toFixed(8));return t};
function table(host,head,rows){const d=document.createElement('details');d.innerHTML='<summary>Data table</summary>';const w=document.createElement('div');w.className='tablewrap';const t=document.createElement('table');t.innerHTML='<thead><tr>'+head.map(h=>'<th>'+h+'</th>').join('')+'</tr></thead><tbody>'+rows.map(r=>'<tr>'+r.map(c=>'<td>'+c+'</td>').join('')+'</tr>').join('')+'</tbody>';w.appendChild(t);d.appendChild(w);host.appendChild(d)}
function tip(box){const t=document.createElement('div');t.className='tip';t.hidden=true;box.appendChild(t);return (html,x,y)=>{if(html==null){t.hidden=true;return}t.innerHTML=html;t.hidden=false;const w=box.clientWidth,tw=t.offsetWidth;t.style.left=Math.max(0,Math.min(w-tw,x+12))+'px';t.style.top=Math.max(0,y-t.offsetHeight-8)+'px'}}
window.lineChart=function(id,o){
 const host=document.getElementById(id),W=Math.max(300,host.clientWidth||720),H=o.height||(W<500?230:270),m={t:10,r:14,b:38,l:46},box=document.createElement('div');box.className='chart';
 if(o.series.length>1){const l=document.createElement('div');l.className='legend';l.innerHTML=o.series.map(s=>'<span><i style="background:var('+s.color+')"></i>'+s.name+'</span>').join('');host.appendChild(l)}
 host.appendChild(box);const svg=el('svg',{viewBox:`0 0 ${W} ${H}`,role:'img','aria-label':o.label},box);
 const all=o.series.flatMap(s=>s.values),lo=o.ymin??Math.min(...all),hi=o.ymax??Math.max(...all),pad=(hi-lo)*.06,y0=o.ymin??lo-pad,y1=o.ymax??hi+pad;
 const X=i=>m.l+(W-m.l-m.r)*i/(o.x.length-1),Y=v=>H-m.b-(H-m.t-m.b)*(v-y0)/(y1-y0);
 nice(y0,y1).forEach(v=>{el('line',{x1:m.l,x2:W-m.r,y1:Y(v),y2:Y(v),stroke:'var(--line)','stroke-width':1},svg);el('text',{x:m.l-8,y:Y(v)+4,'text-anchor':'end'},svg).textContent=(o.fmt||String)(v)});
 const step=Math.ceil(o.x.length/(W<500?4:6));o.x.forEach((v,i)=>{if(i%step==0){el('text',{x:X(i),y:H-m.b+18,'text-anchor':'middle'},svg).textContent=v}});
 if(o.xTitle)el('text',{x:(W+m.l-m.r)/2,y:H-4,'text-anchor':'middle'},svg).textContent=o.xTitle;
 if(o.marker!=null){const i=o.x.indexOf(o.marker.x);el('line',{x1:X(i),x2:X(i),y1:m.t,y2:H-m.b,stroke:'var(--muted)','stroke-dasharray':'4 4'},svg);el('text',{x:X(i)-6,y:m.t+12,'text-anchor':'end',class:'lab'},svg).textContent=o.marker.label}
 o.series.forEach(s=>{el('path',{d:s.values.map((v,i)=>(i?'L':'M')+X(i).toFixed(1)+' '+Y(v).toFixed(1)).join(''),fill:'none',stroke:`var(${s.color})`,'stroke-width':2,'stroke-linejoin':'round','stroke-linecap':'round'},svg)});
 const cross=el('line',{y1:m.t,y2:H-m.b,stroke:'var(--muted)',visibility:'hidden'},svg),t=tip(box);
 const hit=el('rect',{x:m.l,y:m.t,width:W-m.l-m.r,height:H-m.t-m.b,fill:'transparent'},svg);
 const move=e=>{const r=svg.getBoundingClientRect(),cx=(e.clientX-r.left)/r.width*W,i=Math.max(0,Math.min(o.x.length-1,Math.round((cx-m.l)/(W-m.l-m.r)*(o.x.length-1))));cross.setAttribute('x1',X(i));cross.setAttribute('x2',X(i));cross.setAttribute('visibility','visible');t('<b>'+(o.xName||'')+' '+o.x[i]+'</b><br>'+o.series.map(s=>s.name+': '+(o.fmt||String)(s.values[i])).join('<br>'),X(i)/W*r.width,Y(o.series[0].values[i])/H*r.height)};
 hit.style.touchAction='pan-y';hit.addEventListener('pointerdown',move);hit.addEventListener('pointermove',move);hit.addEventListener('pointerleave',e=>{if(e.pointerType==='touch')return;cross.setAttribute('visibility','hidden');t(null)});
 table(host,[o.xName||'',...o.series.map(s=>s.name)],o.x.map((v,i)=>[v,...o.series.map(s=>(o.fmt||String)(s.values[i]))]));
};
//horizontal dots with ranges, for estimates and intervals
window.rangeChart=function(id,o){
 const host=document.getElementById(id),rowH=44,W=Math.max(300,host.clientWidth||720),m={t:8,r:18,b:30,l:Math.min(o.labelW||190,W*.4)},H=m.t+m.b+rowH*o.rows.length,box=document.createElement('div');box.className='chart';host.appendChild(box);
 const svg=el('svg',{viewBox:`0 0 ${W} ${H}`,role:'img','aria-label':o.label},box),all=o.rows.flatMap(r=>[r.low,r.high,r.mid,r.truth??r.mid]);
 const lo=Math.min(...all,o.zero?0:Infinity),hi=Math.max(...all,o.zero?0:-Infinity),pad=(hi-lo)*.08,X=v=>m.l+(W-m.l-m.r)*(v-(lo-pad))/(hi-lo+2*pad);
 nice(lo-pad,hi+pad,5).forEach(v=>{el('line',{x1:X(v),x2:X(v),y1:m.t,y2:H-m.b,stroke:v===0?'var(--muted)':'var(--line)'},svg);el('text',{x:X(v),y:H-m.b+18,'text-anchor':'middle'},svg).textContent=o.fmt(v)});
 const t=tip(box);
 o.rows.forEach((r,i)=>{const y=m.t+rowH*i+rowH/2;el('text',{x:0,y:y+4,class:'lab'},svg).textContent=r.label;
  if(r.low!==r.high)el('line',{x1:X(r.low),x2:X(r.high),y1:y,y2:y,stroke:'var(--s1)','stroke-width':2,'stroke-linecap':'round'},svg);
  el('circle',{cx:X(r.mid),cy:y,r:5.5,fill:'var(--s1)',stroke:'var(--surface)','stroke-width':2},svg);
  if(r.truth!=null)el('path',{d:`M${X(r.truth)} ${y-7}l6 7l-6 7l-6-7z`,fill:'var(--s2)',stroke:'var(--surface)','stroke-width':1.5},svg);
  const hit=el('rect',{x:0,y:y-rowH/2,width:W,height:rowH,fill:'transparent'},svg);
  const html='<b>'+r.label+'</b><br>Estimate: '+o.fmt(r.mid)+(r.low!==r.high?'<br>Range: '+o.fmt(r.low)+' to '+o.fmt(r.high):'')+(r.truth!=null?'<br>Known truth: '+o.fmt(r.truth):'');
  const sh=e=>{const b=svg.getBoundingClientRect();t(html,e.clientX-b.left,e.clientY-b.top)};hit.addEventListener('pointerdown',sh);hit.addEventListener('pointermove',sh);hit.addEventListener('pointerleave',e=>{if(e.pointerType!=='touch')t(null)})});
 if(o.legend){const l=document.createElement('div');l.className='legend';l.innerHTML=o.legend;host.appendChild(l)}
 table(host,['',...(o.rows[0].truth!=null?['Estimate','Low','High','Known truth']:['Estimate','Low','High'])],o.rows.map(r=>[r.label,o.fmt(r.mid),o.fmt(r.low),o.fmt(r.high),...(r.truth!=null?[o.fmt(r.truth)]:[])]));
};
//plain bars, thin, labelled directly
window.barChart=function(id,o){
 const host=document.getElementById(id),rowH=38,W=Math.max(300,host.clientWidth||720),m={t:4,r:o.rightPad||74,b:6,l:Math.min(o.labelW||200,W*.5)},H=m.t+m.b+rowH*o.rows.length,box=document.createElement('div');box.className='chart';host.appendChild(box);
 const svg=el('svg',{viewBox:`0 0 ${W} ${H}`,role:'img','aria-label':o.label},box),vals=o.rows.map(r=>r.value),lo=Math.min(0,...vals),hi=Math.max(0,...vals),X=v=>m.l+(W-m.l-m.r)*(v-lo)/((hi-lo)||1),t=tip(box);
 o.rows.forEach((r,i)=>{const y=m.t+rowH*i+rowH/2;const maxCh=Math.floor((m.l-44)/6.6),lw=r.label.split(' ');if(r.label.length>maxCh&&lw.length>1){let a1='',i=0;while(i<lw.length&&(a1+' '+lw[i]).trim().length<=maxCh)a1=(a1+' '+lw[i++]).trim();const tx=el('text',{x:0,y:y-3,class:'lab'},svg);tx.textContent=a1;el('text',{x:0,y:y+11,class:'lab'},svg).textContent=lw.slice(i).join(' ')}else el('text',{x:0,y:y+4,class:'lab'},svg).textContent=r.label;const a=X(Math.min(0,r.value)),b=X(Math.max(0,r.value));
  el('rect',{x:a,y:y-8,width:Math.max(b-a,1),height:16,rx:3,fill:'var(--s1)'},svg);
  el('text',{x:r.value>=0?b+6:a-6,y:y+4,'text-anchor':r.value>=0?'start':'end'},svg).textContent=r.text||o.fmt(r.value);
  const hit=el('rect',{x:0,y:y-rowH/2,width:W,height:rowH,fill:'transparent'},svg);const sh=e=>{const s=svg.getBoundingClientRect();t('<b>'+r.label+'</b><br>'+(r.text||o.fmt(r.value)),e.clientX-s.left,e.clientY-s.top)};hit.addEventListener('pointerdown',sh);hit.addEventListener('pointermove',sh);hit.addEventListener('pointerleave',e=>{if(e.pointerType!=='touch')t(null)})});
 table(host,['',o.valueName||'Value'],o.rows.map(r=>[r.label,r.text||o.fmt(r.value)]));
};
window.budgetSim=function(id,d){
 const host=document.getElementById(id),names=d.names,cur=d.sim.current,pct=cur.map(()=>100);
 const hill=(x,h,s)=>Math.pow(x,s)/(Math.pow(x,s)+Math.pow(h,s));
 const media=sp=>sp.reduce((a,s,i)=>a+d.sim.beta[i]*hill(s/(1-d.sim.decay[i]),d.sim.half_sat[i],d.sim.shape),0);
 const base=d.sim.baseline,now=base+media(cur),total=cur.reduce((a,b)=>a+b,0);
 const presets={'Current plan':cur,'Cut every channel 20%':cur.map(c=>c*.8),"Model's 20% cut":d.opt};
 host.className='sim';host.innerHTML='<div class="btns">'+Object.keys(presets).map((k,i)=>`<button type="button" data-p="${k}" aria-pressed="false">${k}</button>`).join('')+'</div>'+names.map((n,i)=>`<div class="row"><label for="sl${i}">${n}</label><input id="sl${i}" type="range" min="50" max="150" step="1" value="100"><output id="o${i}"></output></div>`).join('')+'<div class="out"><div><b id="bud"></b><span>Budget vs. current plan</span></div><div><b id="lea"></b><span>Weekly leads vs. current plan</span></div></div>';
 const show=()=>{const sp=cur.map((c,i)=>c*pct[i]/100);names.forEach((_,i)=>{host.querySelector('#sl'+i).value=Math.round(pct[i]);host.querySelector('#o'+i).textContent=Math.round(pct[i])+'%'});const b=sp.reduce((a,x)=>a+x,0)/total-1,l=(base+media(sp))/now-1,f=v=>(v>=0?'+':'')+(v*100).toFixed(1)+'%';host.querySelector('#bud').textContent=f(b);host.querySelector('#lea').textContent=f(l)};
 const press=k=>host.querySelectorAll('button').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.p===k)));
 host.querySelectorAll('button').forEach(b=>b.addEventListener('click',()=>{presets[b.dataset.p].forEach((s,i)=>pct[i]=s/cur[i]*100);press(b.dataset.p);show()}));
 names.forEach((_,i)=>host.querySelector('#sl'+i).addEventListener('input',e=>{pct[i]=+e.target.value;press(null);show()}));
 presets['Cut every channel 20%'].forEach((s,i)=>pct[i]=s/cur[i]*100);press('Cut every channel 20%');show();
};
})();
