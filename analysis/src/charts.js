<script>
const D = window.__D__;
const S = () => { const c = getComputedStyle(document.documentElement);
  return { s1:c.getPropertyValue('--s1').trim(), s2:c.getPropertyValue('--s2').trim(),
           s3:c.getPropertyValue('--s3').trim(), s4:c.getPropertyValue('--s4').trim(),
           ink:c.getPropertyValue('--ink').trim(), ink2:c.getPropertyValue('--ink-2').trim(),
           ink3:c.getPropertyValue('--ink-3').trim(), rule:c.getPropertyValue('--rule').trim(),
           rule2:c.getPropertyValue('--rule-2').trim(), card:c.getPropertyValue('--card').trim(),
           accent:c.getPropertyValue('--accent').trim(),
           /* זוג ערכיות (טוב/רע) + נייטרלי. חמישה גרפים כאן אינם קטגוריאליים
              אלא מקטבים — „מעל/מתחת לצפוי” — ולכן הם משתמשים בזוג הזה ולא
              בסדרות s1…s4. ΔE ‏CVD של הזוג נמוך, ולכן בכל אחד מהם מוצג גם
              הערך המספרי לצד הסימון ולא רק הצבע. */
           up:c.getPropertyValue('--s-up').trim(),
           down:c.getPropertyValue('--s-down').trim(),
           mid:c.getPropertyValue('--s-ref').trim() }; };
const SHORT={'62+63':'תכנות ושירותי מחשב','64+65+66':'שירותים פיננסיים','46':'מסחר סיטוני',
 '86':'שירותי בריאות','72':'מחקר ופיתוח','26':'ייצור אלקטרוניקה ומחשבים','47':'מסחר קמעונאי',
 '50+51+52+53':'תחבורה, אחסנה ודואר','85':'חינוך','87+88':'שירותי סעד ורווחה','1':'חקלאות — גידולים צמחיים',
 '83':'מינהל מקומי','56':'מסעדות ובתי אוכל','94':'ארגוני חברים','84':'מינהל ציבורי וביטחון',
 '41':'בניית מבנים','10':'ייצור מוצרי מזון'};
const short=(code,name)=>SHORT[String(code)]||name;
const NS='http://www.w3.org/2000/svg';
const el=(t,a={})=>{const n=document.createElementNS(NS,t);for(const k in a)n.setAttribute(k,a[k]);return n;};
// unicode-bidi:plaintext lets each label take its base direction from its own first
// strong character, so Hebrew labels read right-to-left inside an LTR <svg> while
// signed numbers keep their leading minus.
const txt=(s,a={})=>{const n=el('text',Object.assign({'font-family':'Heebo,sans-serif','font-size':12,
  fill:S().ink3,'dominant-baseline':'middle',style:'unicode-bidi:plaintext'},a));n.textContent=s;return n;};
const fmt=n=>n.toLocaleString('he-IL').replace('-','\u2212');
const sgn=n=>(n>0?'+':n<0?'\u2212':'')+Math.abs(n).toFixed(1);
const tip=document.getElementById('tip');
function hover(node,html){
  node.style.cursor='default';
  node.addEventListener('pointerenter',e=>{tip.innerHTML=html;tip.classList.add('on');});
  node.addEventListener('pointermove',e=>{
    const w=tip.offsetWidth,h=tip.offsetHeight;
    tip.style.left=Math.min(Math.max(8,e.clientX-w/2),innerWidth-w-8)+'px';
    tip.style.top=Math.max(8,e.clientY-h-14)+'px';});
  node.addEventListener('pointerleave',()=>tip.classList.remove('on'));
}
function legend(id,items){
  const box=document.getElementById(id); if(!box)return; box.innerHTML='';
  items.forEach(([label,color,line])=>{const s=document.createElement('span');
    s.innerHTML=`<i class="sw${line?' line':''}" style="background:${color}"></i>${label}`;box.appendChild(s);});
}
function table(id,head,rows){
  const box=document.getElementById(id); if(!box)return;
  box.innerHTML='<table><thead><tr>'+head.map((h,i)=>`<th${i?'':' style="text-align:right"'}>${h}</th>`).join('')+
    '</tr></thead><tbody>'+rows.map(r=>'<tr>'+r.map((c,i)=>
      i? `<td class="num">${c}</td>` : `<td class="name">${c}</td>`).join('')+'</tr>').join('')+'</tbody></table>';
}
const clear=id=>{const s=document.getElementById(id);if(s)while(s.firstChild)s.removeChild(s.firstChild);return s;};

/* ---------- 1. index line chart ---------- */
function chart1(){
  const c=S(),svg=clear('c1'); if(!svg)return;
  const W=1000,H=380,m={t:26,r:84,b:34,l:56};
  const ys=D.years, series=[['אשכול גליל מזרחי',D.idx_year['אשכול גליל מזרחי'],c.s1],
    ['תל־אביב',D.idx_year['תל־אביב'],c.s3],['מחוז הצפון',D.idx_year['הצפון'],c.s4]];
  const lo=70,hi=130, x=i=>m.l+i*(W-m.l-m.r)/(ys.length-1), y=v=>m.t+(hi-v)*(H-m.t-m.b)/(hi-lo);
  [70,80,90,100,110,120,130].forEach(v=>{
    svg.appendChild(el('line',{x1:m.l,x2:W-m.r,y1:y(v),y2:y(v),stroke:v===100?c.ink3:c.rule2,
      'stroke-width':v===100?1.5:1,'stroke-dasharray':v===100?'':''}));
    svg.appendChild(txt(v+'%',{x:W-m.r+10,y:y(v),fill:v===100?c.ink2:c.ink3,'font-weight':v===100?700:400}));});
  svg.appendChild(txt('ארצי = 100% (הקו המודגש)',{x:m.l+6,y:y(100)-13,fill:c.ink2,'font-size':11,'font-weight':700,'text-anchor':'start'}));
  svg.appendChild(txt('% מהשכר הממוצע הארצי',{x:m.l+6,y:m.t+10,fill:c.ink2,'font-size':11.5,'text-anchor':'start'}));
  ys.forEach((yr,i)=>svg.appendChild(txt(yr,{x:x(i),y:H-14,'text-anchor':'middle'})));
  series.forEach(([nm,vals,col])=>{
    const pts=vals.map((v,i)=>v==null?null:[x(i),y(v)]).filter(Boolean);
    svg.appendChild(el('path',{d:pts.map((p,i)=>(i?'L':'M')+p[0]+' '+p[1]).join(' '),fill:'none',
      stroke:col,'stroke-width':2.5,'stroke-linejoin':'round','stroke-linecap':'round'}));
    const last=pts[pts.length-1];
    svg.appendChild(el('circle',{cx:last[0],cy:last[1],r:4.5,fill:col,stroke:c.card,'stroke-width':2}));
  });
  ys.forEach((yr,i)=>{
    const g=el('g'); const r=el('rect',{x:x(i)-24,y:m.t,width:48,height:H-m.t-m.b,fill:'transparent'});
    g.appendChild(r);
    series.forEach(([nm,vals,col])=>{ if(vals[i]==null)return;
      g.appendChild(el('circle',{cx:x(i),cy:y(vals[i]),r:3.2,fill:col,opacity:.9}));});
    hover(g,`<b>${yr}</b>`+series.map(([nm,v,col])=>v[i]==null?'':
      `<i style="color:${col}">■</i> ${nm} <b style="display:inline;font-weight:700">${v[i]}%</b>`+
      (nm==='אשכול גליל מזרחי'?` <i>(${fmt(D.wage_abs['אשכול גליל מזרחי'][i])} ₪ · ארצי ${fmt(D.wage_abs['ארצי'][i])} ₪)</i>`:'')
      ).filter(Boolean).join('<br>'));
    svg.appendChild(g);});
  legend('lg1',[['אשכול גליל מזרחי',c.s1,1],['תל־אביב',c.s3,1],['מחוז הצפון',c.s4,1]]);
  table('t1',['שנה','מדד אשכול','מדד תל־אביב','מדד הצפון','שכר אשכול ₪','שכר ארצי ₪','רשויות באשכול'],
    ys.map((yr,i)=>[yr,D.idx_year['אשכול גליל מזרחי'][i]??'—',D.idx_year['תל־אביב'][i]??'—',
      D.idx_year['הצפון'][i]??'—',fmt(D.wage_abs['אשכול גליל מזרחי'][i]),fmt(D.wage_abs['ארצי'][i]),
      D.cluster.auth[i]]));
}

/* ---------- 2. one gap, two rulers: percent flat / shekels widening ---------- */
/* Two small multiples side by side (RTL: percent first, on the right), same mark,
   same color, same nine years — so "flat" and "rising" are read off identical
   geometry. Not one frame with two y-scales: a dual axis would let the reader
   blame the scales for the divergence, which is the whole finding. */
function chart2(){
  const c=S(),svg=clear('c2'); if(!svg)return;
  const W=1000,H=350,T=64,B=H-40;
  const ys=D.years, nat=D.wage_abs['ארצי'], eg=D.wage_abs['אשכול גליל מזרחי'],
        pct=ys.map((_,i)=>100*(nat[i]-eg[i])/nat[i]), gap=ys.map((_,i)=>nat[i]-eg[i]);
  function panel(x0,x1,vals,hi,ticks,title,sub,fmtv,fmtt){
    svg.appendChild(txt(title,{x:x1,y:T-30,'text-anchor':'end','font-size':13,'font-weight':700,fill:c.ink}));
    svg.appendChild(txt(sub,{x:x1,y:T-13,'text-anchor':'end','font-size':11,fill:c.ink3}));
    const y=v=>B-v*(B-T)/hi, step=(x1-x0)/ys.length, bw=step*0.62;
    ticks.forEach(v=>{
      svg.appendChild(el('line',{x1:x0,x2:x1,y1:y(v),y2:y(v),stroke:v?c.rule2:c.ink3,'stroke-width':v?1:1.5}));
      svg.appendChild(txt((fmtt||fmtv)(v),{x:x1+8,y:y(v),'text-anchor':'start','font-size':10.5,fill:c.ink3}));});
    vals.forEach((v,i)=>{
      const cx=x0+step*i+step/2;
      svg.appendChild(el('rect',{x:cx-bw/2,y:y(v),width:bw,height:y(0)-y(v),fill:c.s1,rx:3}));
      if(i===0||i===vals.length-1)
        svg.appendChild(txt(fmtv(v),{x:cx,y:y(v)-10,'text-anchor':'middle','font-size':11.5,
          'font-weight':700,fill:c.ink}));
      svg.appendChild(txt(ys[i],{x:cx,y:B+16,'text-anchor':'middle','font-size':9.5,fill:c.ink3}));
      const hit=el('rect',{x:cx-step/2,y:T-14,width:step,height:B-T+14,fill:'transparent'});
      hover(hit,`<b>${ys[i]}</b><i>הפער באחוזים</i> <b style="display:inline">${pct[i].toFixed(1)}%</b>`+
        `<i>הפער בשקלים</i> <b style="display:inline">${fmt(gap[i])} ש״ח</b>`+
        `<i>שכר ארצי / אשכול</i> ${fmt(nat[i])} / ${fmt(eg[i])} ש״ח`);
      svg.appendChild(hit);});
  }
  panel(560,948,pct,26,[0,10,20],'הפער באחוזים','כמה אחוזים חסרים לאשכול מהשכר הארצי',
        v=>v.toFixed(1)+'%', v=>v+'%');
  panel(52,440,gap,3000,[0,1000,2000,3000],'הפער בשקלים','אותו פער, במונחי שקלים לחודש',
        v=>fmt(Math.round(v)));
  svg.appendChild(el('line',{x1:498,x2:498,y1:T-34,y2:B+6,stroke:c.rule2}));
  table('t2',['שנה','שכר אשכול','שכר ארצי','הפער באחוזים','הפער בשקלים'],
    ys.map((yr,i)=>[yr,fmt(eg[i]),fmt(nat[i]),pct[i].toFixed(1)+'%',fmt(gap[i])]));
}

/* ---------- 3. income distribution: cluster vs national ---------- */
/* Paired bars per income group. A 100% stacked bar hides the thing that matters
   here — the group-by-group gap — so each group gets its own pair plus the
   explicit difference in percentage points. */
function chart3(){
  const c=S(),svg=clear('c3'); if(!svg)return;
  const W=1000,H=340,m={t:28,r:130,b:34,l:200};
  const keys=D.inc_rows, eg=D.inc['אשכול 2024'], nat=D.inc['ארצי 2024'];
  const hi=40, x=v=>m.l+v*(W-m.l-m.r)/hi, bh=(H-m.t-m.b)/keys.length;
  [0,10,20,30,40].forEach(v=>{
    svg.appendChild(el('line',{x1:x(v),x2:x(v),y1:m.t-8,y2:H-m.b,stroke:v?c.rule2:c.ink3,
      'stroke-width':v?1:1.5}));
    svg.appendChild(txt(v+'%',{x:x(v),y:H-18,'text-anchor':'middle','font-size':11}));});
  svg.appendChild(txt('הפרש בנק׳ אחוז',{x:W-m.r+118,y:m.t-16,'text-anchor':'end','font-size':10.5,
    fill:c.ink3}));
  svg.appendChild(txt('% מהמועסקים',{x:m.l+6,y:m.t-16,'text-anchor':'start','font-size':10.5,fill:c.ink3}));
  keys.forEach((k,i)=>{
    const y0=m.t+bh*i+4, h=(bh-14)/2, mid=y0+h+1;
    if(i)svg.appendChild(el('line',{x1:10,x2:W-10,y1:y0-5,y2:y0-5,stroke:c.rule2}));
    [[eg[i],c.s1,'אשכול גליל מזרחי'],[nat[i],c.s3,'ארצי']].forEach(([v,col,lab],j)=>{
      const yy=y0+j*(h+2);
      const b=el('rect',{x:m.l+1,y:yy,width:Math.max(1,x(v)-m.l-1),height:h,fill:col,rx:2});
      hover(b,`<b>${lab}</b><i>${k}</i> <b style="display:inline">${v}%</b> מהמועסקים`);
      svg.appendChild(b);
      svg.appendChild(txt(v.toFixed(1)+'%',{x:x(v)+7,y:yy+h/2,'text-anchor':'start','font-size':11,
        'font-weight':j?400:700,fill:j?c.ink3:c.ink}));});
    const d=+(eg[i]-nat[i]).toFixed(1);
    svg.appendChild(txt('('+sgn(d)+')',{x:W-m.r+118,y:mid,'text-anchor':'end','font-size':13,
      'font-weight':700,fill:d>0?c.s1:c.s3}));
    svg.appendChild(txt(k,{x:m.l-12,y:mid,'text-anchor':'end','font-size':12.5,fill:c.ink,
      'font-family':'Assistant,sans-serif','font-weight':600}));});
  legend('lg3',[['אשכול גליל מזרחי',c.s1],['ארצי',c.s3]]);
  table('t4',['קבוצת הכנסה','אשכול 2024','ארצי 2024','הפרש 2024','אשכול 2023','ארצי 2023'],
    keys.map((k,jx)=>[k,D.inc['אשכול 2024'][jx]+'%',D.inc['ארצי 2024'][jx]+'%',
                        sgn(+(D.inc['אשכול 2024'][jx]-D.inc['ארצי 2024'][jx]).toFixed(1)),
                        D.inc['אשכול 2023'][jx]+'%',D.inc['ארצי 2023'][jx]+'%']));
}

/* ---------- 4. shift-share, per industry ---------- */
/* Was a signed stacked bar on a reversed axis — two unknowns at once, and readers
   could not tell which segment was which. Now: magnitudes only, two plain bars per
   industry growing the same way, with the sign carried in the labels and the
   caption. Same paired-bar pattern as chart 3. */
function chart4(){
  const c=S(),svg=clear('c4'); if(!svg)return;
  const rows=D.shift, W=1000,rowH=44,m={t:38,r:104,b:30,l:250},H=m.t+rows.length*rowH+m.b;
  svg.setAttribute('viewBox','0 0 '+W+' '+H);
  const hi=Math.max(...rows.map(r=>Math.max(-r.mix,-r.pay)))*1.16;
  const x=v=>m.l+v*(W-m.l-m.r)/hi;
  [0,250,500,750,1000].forEach(v=>{ if(v>hi)return;
    svg.appendChild(el('line',{x1:x(v),x2:x(v),y1:m.t-10,y2:H-m.b,stroke:v?c.rule2:c.ink3,
      'stroke-width':v?1:1.5}));
    svg.appendChild(txt(v?'−'+fmt(v):'0',{x:x(v),y:H-14,'text-anchor':'middle','font-size':11}));});
  svg.appendChild(txt('ש״ח שהענף גורע מהשכר הממוצע באשכול',{x:m.l,y:m.t-20,'text-anchor':'start',
    'font-size':11,fill:c.ink3}));
  rows.forEach((r,i)=>{
    const y0=m.t+rowH*i+5, h=(rowH-16)/2;
    if(i)svg.appendChild(el('line',{x1:10,x2:W-10,y1:y0-5,y2:y0-5,stroke:c.rule2}));
    [[-r.mix,c.s1,'הרכב ענפי — יש כאן פחות מהענף הזה'],
     [-r.pay,c.s2,'שכר בתוך הענף — משלמים כאן פחות']].forEach(([v,col,lab],j)=>{
      const yy=y0+j*(h+2);
      const bar=el('rect',{x:m.l+1,y:yy,width:Math.max(1,x(v)-m.l-1),height:h,fill:col,rx:2});
      hover(bar,`<b>${r.name}</b><i>${lab}</i> <b style="display:inline">−${fmt(v)} ש״ח</b>`);
      svg.appendChild(bar);
      svg.appendChild(txt('−'+fmt(v),{x:x(v)+7,y:yy+h/2,'text-anchor':'start','font-size':11,
        'font-weight':j?400:700,fill:j?c.ink3:c.ink}));});
    svg.appendChild(txt(r.name,{x:m.l-14,y:y0+h-2,'text-anchor':'end','font-size':12.5,fill:c.ink,
      'font-family':'Assistant,sans-serif','font-weight':600}));
    svg.appendChild(txt(`${r.s_eg}% מהשכירים כאן · ${r.s_nat}% ארצית · משלם ${r.wr}%`,
      {x:m.l-14,y:y0+h+13,'text-anchor':'end','font-size':10.5,fill:c.ink3}));
    svg.appendChild(txt('−'+fmt(-(r.mix+r.pay)),{x:W-14,y:y0+rowH/2-6,
      'text-anchor':'end','font-size':12.5,'font-weight':700,fill:c.ink}));});
  svg.appendChild(txt('סה״כ',{x:W-14,y:m.t-20,'text-anchor':'end','font-size':11,fill:c.ink3}));
  legend('lg4',[['הרכב ענפי — יש כאן פחות מהענף הזה',c.s1],
                ['שכר בתוך הענף — משלמים כאן פחות',c.s2]]);
  table('t_c4',['ענף','% מהשכירים באשכול','% ארצית','שכר ביחס לארצי','הרכב ענפי','שכר בענף','סה״כ'],
    rows.map(r=>[r.name,r.s_eg+'%',r.s_nat+'%',r.wr+'%','−'+fmt(-r.mix),'−'+fmt(-r.pay),
                 '−'+fmt(-(r.mix+r.pay))]));
}

/* ---------- 5. authority dumbbell ---------- */
function chart5(){
  const c=S(),svg=clear('c5'); if(!svg)return;
  const rows=D.auth, W=1000,H=580,m={t:24,r:118,b:40,l:186};
  const lo=50,hi=125, x=v=>m.l+(v-lo)*(W-m.l-m.r)/(hi-lo), bh=(H-m.t-m.b)/rows.length;
  [50,60,70,80,90,100,110,120].forEach(v=>{
    svg.appendChild(el('line',{x1:x(v),x2:x(v),y1:m.t,y2:H-m.b,stroke:v===100?c.ink3:c.rule2,
      'stroke-width':v===100?1.5:1}));
    svg.appendChild(txt(v,{x:x(v),y:H-22,'text-anchor':'middle','font-size':11,
      fill:v===100?c.ink2:c.ink3,'font-weight':v===100?700:400}));});
  svg.appendChild(txt('ארצי = 100%',{x:x(100),y:m.t-2,'text-anchor':'middle','font-size':11,
    'font-weight':700,fill:c.ink2}));
  rows.forEach((r,i)=>{
    const yy=m.t+bh*i+bh/2;
    svg.appendChild(el('line',{x1:x(Math.min(r.idx,r.idxm)),x2:x(Math.max(r.idx,r.idxm)),y1:yy,y2:yy,
      stroke:c.rule,'stroke-width':3,'stroke-linecap':'round'}));
    [[r.idx,c.s1],[r.idxm,c.s2]].forEach(([v,col])=>{
      const d=el('circle',{cx:x(v),cy:yy,r:5.5,fill:col,stroke:c.card,'stroke-width':1.8});
      hover(d,`<b>${r.name}</b><i>מדד ממוצע</i> <b style="display:inline">${r.idx}</b> · `+
        `<i>מדד חציון</i> <b style="display:inline">${r.idxm}</b><br>`+
        `<i>${fmt(r.n)} מועסקים · ממוצע ${fmt(r.mean)} ₪ · חציון ${fmt(r.med)} ₪ · מקום ${r.rank} מתוך ${D.rank_of}</i>`);
      svg.appendChild(d);});
    svg.appendChild(txt(r.name,{x:m.l-14,y:yy-5,'text-anchor':'end','font-size':13,fill:c.ink,
      'font-family':'Assistant,sans-serif','font-weight':600}));
    svg.appendChild(txt(`${fmt(r.n)} מועסקים · מקום ${r.rank}`,{x:m.l-14,y:yy+9,'text-anchor':'end','font-size':10.5}));
    svg.appendChild(txt(`${fmt(r.mean)} ₪`,{x:W-m.r+12,y:yy,'font-size':11.5,fill:c.ink2,'font-weight':500}));});
  legend('lg5',[['מדד שכר ממוצע',c.s1],['מדד שכר חציוני',c.s2]]);
  table('t3',['רשות','מועסקים','ממוצע ₪','חציון ₪','מדד ממוצע','מדד חציון','מקום ארצי'],
    rows.map(r=>[r.name,fmt(r.n),fmt(r.mean),fmt(r.med),r.idx,r.idxm,r.rank+' / '+D.rank_of]));
}

/* ---------- 6. duration ---------- */
function chart6(){
  const c=S(),svg=clear('c6'); if(!svg)return;
  const W=520,H=300,m={t:16,r:16,b:52,l:46};
  const cols=['תל־אביב','ארצי','אשכול'], i12=D.dur_rows.indexOf('12 חודשים');
  const hi=80,y=v=>m.t+(hi-v)*(H-m.t-m.b)/hi, bw=(W-m.l-m.r)/cols.length;
  [0,20,40,60,80].forEach(v=>{svg.appendChild(el('line',{x1:m.l,x2:W-m.r,y1:y(v),y2:y(v),stroke:c.rule2}));
    svg.appendChild(txt(v+'%',{x:m.l-8,y:y(v),'text-anchor':'end','font-size':11}));});
  cols.forEach((k,i)=>{
    const v=D.dur[k][i12], cx=m.l+bw*i+bw/2, w=bw*0.46;
    const b=el('rect',{x:cx-w/2,y:y(v),width:w,height:y(0)-y(v),fill:k==='אשכול'?c.s1:c.ink3,rx:4});
    hover(b,`<b>${k}</b><i>עבדו 12 חודשים</i> <b style="display:inline">${v}%</b><br>`+
      `<i>ממוצע ${D.dur[k][D.dur_rows.length-1]} חודשי עבודה</i>`);
    svg.appendChild(b);
    svg.appendChild(txt(v.toFixed(1)+'%',{x:cx,y:y(v)-11,'text-anchor':'middle','font-size':12.5,'font-weight':700,fill:c.ink}));
    svg.appendChild(txt(k,{x:cx,y:H-30,'text-anchor':'middle','font-size':12,fill:c.ink2}));
    svg.appendChild(txt(D.dur[k][D.dur_rows.length-1]+' חוד׳ בממוצע',{x:cx,y:H-14,'text-anchor':'middle','font-size':10.5}));});
  legend('lg6',[['אשכול גליל מזרחי',c.s1],['השוואה',c.ink3]]);
}

/* ---------- 7. minimum wage lines ---------- */
function chart7(){
  const c=S(),svg=clear('c7'); if(!svg)return;
  const W=520,H=300,m={t:14,r:96,b:38,l:38};
  const pick=[['מסעדה',c.s3],['צפת',c.s1],['קרית שמונה',c.s4],['— כלל יישובי הארץ —',c.ink3]];
  const ys=D.mw_years, lo=25,hi=60;
  const x=i=>m.l+i*(W-m.l-m.r)/(ys.length-1), y=v=>m.t+(hi-v)*(H-m.t-m.b)/(hi-lo);
  [30,40,50,60].forEach(v=>{svg.appendChild(el('line',{x1:m.l,x2:W-m.r,y1:y(v),y2:y(v),stroke:c.rule2}));
    svg.appendChild(txt(v+'%',{x:m.l-6,y:y(v),'text-anchor':'end','font-size':11}));});
  ys.forEach((yr,i)=>{ if(i%2===0) svg.appendChild(txt(yr,{x:x(i),y:H-16,'text-anchor':'middle','font-size':10.5}));});
  const placed=[];
  pick.forEach(([nm,col])=>{
    const vals=D.mw[nm]; if(!vals)return;
    const pts=vals.map((v,i)=>v==null?null:[x(i),y(v)]).filter(Boolean);
    svg.appendChild(el('path',{d:pts.map((p,i)=>(i?'L':'M')+p[0]+' '+p[1]).join(' '),fill:'none',stroke:col,
      'stroke-width':nm.startsWith('—')?2:2.5,'stroke-dasharray':nm.startsWith('—')?'5 4':'','stroke-linecap':'round'}));
    const last=pts[pts.length-1];
    svg.appendChild(el('circle',{cx:last[0],cy:last[1],r:3.5,fill:col}));
    let ly=last[1];
    while(placed.some(p=>Math.abs(p-ly)<13)) ly+=13;   // keep end labels from stacking
    placed.push(ly);
    if(Math.abs(ly-last[1])>2)
      svg.appendChild(el('line',{x1:last[0]+4,x2:W-m.r+4,y1:last[1],y2:ly,stroke:col,'stroke-width':1,opacity:.5}));
    svg.appendChild(txt(nm.startsWith('—')?'כלל הארץ':nm,{x:W-m.r+8,y:ly,'font-size':11,fill:col,'font-weight':600}));
    pts.forEach((p,i)=>{const h=el('circle',{cx:p[0],cy:p[1],r:9,fill:'transparent'});
      hover(h,`<b>${nm.startsWith('—')?'כלל יישובי הארץ':nm} · ${ys[i]}</b><b style="display:inline">${vals[i]}%</b> עד שכר מינימום`);
      svg.appendChild(h);});});
  legend('lg7',pick.map(([nm,col])=>[nm.startsWith('—')?'כלל יישובי הארץ':nm,col,1]));
}

/* ---------- 8. employment change ---------- */
function chart8(){
  const c=S(),svg=clear('c8'); if(!svg)return;
  const W=1000,H=340,m={t:20,r:20,b:44,l:52};
  const ys=D.years.slice(1), keys=[['אשכול','אשכול',c.s1],['ארצי','ארצי',c.s2],['תל־אביב','תל־אביב',c.s3]];
  const lo=-6,hi=6, x=i=>m.l+i*(W-m.l-m.r)/ys.length, y=v=>m.t+(hi-v)*(H-m.t-m.b)/(hi-lo);
  const gw=(W-m.l-m.r)/ys.length;
  [-6,-4,-2,0,2,4,6].forEach(v=>{svg.appendChild(el('line',{x1:m.l,x2:W-m.r,y1:y(v),y2:y(v),
      stroke:v?c.rule2:c.ink3,'stroke-width':v?1:1.5}));
    svg.appendChild(txt(v+'%',{x:m.l-8,y:y(v),'text-anchor':'end','font-size':11}));});
  ys.forEach((yr,i)=>{
    svg.appendChild(txt(yr,{x:x(i)+gw/2,y:H-18,'text-anchor':'middle','font-size':11.5}));
    keys.forEach(([lab,k,col],j)=>{
      const v=D.workers_yoy[k][i+1]; if(v==null)return;
      const bw=gw*0.24, bx=x(i)+gw/2+(j-1)*(bw+3)-bw/2;
      const b=el('rect',{x:bx,y:Math.min(y(v),y(0)),width:bw,height:Math.max(2,Math.abs(y(v)-y(0))),fill:col,rx:3});
      hover(b,`<b>${lab} · ${yr}</b><b style="display:inline">${v>0?'+':''}${v}%</b> שינוי במספר המועסקים`);
      svg.appendChild(b);
      if(yr===2024)svg.appendChild(txt(sgn(v)+'%',{x:bx+bw/2,y:v<0?y(v)+15:y(v)-12-(j===2?13:0),
        'text-anchor':'middle','font-size':11,'font-weight':700,fill:col}));});});
  legend('lg8',keys.map(([lab,k,col])=>[lab,col]));
}


/* ---------- 9. composition effect: Δemployment vs Δmedian wage ---------- */
function chart9(){
  const c=S(),svg=clear('c9'); if(!svg)return;
  const W=1000,H=430,m={t:22,r:26,b:56,l:70}, P=D.prof;
  const xs=P.map(p=>p.dn), ys=P.map(p=>p.dm);
  const xlo=-24,xhi=4, ylo=0,yhi=24;
  const X=v=>m.l+(v-xlo)*(W-m.l-m.r)/(xhi-xlo), Y=v=>H-m.b-(v-ylo)*(H-m.t-m.b)/(yhi-ylo);
  for(let v=-24;v<=4;v+=4){svg.appendChild(el('line',{x1:X(v),x2:X(v),y1:m.t,y2:H-m.b,
      stroke:v===0?c.ink3:c.rule2,'stroke-width':v===0?1.5:1}));
    svg.appendChild(txt(v+'%',{x:X(v),y:H-m.b+18,'text-anchor':'middle','font-size':11}));}
  for(let v=0;v<=24;v+=4){svg.appendChild(el('line',{x1:m.l,x2:W-m.r,y1:Y(v),y2:Y(v),stroke:c.rule2}));
    svg.appendChild(txt(v+'%',{x:m.l-8,y:Y(v),'text-anchor':'end','font-size':11}));}
  svg.appendChild(txt('שינוי במספר המועסקים',{x:(m.l+W-m.r)/2,y:H-14,'text-anchor':'middle','font-size':12,fill:c.ink2}));
  svg.appendChild(txt('שינוי בשכר החציוני ↑',{x:m.l+10,y:H-m.b-14,'text-anchor':'start','font-size':12,fill:c.ink2}));
  // least-squares line over the 17 authorities
  const n=xs.length, mx=xs.reduce((a,b)=>a+b)/n, my=ys.reduce((a,b)=>a+b)/n;
  let sxy=0,sxx=0; for(let i=0;i<n;i++){sxy+=(xs[i]-mx)*(ys[i]-my);sxx+=(xs[i]-mx)**2;}
  const sl=sxy/sxx, ic=my-sl*mx;
  svg.appendChild(el('line',{x1:X(xlo),y1:Y(sl*xlo+ic),x2:X(xhi),y2:Y(sl*xhi+ic),
    stroke:c.ink3,'stroke-width':2,'stroke-dasharray':'6 5',opacity:.7}));
  P.forEach(p=>{
    const col=p.band?c.s2:c.s1;
    const d=el('circle',{cx:X(p.dn),cy:Y(p.dm),r:6,fill:col,stroke:c.card,'stroke-width':2});
    hover(d,`<b>${p.name}</b><i>מועסקים</i> <b style="display:inline">${p.dn>0?'+':''}${p.dn}%</b> · `+
      `<i>שכר חציוני</i> <b style="display:inline">+${p.dm}%</b><br><i>${fmt(p.n)} מועסקים ב-2024</i>`);
    svg.appendChild(d);});
  [['עג\'ר',8,-14],['קרית שמונה',10,-12],['מטולה',-4,-16],['צפת',10,14],['גולן',-8,16],['גליל עליון',12,-10]]
    .forEach(([nm,dx,dy])=>{const p=P.find(q=>q.name===nm); if(!p)return;
      svg.appendChild(txt(nm,{x:X(p.dn)+dx,y:Y(p.dm)+dy,'font-size':11.5,fill:c.ink,'font-weight':600,
        'font-family':'Assistant,sans-serif','text-anchor':dx<0?'end':'start'}));});
  svg.appendChild(txt('r = \u22120.96',{x:W-m.r-8,y:m.t+12,'text-anchor':'end','font-size':13,
    'font-weight':700,fill:c.ink2}));
  legend('lg9',[['רשויות קו העימות',c.s2],['שאר רשויות האשכול',c.s1]]);
}

/* ---------- 10. equality relative to what the wage level predicts ---------- */
function chart10(){
  const c=S(),svg=clear('c10'); if(!svg)return; const R=D.ratio;
  const W=1000,H=470,m={t:26,r:30,b:60,l:74};
  const xlo=40,xhi=175, ylo=44,yhi=92;
  const X=v=>m.l+(v-xlo)*(W-m.l-m.r)/(xhi-xlo), Y=v=>H-m.b-(v-ylo)*(H-m.t-m.b)/(yhi-ylo);
  for(let v=50;v<=175;v+=25){svg.appendChild(el('line',{x1:X(v),x2:X(v),y1:m.t,y2:H-m.b,stroke:c.rule2}));
    svg.appendChild(txt(v,{x:X(v),y:H-m.b+18,'text-anchor':'middle','font-size':11}));}
  for(let v=50;v<=90;v+=10){svg.appendChild(el('line',{x1:m.l,x2:W-m.r,y1:Y(v),y2:Y(v),stroke:c.rule2}));
    svg.appendChild(txt(v+'%',{x:m.l-8,y:Y(v),'text-anchor':'end','font-size':11}));}
  svg.appendChild(txt('מדד שכר ממוצע ברשות (ארצי = 100)',{x:(m.l+W-m.r)/2,y:H-16,'text-anchor':'middle','font-size':12,fill:c.ink2}));
  svg.appendChild(txt('חציון ÷ ממוצע — ככל שגבוה יותר, שוויוני יותר ↑',{x:m.l+10,y:m.t+12,'text-anchor':'start','font-size':11.5,fill:c.ink2}));
  // the other 324 authorities, as the national cloud
  R.others.forEach(([x,y])=>svg.appendChild(el('circle',{cx:X(x),cy:Y(y),r:2.6,fill:c.ink3,'fill-opacity':.28})));
  // national trend: what the wage level predicts
  const f=v=>R.intercept+R.slope*v;
  [[R.sd,'+1 ס״ת'],[-R.sd,'\u22121 ס״ת']].forEach(([d])=>
    svg.appendChild(el('line',{x1:X(xlo),y1:Y(f(xlo)+d),x2:X(xhi),y2:Y(f(xhi)+d),
      stroke:c.ink3,'stroke-width':1,'stroke-dasharray':'3 4',opacity:.45})));
  svg.appendChild(el('line',{x1:X(xlo),y1:Y(f(xlo)),x2:X(xhi),y2:Y(f(xhi)),stroke:c.ink2,'stroke-width':2.2}));
  svg.appendChild(txt('הקו הארצי: מה שמצופה מרמת השכר',{x:X(xhi)-6,y:Y(f(xhi))-10,'text-anchor':'end',
    'font-size':11.5,'font-weight':700,fill:c.ink2}));
  R.cluster.forEach(p=>{
    const col=p.resid>=2?c.up:(p.resid<=-2?c.down:c.mid);
    const d=el('circle',{cx:X(p.idx),cy:Y(p.ratio),r:6.5,fill:col,stroke:c.card,'stroke-width':2});
    hover(d,`<b>${p.name}</b><i>מדד שכר</i> <b style="display:inline">${p.idx}</b> · `+
      `<i>חציון/ממוצע</i> <b style="display:inline">${p.ratio}%</b><br>`+
      `<i>מצופה לרמת שכר זו: ${p.exp}% — חריגה של ${p.resid>0?'+':''}${p.resid} נק׳</i><br>`+
      `<i>${fmt(p.n)} מועסקים</i>`);
    svg.appendChild(d);});
  [['מסעדה',-14,20],["מג'דל שמס",26,20],['בוקעתא',-20,-12],['טובא-זנגריה',0,-14],
   ['ראש פינה',0,17],['גליל עליון',0,-14],['צפת',-6,-14],['קרית שמונה',0,-14]]
   .forEach(([nm,dx,dy])=>{const p=R.cluster.find(q=>q.name===nm); if(!p)return;
     svg.appendChild(txt(nm,{x:X(p.idx)+dx,y:Y(p.ratio)+dy,'text-anchor':'middle','font-size':11.5,
       fill:c.ink,'font-weight':600,'font-family':'Assistant,sans-serif'}));});
  legend('lg10',[['שוויונית מהמצופה (מעל +2 נק׳)',c.up],['כמצופה',c.mid],
                 ['פחות שוויונית מהמצופה (מתחת ‎−2 נק׳)',c.down],['341 הרשויות בארץ',c.ink3]]);
  table('t5',['רשות','מועסקים','מדד שכר','חציון/ממוצע','מצופה לרמה זו','חריגה (נק׳)'],
    R.cluster.map(p=>[p.name,fmt(p.n),p.idx,p.ratio+'%',p.exp+'%',(p.resid>0?'+':'')+p.resid]));
}

/* ---------- 11. knowledge share vs wage index ---------- */
function chart11(){
  const c=S(),svg=clear('c11'); if(!svg)return; const K=D.anaf.know;
  const W=1000,H=430,m={t:24,r:28,b:56,l:70};
  const xlo=0,xhi=12, ylo=55,yhi=112;
  const X=v=>m.l+(v-xlo)*(W-m.l-m.r)/(xhi-xlo), Y=v=>H-m.b-(v-ylo)*(H-m.t-m.b)/(yhi-ylo);
  for(let v=0;v<=12;v+=2){svg.appendChild(el('line',{x1:X(v),x2:X(v),y1:m.t,y2:H-m.b,stroke:c.rule2}));
    svg.appendChild(txt(v+'%',{x:X(v),y:H-m.b+18,'text-anchor':'middle','font-size':11}));}
  for(let v=60;v<=110;v+=10){svg.appendChild(el('line',{x1:m.l,x2:W-m.r,y1:Y(v),y2:Y(v),stroke:c.rule2}));
    svg.appendChild(txt(v,{x:m.l-8,y:Y(v),'text-anchor':'end','font-size':11}));}
  svg.appendChild(el('line',{x1:X(D.anaf.nat_know),x2:X(D.anaf.nat_know),y1:m.t,y2:H-m.b,
    stroke:c.ink3,'stroke-width':1.5,'stroke-dasharray':'5 4'}));
  svg.appendChild(txt('שיעור ארצי '+D.anaf.nat_know+'%',{x:X(D.anaf.nat_know)-8,y:m.t+12,
    'text-anchor':'end','font-size':11,'font-weight':600,fill:c.ink2}));
  svg.appendChild(el('line',{x1:m.l,x2:W-m.r,y1:Y(100),y2:Y(100),stroke:c.ink3,'stroke-width':1.5,'stroke-dasharray':'5 4'}));
  svg.appendChild(txt('שכר ארצי',{x:W-m.r-6,y:Y(100)-9,'text-anchor':'end','font-size':11,'font-weight':600,fill:c.ink2}));
  svg.appendChild(txt('חלק ענפי הידע מהשכירים',{x:(m.l+W-m.r)/2,y:H-14,'text-anchor':'middle','font-size':12,fill:c.ink2}));
  svg.appendChild(txt('מדד שכר (ארצי = 100) ↑',{x:m.l+10,y:H-m.b-14,'text-anchor':'start','font-size':12,fill:c.ink2}));
  const xs=K.map(k=>k.share), ys=K.map(k=>k.idx), n=xs.length;
  const mx=xs.reduce((a,b)=>a+b)/n,my=ys.reduce((a,b)=>a+b)/n;
  let sxy=0,sxx=0; for(let i=0;i<n;i++){sxy+=(xs[i]-mx)*(ys[i]-my);sxx+=(xs[i]-mx)**2;}
  const sl=sxy/sxx, ic=my-sl*mx;
  svg.appendChild(el('line',{x1:X(1.5),y1:Y(sl*1.5+ic),x2:X(9.8),y2:Y(sl*9.8+ic),
    stroke:c.ink3,'stroke-width':2,'stroke-dasharray':'6 5',opacity:.7}));
  K.forEach(k=>{
    const d=el('circle',{cx:X(k.share),cy:Y(k.idx),r:7,fill:c.s1,stroke:c.card,'stroke-width':2});
    hover(d,`<b>${k.name}</b><i>ענפי ידע</i> <b style="display:inline">${k.share}%</b> (${fmt(k.n)} שכירים) · `+
      `<i>מדד שכר</i> <b style="display:inline">${k.idx}</b><br><i>כיסוי הקובץ ${k.cov}%</i>`);
    svg.appendChild(d);
    svg.appendChild(txt(k.name,{x:X(k.share),y:Y(k.idx)-16,'text-anchor':'middle','font-size':11.5,
      fill:c.ink,'font-weight':600,'font-family':'Assistant,sans-serif'}));});
  svg.appendChild(txt('r = +0.74',{x:W-m.r-8,y:m.t+12,'text-anchor':'end','font-size':13,'font-weight':700,fill:c.ink2}));
  legend('lg11',[['רשות באשכול',c.s1]]);
  const HI=D.anaf.hi, by={};
  HI.forEach(h=>{(by[h.name]=by[h.name]||{})[h.anaf]=h;});
  const cols=['ייצור אלקטרוניקה','תכנות ושירותי מחשב','מחקר ופיתוח','שירותים פיננסיים'];
  table('t6',['רשות',...cols.map(x=>x+' — שכירים / % מהארצי')],
    Object.keys(by).sort((a,b)=>{const s=x=>cols.reduce((t,cc)=>t+(by[x][cc]?by[x][cc].n:0),0);return s(b)-s(a);})
      .map(nm=>[nm,...cols.map(cc=>by[nm][cc]?`${fmt(by[nm][cc].n)} · ${by[nm][cc].ratio}%`:'—')]));
}

/* ---------- 12. education wage by authority ---------- */
function chart12(){
  const c=S(),svg=clear('c12'); if(!svg)return; const E=D.anaf.edu;
  const W=1000,H=400,m={t:26,r:24,b:96,l:62}, natw=D.anaf.edu_nat;
  const hi=16500, y=v=>m.t+(hi-v)*(H-m.t-m.b)/hi, bw=(W-m.l-m.r)/E.length;
  [0,4000,8000,12000,16000].forEach(v=>{svg.appendChild(el('line',{x1:m.l,x2:W-m.r,y1:y(v),y2:y(v),stroke:c.rule2}));
    svg.appendChild(txt(fmt(v),{x:m.l-8,y:y(v),'text-anchor':'end','font-size':11}));});
  E.forEach((e,i)=>{
    const x=m.l+bw*i+bw*0.12, w=bw*0.76;
    const b=el('rect',{x,y:y(e.wage),width:w,height:y(0)-y(e.wage),fill:e.ratio<100?c.s3:c.s1,rx:3});
    hover(b,`<b>${e.name}</b><i>שכר בחינוך</i> <b style="display:inline">${fmt(e.wage)} ₪</b> (${e.ratio}% מהארצי)<br>`+
      `<i>${fmt(e.n)} שכירים · ${e.share}% מכלל שכירי הרשות</i>`);
    svg.appendChild(b);
    svg.appendChild(txt(fmt(e.n),{x:x+w/2,y:y(e.wage)-9,'text-anchor':'middle','font-size':9.5,fill:c.ink3}));
    svg.appendChild(txt(e.name,{x:x+w/2,y:H-m.b+10,'font-size':10.5,fill:c.ink2,
      'font-family':'Assistant,sans-serif','text-anchor':'end',
      transform:`rotate(-45 ${x+w/2} ${H-m.b+10})`}));});
  svg.appendChild(el('line',{x1:m.l,x2:W-m.r,y1:y(natw),y2:y(natw),stroke:c.s2,'stroke-width':2,'stroke-dasharray':'6 4'}));
  svg.appendChild(txt('שכר ארצי בענף '+fmt(natw)+' ₪',{x:m.l+6,y:y(natw)-10,'text-anchor':'start',
    'font-size':11.5,'font-weight':700,fill:c.s2}));
  legend('lg12',[['משלמת מעל הארצי בענף',c.s1],['משלמת מתחת לארצי',c.s3]]);
}

/* ---------- 13. per-authority: what each fix would be worth ---------- */
/* Third attempt. The first two drew the decomposition as contributions to a gap,
   which readers could not hold in mind. This anchors it in the wage people
   actually earn and builds up to the national standard, so each segment answers
   "how many shekels would this fix add". Identity: wage + fix_pay + fix_mix = standard. */
function chart13(){
  const c=S(),svg=clear('c13'); if(!svg)return; const A=D.anaf.ss2;
  const W=1000,rowH=46,m={t:52,r:150,b:34,l:118},H=m.t+A.length*rowH+m.b;
  svg.setAttribute('viewBox','0 0 '+W+' '+H);
  const hi=14000, x=v=>m.l+v*(W-m.l-m.r)/hi;
  [0,4000,8000,12000].forEach(v=>{
    svg.appendChild(el('line',{x1:x(v),x2:x(v),y1:m.t-12,y2:H-m.b,stroke:v?c.rule2:c.ink3,
      'stroke-width':v?1:1.5}));
    svg.appendChild(txt(v?fmt(v):'0',{x:x(v),y:H-14,'text-anchor':'middle','font-size':10.5}));});
  svg.appendChild(txt('ש״ח לחודש עבודה',{x:m.l,y:m.t-26,'text-anchor':'start','font-size':11,fill:c.ink3}));
  svg.appendChild(txt('התקן הארצי לתמהיל שלה',{x:W-m.r+140,y:m.t-26,'text-anchor':'end',
    'font-size':11,fill:c.ink3}));
  A.forEach((a,i)=>{
    const y0=m.t+rowH*i, y=y0+rowH/2-4, h=19;
    if(i)svg.appendChild(el('line',{x1:10,x2:W-10,y1:y0-2,y2:y0-2,stroke:c.rule2}));
    const base=el('rect',{x:x(0),y:y-h/2,width:x(a.wage)-x(0),height:h,fill:c.ink3,opacity:.55,rx:2});
    hover(base,`<b>${a.name}</b><i>השכר בפועל</i> <b style="display:inline">${fmt(a.wage)} ש״ח</b>`+
      `<i>התקן הארצי לתמהיל שלה</i> ${fmt(a.std)} ש״ח<i>כיסוי ענפי</i> ${a.cov}%`);
    svg.appendChild(base);
    // positive segments extend the bar; negative ones sit under it so they never
    // overlap the base bar's own label
    let acc=a.wage;
    [[a.fix_pay,c.s2,'לשלם כמו הארץ בענפים הקיימים'],
     [a.fix_mix,c.s1,'להחזיק את תמהיל הענפים הארצי']].forEach(([v,col,lab])=>{
      const x0=x(acc),x1=x(acc+v), neg=v<0;
      const yy=neg?y+h/2+7:y-h/2, hh=neg?7:h;
      const seg=el('rect',{x:Math.min(x0,x1),y:yy,width:Math.max(2,Math.abs(x1-x0)),
        height:hh,fill:col,rx:2});
      hover(seg,`<b>${a.name}</b><i>${lab}</i> <b style="display:inline">${neg?'−':'+'}${fmt(Math.abs(v))} ש״ח</b>`);
      svg.appendChild(seg);
      if(neg)
        svg.appendChild(txt('−'+fmt(-v),{x:Math.min(x0,x1)-6,y:yy+4,'text-anchor':'end',
          'font-size':10,'font-weight':700,fill:col}));
      else if(Math.abs(x1-x0)>46)
        svg.appendChild(txt('+'+fmt(v),{x:(x0+x1)/2,y,'text-anchor':'middle',
          'font-size':11,'font-weight':700,fill:'#fff'}));
      acc+=v;});
    // wage label at the START of the base bar: at the right-hand end it collides with
    // the standard tick whenever the authority already pays above the standard
    svg.appendChild(txt(fmt(a.wage),{x:x(0)+10,y,'text-anchor':'start','font-size':11.5,
      'font-weight':700,fill:'#fff'}));
    svg.appendChild(el('line',{x1:x(a.std),x2:x(a.std),y1:y-h/2-5,y2:y+h/2+5,stroke:c.ink,
      'stroke-width':2}));
    svg.appendChild(txt(fmt(a.std),{x:W-m.r+140,y:y-4,'text-anchor':'end','font-size':11.5,
      'font-weight':700,fill:c.ink}));
    svg.appendChild(txt(a.name,{x:m.l-12,y:y-4,'text-anchor':'end','font-size':12.5,fill:c.ink,
      'font-family':'Assistant,sans-serif','font-weight':600}));
    svg.appendChild(txt('כיסוי '+a.cov+'%',{x:m.l-12,y:y+12,'text-anchor':'end','font-size':10,
      fill:c.ink3}));});
  legend('lg13',[['השכר בפועל',c.ink3],['תוספת אילו שילמו כמו הארץ באותם ענפים',c.s2],
                 ['תוספת אילו היה תמהיל הענפים הארצי',c.s1]]);
  table('t7',['רשות','שכר בפועל','תוספת משכר בענפים','תוספת מתמהיל','התקן הארצי','כיסוי'],
    A.map(a=>[a.name,fmt(a.wage),(a.fix_pay<0?'−':'+')+fmt(Math.abs(a.fix_pay)),
              (a.fix_mix<0?'−':'+')+fmt(Math.abs(a.fix_mix)),fmt(a.std),a.cov+'%']));
}

/* ---------- 14. each authority against its socio-economic peers ---------- */
/* Dumbbell: hollow circle = the average of authorities in the same CBS
   socio-economic cluster, filled circle = this authority. The line between them
   is the finding. Sorted by the gap, worst first. */
function chart14(){
  const c=S(),svg=clear('c14'); if(!svg)return;
  const R=D.ses.rows, W=1000,rowH=24,m={t:34,r:210,b:26,l:64},H=m.t+R.length*rowH+m.b;
  svg.setAttribute('viewBox','0 0 '+W+' '+H);
  const lo=50,hi=125, x=v=>m.l+(v-lo)*(W-m.l-m.r)/(hi-lo);
  [50,60,70,80,90,100,110,120].forEach(v=>{
    svg.appendChild(el('line',{x1:x(v),x2:x(v),y1:m.t-10,y2:H-m.b,stroke:v===100?c.ink3:c.rule2,
      'stroke-width':v===100?1.5:1}));
    svg.appendChild(txt(v+'%',{x:x(v),y:m.t-18,'text-anchor':'middle','font-size':10.5}));});
  svg.appendChild(txt('ארצי',{x:x(100),y:H-10,'text-anchor':'middle','font-size':10.5,
    'font-weight':700,fill:c.ink2}));
  R.forEach((r,i)=>{
    const y=m.t+rowH*i+rowH/2, up=r.d>0, col=up?c.up:c.down;
    svg.appendChild(el('line',{x1:x(r.idx),x2:x(r.idx_p),y1:y,y2:y,stroke:col,
      'stroke-width':3,'stroke-linecap':'round'}));
    svg.appendChild(el('circle',{cx:x(r.idx_p),cy:y,r:4.6,fill:c.card,stroke:c.ink3,'stroke-width':2}));
    const dot=el('circle',{cx:x(r.idx),cy:y,r:4.6,fill:col});
    hover(dot,`<b>${r.name}</b><i>אשכול חברתי-כלכלי</i> ${r.ses} (מתוך 10)`+
      `<i>מדד השכר שלה</i> <b style="display:inline">${r.idx}%</b>`+
      `<i>ממוצע ${r.peers} רשויות באותו אשכול</i> <b style="display:inline">${r.idx_p}%</b>`+
      `<i>הפרש</i> <b style="display:inline">${sgn(r.d)} נק׳</b>`);
    svg.appendChild(dot);
    svg.appendChild(txt(r.name,{x:W-m.r+10,y,'text-anchor':'start','font-size':12,fill:c.ink}));
    svg.appendChild(txt('אשכול '+r.ses,{x:W-m.r+118,y,'text-anchor':'start','font-size':10.5,fill:c.ink3}));
    svg.appendChild(txt(sgn(r.d),{x:m.l-10,y,'text-anchor':'end','font-size':12,'font-weight':700,fill:col}));});
  legend('lg14',[['הרשות — מתחת לדומות לה',c.down],['הרשות — מעליהן',c.up],
    ['ממוצע הרשויות באותו אשכול חברתי-כלכלי',c.ink3]]);
  table('t14',['רשות','אשכול חב״כ','רשויות השוואה','מדד השכר שלה','ממוצע ההשוואה','הפרש'],
    R.map(r=>[r.name,r.ses,r.peers,r.idx+'%',r.idx_p+'%',sgn(r.d)]));
}

/* ---------- 15. distribution ends vs socio-economic peers ---------- */
/* Two panels, one shared scale, same row order: a bar of a given length means the
   same number of percentage points in both. Colour carries valence, because the
   two measures are "worse" in opposite directions. */
function chart15(){
  const c=S(),svg=clear('c15'); if(!svg)return;
  const R=D.ses.rows.slice().sort((a,b)=>b.d_minw-a.d_minw);
  const W=1000,rowH=24,T=64,B=T+R.length*rowH,H=B+40;
  svg.setAttribute('viewBox','0 0 '+W+' '+H);
  const lo=-7,hi=11, PW=390;
  const panels=[{x0:470,d:'d_minw',v:'minw',p:'minw_p',t:'עודף משתכרי שכר מינימום',
                 sub:'ימינה = יותר מהדומות לה',worse:d=>d>0},
                {x0:40, d:'d_top', v:'top', p:'top_p', t:'פער במשתכרים מעל פי שניים',
                 sub:'שמאלה = פחות מהדומות לה',worse:d=>d<0}];
  panels.forEach(pn=>{
    const x=v=>pn.x0+(v-lo)*PW/(hi-lo);
    svg.appendChild(txt(pn.t,{x:pn.x0+PW,y:T-34,'text-anchor':'end','font-size':13,
      'font-weight':700,fill:c.ink}));
    svg.appendChild(txt(pn.sub,{x:pn.x0+PW,y:T-18,'text-anchor':'end','font-size':11,fill:c.ink3}));
    [-5,0,5,10].forEach(v=>{
      svg.appendChild(el('line',{x1:x(v),x2:x(v),y1:T-8,y2:B,stroke:v?c.rule2:c.ink,
        'stroke-width':v?1:1.6}));
      svg.appendChild(txt(v?sgn(v).replace('.0',''):'0',{x:x(v),y:H-16,'text-anchor':'middle',
        'font-size':10,fill:c.ink3}));});
    R.forEach((r,i)=>{
      const d=r[pn.d], y=T+rowH*i+rowH/2, col=pn.worse(d)?c.down:c.up;
      const x0=x(0),x1=x(d), h=12;
      const bar=el('rect',{x:Math.min(x0,x1),y:y-h/2,width:Math.max(1.5,Math.abs(x1-x0)),
        height:h,fill:col,rx:2});
      hover(bar,`<b>${r.name}</b><i>אשכול חברתי-כלכלי</i> ${r.ses}`+
        `<i>היא</i> <b style="display:inline">${r[pn.v]}%</b>`+
        `<i>ממוצע ${r.peers} הרשויות באותו אשכול</i> <b style="display:inline">${r[pn.p]}%</b>`+
        `<i>הפרש</i> <b style="display:inline">${sgn(d)} נק׳</b>`);
      svg.appendChild(bar);
      svg.appendChild(txt(sgn(d),{x:x1+(d<0?-5:5),y,'text-anchor':d<0?'end':'start',
        'font-size':10,'font-weight':700,fill:c.ink2}));});
  });
  R.forEach((r,i)=>svg.appendChild(txt(r.name,{x:W-10,y:T+rowH*i+rowH/2,'text-anchor':'end',
    'font-size':11.5,fill:c.ink})));
  svg.appendChild(txt('הרשות',{x:W-10,y:T-18,'text-anchor':'end','font-size':11,fill:c.ink3}));
  legend('lg15',[['גרוע מהרשויות באותו אשכול חברתי-כלכלי',c.down],['טוב מהן',c.up]]);
  table('t15',['רשות','אשכול חב״כ','עד מינימום — היא','ההשוואה','הפרש',
               'מעל פי 2 — היא','ההשוואה','הפרש'],
    R.map(r=>[r.name,r.ses,r.minw+'%',r.minw_p+'%',sgn(r.d_minw),
              r.top+'%',r.top_p+'%',sgn(r.d_top)]));
}

/* ---------- 16. characterisation matrix: median wage x mean/median ratio ---------- */
/* Quadrants split on the MEDIAN Israeli authority, not on the national aggregate:
   the aggregate ratio (1.419) sits above 87% of authorities, so splitting there
   would leave two quadrants empty and say nothing. */
function chart16(){
  const c=S(),svg=clear('c16'); if(!svg)return; const SC=D.scatter;
  const W=1000,H=620,m={t:52,r:64,b:70,l:74};
  const xlo=5500,xhi=16000, ylo=1.10,yhi=1.52;
  const X=v=>m.l+(v-xlo)*(W-m.l-m.r)/(xhi-xlo), Y=v=>H-m.b-(v-ylo)*(H-m.t-m.b)/(yhi-ylo);
  const cx=SC.nat_med_auth, cy=SC.nat_ratio_auth;
  // faint tint on the quadrant that is bad on both axes
  svg.appendChild(el('rect',{x:X(xlo),y:Y(yhi),width:X(cx)-X(xlo),height:Y(cy)-Y(yhi),
    fill:c.down,opacity:.07}));
  [6000,8000,10000,12000,14000,16000].forEach(v=>{
    svg.appendChild(el('line',{x1:X(v),x2:X(v),y1:m.t,y2:H-m.b,stroke:c.rule2}));
    svg.appendChild(txt(fmt(v),{x:X(v),y:H-m.b+18,'text-anchor':'middle','font-size':10.5}));});
  [1.1,1.2,1.3,1.4,1.5].forEach(v=>{
    svg.appendChild(el('line',{x1:m.l,x2:W-m.r,y1:Y(v),y2:Y(v),stroke:c.rule2}));
    svg.appendChild(txt(v.toFixed(2),{x:m.l-10,y:Y(v),'text-anchor':'end','font-size':10.5}));});
  // background: the other 324 authorities
  SC.others.forEach(([mx,my])=>{ if(mx<xlo||mx>xhi||my<ylo||my>yhi)return;
    svg.appendChild(el('circle',{cx:X(mx),cy:Y(my),r:2.6,fill:c.ink3,opacity:.20}));});
  // quadrant reference lines
  svg.appendChild(el('line',{x1:X(cx),x2:X(cx),y1:m.t,y2:H-m.b,stroke:c.ink,'stroke-width':1.6,
    'stroke-dasharray':'6 4'}));
  svg.appendChild(el('line',{x1:m.l,x2:W-m.r,y1:Y(cy),y2:Y(cy),stroke:c.ink,'stroke-width':1.6,
    'stroke-dasharray':'6 4'}));
  svg.appendChild(txt('חציון השכר החציוני ב־341 הרשויות · '+fmt(cx)+' ש״ח',
    {x:X(cx)-8,y:m.t+12,'text-anchor':'end','font-size':10.5,'font-weight':700,fill:c.ink2}));
  svg.appendChild(txt('חציון היחס ב־341 הרשויות · '+cy.toFixed(2),
    {x:W-m.r-6,y:Y(cy)-7,'text-anchor':'end','font-size':10.5,'font-weight':700,fill:c.ink2}));
  [['שכר חציוני נמוך · פחות שוויוני',X(xlo)+10,Y(yhi)+16,'start',c.down],
   ['שכר חציוני גבוה · פחות שוויוני',W-m.r-10,Y(yhi)+16,'end',c.ink3],
   ['שכר חציוני נמוך · שוויוני יותר',X(xlo)+10,H-m.b-10,'start',c.ink3],
   ['שכר חציוני גבוה · שוויוני יותר',W-m.r-10,H-m.b-10,'end',c.up]]
    .forEach(([t,x,y,a,col])=>svg.appendChild(txt(t,{x,y,'text-anchor':a,'font-size':11,
      'font-weight':700,fill:col,opacity:.85})));
  const nmax=Math.max(...SC.rows.map(r=>r.n)), R=n=>7+19*Math.sqrt(n/nmax);
  const placed=[];
  SC.rows.slice().sort((a,b)=>b.n-a.n).forEach(r=>{
    const px=X(r.med),py=Y(r.ratio),rr=R(r.n);
    const bad=r.med<cx&&r.ratio>cy, good=r.med>=cx&&r.ratio<=cy;
    const col=bad?c.down:good?c.up:c.mid;
    const dot=el('circle',{cx:px,cy:py,r:rr,fill:col,opacity:.72,stroke:c.card,'stroke-width':1.5});
    hover(dot,`<b>${r.name}</b><i>שכר חציוני</i> <b style="display:inline">${fmt(r.med)} ש״ח</b>`+
      `<i>שכר ממוצע</i> ${fmt(r.mean)} ש״ח<i>יחס ממוצע/חציון</i> <b style="display:inline">${r.ratio}</b>`+
      `<i>יחס חציון/ממוצע</i> ${r.mm}%<i>מועסקים</i> ${fmt(r.n)}`);
    svg.appendChild(dot);
    let ly=py-rr-6, anchor='middle', lx=px;
    if(placed.some(q=>Math.abs(q.x-lx)<58&&Math.abs(q.y-ly)<13)) ly=py+rr+13;
    if(placed.some(q=>Math.abs(q.x-lx)<58&&Math.abs(q.y-ly)<13)){ lx=px+rr+7; ly=py+4; anchor='start'; }
    placed.push({x:lx,y:ly});
    svg.appendChild(txt(r.name,{x:lx,y:ly,'text-anchor':anchor,'font-size':10.5,
      'font-weight':600,fill:c.ink}));});
  svg.appendChild(txt('שכר חציוני לחודש עבודה, ש״ח',{x:W-m.r,y:H-14,'text-anchor':'end',
    'font-size':11,fill:c.ink3}));
  svg.appendChild(txt('↑ יחס ממוצע/חציון — גבוה = פחות שוויוני',{x:m.l,y:m.t-26,
    'text-anchor':'start','font-size':11,fill:c.ink3}));
  legend('lg16',[['נמוך ולא שוויוני',c.down],['גבוה ושוויוני',c.up],['ביניים',c.mid],
                 ['341 הרשויות בארץ',c.ink3]]);
  table('t16',['רשות','מועסקים','שכר חציוני','שכר ממוצע','ממוצע/חציון','חציון/ממוצע'],
    SC.rows.slice().sort((a,b)=>b.med-a.med).map(r=>
      [r.name,fmt(r.n),fmt(r.med),fmt(r.mean),r.ratio,r.mm+'%']));
}

/* ---------- 17. six industries, one panel each ---------- */
/* Small multiples: same geometry, same 100% reference, one industry per card, so
   the reader compares authorities inside an industry and industries against each
   other without re-learning the chart. */
function chart17(){
  const c=S();
  (D.anafpick||[]).forEach((p,k)=>{
    const svg=clear('c17_'+k); if(!svg)return;
    const rows=p.rows, rowH=16, W=340, m={t:16,r:46,b:22,l:92},
          H=m.t+rows.length*rowH+m.b;
    svg.setAttribute('viewBox','0 0 '+W+' '+H);
    const hi=Math.max(120,Math.ceil(Math.max(...rows.map(r=>r.ratio))/20)*20);
    const x=v=>m.l+v*(W-m.l-m.r)/hi;
    [0,50,100].forEach(v=>{ if(v>hi)return;
      svg.appendChild(el('line',{x1:x(v),x2:x(v),y1:m.t-6,y2:H-m.b,
        stroke:v===100?c.ink:c.rule2,'stroke-width':v===100?1.4:1,
        'stroke-dasharray':v===100?'4 3':''}));
      svg.appendChild(txt(v+'%',{x:x(v),y:H-8,'text-anchor':'middle','font-size':9.5,
        fill:v===100?c.ink2:c.ink3,'font-weight':v===100?700:400}));});
    rows.forEach((r,i)=>{
      const y=m.t+rowH*i+rowH/2, up=r.ratio>=100, col=up?c.up:c.down;
      const b=el('rect',{x:m.l,y:y-5,width:Math.max(1,x(r.ratio)-m.l),height:10,fill:col,rx:2});
      hover(b,`<b>${r.name}</b><i>${p.short}</i>`+
        `<i>שכר תושבי הרשות בענף</i> <b style="display:inline">${fmt(r.wage)} ש״ח</b>`+
        `<i>ארצי בענף</i> ${fmt(p.w_nat)} ש״ח<i>יחס</i> <b style="display:inline">${r.ratio}%</b>`+
        `<i>שכירים</i> ${fmt(r.n)}`);
      svg.appendChild(b);
      // value labels in a fixed right-hand column: next to the bar they collide with
      // the dashed 100% line whenever a ratio sits near it
      svg.appendChild(txt(r.ratio+'%',{x:W-6,y,'text-anchor':'end','font-size':9.5,
        'font-weight':up?700:400,fill:up?c.ink:c.ink3}));
      svg.appendChild(txt(r.name,{x:m.l-6,y,'text-anchor':'end','font-size':10,fill:c.ink}));});
  });
}

/* ---------- branch table ---------- */
function branchTable(){
  table('t2',['ענף','% מהמועסקים באשכול','% ארצית','שכר ארצי ₪','שכר באשכול ₪','יחס'],
    D.big.map(r=>[r.name,r.s_eg+'%',r.s_nat+'%',fmt(r.w_nat),fmt(r.w_eg),r.wr+'%']));
}

function drawAll(){ [chart1,chart2,chart3,chart4,chart5,chart6,chart7,chart8,chart9,chart10,chart11,chart12,chart13,chart14,chart15,chart16,chart17,branchTable]
  .forEach(f=>{try{f()}catch(e){console.error(f.name,e)}}); }
drawAll();
matchMedia('(prefers-color-scheme:dark)').addEventListener('change',drawAll);
new MutationObserver(drawAll).observe(document.documentElement,{attributes:true,attributeFilter:['data-theme']});
</script>
