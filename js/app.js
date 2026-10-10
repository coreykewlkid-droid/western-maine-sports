/* app.js — Western Maine 2026 Fall Sports Dashboard */
(function(){
  const D = window.WM_DATA;
  const $ = (s,r=document)=>r.querySelector(s);
  const $$ = (s,r=document)=>[...r.querySelectorAll(s)];
  const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const today=new Intl.DateTimeFormat('en-CA',{timeZone:'America/New_York',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date());

  /* ---- Theme toggle ---- */
  (function(){
    const t=$('[data-theme-toggle]'), r=document.documentElement;
    let d=matchMedia('(prefers-color-scheme:dark)').matches?'dark':'light';
    r.setAttribute('data-theme',d);
    function icon(d){
      return d==='dark'
        ? '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="5"/><path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/></svg>'
        : '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>';
    }
    t.innerHTML=icon(d); t.setAttribute('aria-label','Switch to '+(d==='dark'?'light':'dark')+' mode');
    t.addEventListener('click',()=>{
      d=d==='dark'?'light':'dark';
      r.setAttribute('data-theme',d); t.innerHTML=icon(d);
      t.setAttribute('aria-label','Switch to '+(d==='dark'?'light':'dark')+' mode');
    });
  })();

  /* ---- Sport styling ---- */
  const SPORT_META={
    "Football":   {varName:'--sport-football', short:'FB'},
    "Boys Soccer":{varName:'--sport-bsoccer', short:'B-SOC'},
    "Girls Soccer":{varName:'--sport-gsoccer', short:'G-SOC'},
    "Field Hockey":{varName:'--sport-fhockey',short:'FH'},
    "Cross Country":{varName:'--sport-xc', short:'XC'},
    "Volleyball": {varName:'--sport-volleyball', short:'VB'},
    "Golf":       {varName:'--sport-golf', short:'GOLF'},
  };
  function sportColor(s){return `var(${SPORT_META[s]?.varName||'--color-primary'})`;}
  function sportShort(s){return SPORT_META[s]?.short||s;}
  function sportChip(s){const c=sportColor(s);return `<span class="sport-chip"><span class="sw" style="background:${c}"></span>${sportShort(s)}</span>`;}

  /* ---- Meta / KPIs ---- */
  $('#genDate').textContent=D.meta.generated;
  $('#updatedLabel').textContent='Data checked '+D.meta.checked;
  $('#coverageNote').textContent=D.meta.coverageNote;
  $('#standUpdated').textContent=D.standings.lastUpdated;

  const _dates=D.schedule.map(g=>{const m=g.dateRaw.split('.');return new Date(+m[2],+m[0]-1,+m[1]).getTime();}).filter(t=>!isNaN(t));
  const _fmt=t=>new Date(t).toLocaleDateString('en-US',{month:'short',day:'numeric',year:'numeric'});
  const _range=_dates.length?`${_fmt(Math.min(..._dates))} – ${_fmt(Math.max(..._dates))}`:'';
  const kpis=[
    {v:D.schedule.filter(g=>g.completed).length,l:'Reported scores',s:'Final scores supplied by linked sources'},
    {v:D.schedule.filter(g=>!g.completed&&g.dateISO>=today&&!g.reviewNote).length,l:'Next listed games',s:'Confirm changes with schools'},
    {v:D.teams.length,l:'Coverage schools',s:'WMR local coverage',accent:true},
    {v:'Pending',l:'Official rankings',s:'MPA verification required'},
  ];
  $('#kpiGrid').innerHTML=kpis.map(k=>`<div class="kpi"><div class="v ${k.accent?'accent':''}">${k.v}</div><div class="l">${k.l}</div><div class="s">${k.s}</div></div>`).join('');

  /* ---- Key matchups (Oxford Hills + Fryeburg pinned) ---- */
  const matchups=D.schedule.filter(g=>!g.completed&&g.dateISO>=today&&!g.reviewNote).slice(0,8);
  $('#matchupGrid').innerHTML=matchups.map(g=>`
    <div class="matchup pinned" style="border-left-color:${sportColor(g.sport)}">
      <div class="tag">${esc(g.date)} · ${esc(g.time)}</div>
      <div class="teams">${esc(g.away)} <span class="vs">at</span> ${esc(g.home)}</div>
      <div class="meta">${sportChip(g.sport)} <a class="src-link" href="${esc(g.sourceUrl)}" target="_blank" rel="noopener">Source ↗</a></div>
    </div>`).join('')||'<p>No upcoming games verified in this snapshot.</p>';

  /* ---- Schedule table ---- */
  const tbody=$('#schedBody');
  let sortKey='date', sortDir=1, activeSport='All', searchTerm='', westOnly=false, gameStatus='upcoming';

  const SPORTS_ALL=['All',...Object.keys(SPORT_META)];
  $('#sportChips').innerHTML=SPORTS_ALL.map(s=>`<button class="chip${s==='All'?' active':''}" data-sport="${s}">${s}</button>`).join('');
  $$('#sportChips .chip').forEach(c=>c.addEventListener('click',()=>{
    activeSport=c.dataset.sport;
    $$('#sportChips .chip').forEach(x=>x.classList.toggle('active',x===c));
    renderSched();
  }));
  $('#resultFilter').addEventListener('change',e=>{gameStatus=e.target.value;sortDir=gameStatus==='completed'?-1:1;renderSched();});
  $('#teamSearch').addEventListener('input',e=>{searchTerm=e.target.value.toLowerCase();renderSched();});
  $('#westOnly').addEventListener('change',e=>{westOnly=e.target.checked;renderSched();});
  $('#sortSelect').addEventListener('change',e=>{sortKey=e.target.value;renderSched();});

  function dateSortVal(g){const m=g.dateRaw.split('.');return new Date(+m[2],+m[0]-1,+m[1]).getTime();}
  function timeHour(t){const m=t.match(/(\d+)(?::(\d+))?\s*(am|pm)?/i);if(!m)return 99;let h=+m[1];const ap=(m[3]||'').toLowerCase();if(ap==='pm'&&h!==12)h+=12;if(ap==='am'&&h===12)h=0;return h;}

  function filtered(){
    return D.schedule.filter(g=>{
      if(gameStatus==='upcoming'&&(g.completed||g.dateISO<today||g.reviewNote)) return false;
      if(gameStatus==='completed'&&!g.completed) return false;
      if(gameStatus==='pending'&&(g.completed||g.dateISO>today)) return false;
      if(activeSport!=='All'&&g.sport!==activeSport) return false;
      if(westOnly&&g.region!=='Western ME') return false;
      if(searchTerm){
        const hay=(g.away+' '+g.home+' '+g.sport+' '+(g.location||'')+' '+((g.coveredTeams||[]).join(' '))+' '+((g.participants||[]).join(' '))).toLowerCase();
        if(!hay.includes(searchTerm)) return false;
      }
      return true;
    });
  }
  function sorted(list){
    const arr=[...list];
    arr.sort((a,b)=>{
      let v=0;
      if(sortKey==='date') v=dateSortVal(a)-dateSortVal(b);
      else if(sortKey==='time') v=timeHour(a.time)-timeHour(b.time);
      else v=String(a[sortKey]).localeCompare(String(b[sortKey]));
      return v*sortDir;
    });
    return arr;
  }
  function renderSched(){
    const list=sorted(filtered());
    $('#schedCount').textContent=list.length+' items';
    if(!list.length){tbody.innerHTML='<tr class="empty-row"><td colspan="7">No games match your filters.</td></tr>';return;}
    const FOCUS=D.teams.map(t=>t.name);
    tbody.innerHTML=list.map(g=>{
      const isMeet=g.eventType==='meet';
      const ct=g.coveredTeams||[];
      const pin=FOCUS.some(t=>g.away.includes(t)||g.home.includes(t)||ct.includes(t))&&activeSport==='All'&&!searchTerm;
      const src=g.sourceUrl?`<a class="src-link" href="${g.sourceUrl}" target="_blank" rel="noopener" title="${g.source||'Source'}">↗ source</a>`:'';
      let regionCell=g.region||'—';
      if(isMeet){
        const shown=ct.slice(0,5).join(', ')+(ct.length>5?` +${ct.length-5} more`:"");
        regionCell=`${g.region||'—'} <span class="meet-tag">${g.meetInfo||''}</span><div class="meet-teams">${shown}</div>${src}`;
      } else {
        regionCell=`${g.region||'—'}${src?` <br>${src}`:''}`;
      }
      if(g.reviewNote) regionCell+=`<div class="meet-teams">${esc(g.reviewNote)}</div>`;
      const at=g.location&&!isMeet?`<span class="loc-sub">${g.location}</span>`:'';
      return `<tr class="${pin?'pinned-row':''}${isMeet?' meet-row':''}">
        <td>${g.date}</td>
        <td>${sportChip(g.sport)}</td>
        <td class="teams-cell">${esc(g.away)}</td>
        <td style="font-variant-numeric:tabular-nums">${g.completed?`${g.awayScore}–${g.homeScore}`:"at"}</td>
        <td class="teams-cell">${esc(g.home)}${at?`<br>${at}`:''}</td>
        <td>${g.completed?"Final":g.dateISO<today?"Result pending":esc(g.time)}</td>
        <td class="loc-cell">${regionCell}</td>
      </tr>`;
    }).join('');
    // header arrow indicators
    $$('#schedTable thead th').forEach(th=>{
      const k=th.dataset.sort;
      th.classList.toggle('sorted',k===sortKey);
      const ar=$('.arrow',th);
      if(ar) ar.textContent = k===sortKey ? (sortDir>0?'▾':'▴') : '';
    });
  }
  // header click sorting
  $$('#schedTable thead th[data-sort]').forEach(th=>{
    th.addEventListener('click',()=>{
      const k=th.dataset.sort;
      if(sortKey===k) sortDir*=-1; else {sortKey=k;sortDir=1;}
      $('#sortSelect').value=k;
      renderSched();
    });
  });
  renderSched();

  $('#athGrid').innerHTML=D.teams.map(t=>`<div class="ath"><div class="name">${esc(t.name)}</div><div class="note">${D.schedule.filter(g=>g.coveredTeams?.includes(t.name)).length} source-linked entries</div></div>`).join('');

  /* ---- Realignments ---- */
  const REALIGN_KEYS=[
    ['football','Football'],
    ['fieldHockey','Field Hockey'],
    ['soccer','Soccer'],
    ['crossCountry','Cross Country'],
    ['volleyball','Volleyball'],
  ];
  let activeRealign='football';
  function renderRealign(){
    $('#realignTabs').innerHTML=REALIGN_KEYS.map(([k,label])=>`<button class="chip${k===activeRealign?' active':''}" data-rk="${k}">${label}</button>`).join('');
    $$('#realignTabs .chip').forEach(c=>c.addEventListener('click',()=>{activeRealign=c.dataset.rk;renderRealign();}));
    const r=D.realignments[activeRealign];
    const html=`
      <div style="margin-bottom:var(--space-3)">
        <div class="cutoffs" style="display:inline-block;margin-right:var(--space-4)">Enrollment cutoffs: ${r.cutoffs}</div>
        <span style="font-size:var(--text-xs);color:var(--color-text-muted)">${r.season}</span>
      </div>
      ${r.changes?.length?`<ul class="changes-list" style="margin-bottom:var(--space-5)">${r.changes.map(c=>`<li>${c}</li>`).join('')}</ul>`:''}
      <div class="realign-grid">
        ${r.classes.map(c=>`
          <div class="realign-card">
            <h4>${c.class}</h4>
            <div class="realign-class"><span class="cls">${c.class}</span><span class="reg">${c.region}</span><span class="tm">${c.teams}</span></div>
          </div>`).join('')}
      </div>`;
    $('#realignContent').innerHTML=html;
  }
  renderRealign();

  /* ---- Standings ---- */
  $('#standNote').textContent=D.standings.note;
  function statusClass(s){
    const t=s.toLowerCase();
    if(t.includes('in ')||t.includes('clinched')||t.includes('contender')) return 'in';
    if(t.includes('bubble')) return 'bubble';
    if(t.includes('out')) return 'out';
    return 'preseason';
  }
  $('#standBody').innerHTML=D.standings.rows.map(s=>`
    <tr><td class="team">${esc(s.team)}</td><td>${esc(s.sport)}</td><td>${esc(s.rank)}</td><td>${esc(s.record)}</td><td>${esc(s.status)}</td><td>${esc(s.latest)}</td></tr>`).join('');

  /* ---- Update center: log (in-memory) ---- */
  let logEntries=[...D.updateLog];
  function renderLog(){
    $('#logList').innerHTML=logEntries.length?logEntries.map(l=>`<div class="log-item"><b>${l.week}</b> — ${l.date}<br>${l.summary}</div>`).join(''):'<div class="log-item" style="color:var(--color-text-faint)">No entries yet.</div>';
  }
  renderLog();
  $('#addLogBtn').addEventListener('click',()=>{
    const label=$('#wkLabel').value.trim()||'Week '+(logEntries.length+1);
    const summary=$('#wkSummary').value.trim()||'(no summary entered)';
    logEntries.unshift({week:label,date:new Date().toLocaleDateString('en-US',{month:'short',day:'numeric',year:'numeric'}),summary});
    renderLog();
    $('#wkLabel').value='';$('#wkSummary').value='';
  });
  $('#copyDataBtn').addEventListener('click',async()=>{
    const tpl=`{
  "lastUpdated": "WEEK DATE (e.g. Sep 10, 2026 — Week 1)",
  "rows": [
    {"team":"Telstar","sport":"Boys Soccer","class":"VERIFY CLASS","region":"VERIFY REGION","rank":"OFFICIAL RANK","record":"W-L-T","sourceUrl":"OFFICIAL URL"}
  ],
  "note":"Replace preseason outlook with computed MPA Heal Point standings. Verify at mpa.cc."
}`;
    try{await navigator.clipboard.writeText(tpl);alert('Standings data template copied to clipboard.');}
    catch(e){prompt('Copy this template:',tpl);}
  });
  $('#downloadLogBtn').addEventListener('click',()=>{
    const blob=new Blob([JSON.stringify({generated:D.meta.generated,logEntries},null,2)],{type:'application/json'});
    const url=URL.createObjectURL(blob);
    const a=document.createElement('a');
    a.href=url;a.download='western-maine-update-log.json';a.click();
    URL.revokeObjectURL(url);
  });

  /* ---- Sources ---- */
  $('#sourcesList').innerHTML=D.sources.map(s=>`
    <div class="src-item"><a href="${s.url}" target="_blank" rel="noopener">${s.name}</a><span class="u">${s.use}</span></div>`).join('');

  /* ---- Sidebar active link on scroll ---- */
  const navLinks=$$('#nav a');
  navLinks.forEach(a=>a.addEventListener('click',()=>{
    navLinks.forEach(x=>x.classList.toggle('active',x===a));
  }));
  const sections=navLinks.map(a=>$(a.getAttribute('href'))).filter(Boolean);
  const obs=new IntersectionObserver(es=>{
    es.forEach(e=>{if(e.isIntersecting){
      navLinks.forEach(a=>a.classList.toggle('active',a.getAttribute('href')==='#'+e.target.id));
    }});
  },{root:$('.main'),threshold:0.4,rootMargin:'-20% 0px -50% 0px'});
  sections.forEach(s=>obs.observe(s));
})();
