/* app.js — Western Maine 2026 Fall Sports Dashboard */
(function(){
  const D = window.WM_DATA;
  const R = window.WM_REPORT;
  const $ = (s,r=document)=>r.querySelector(s);
  const $$ = (s,r=document)=>[...r.querySelectorAll(s)];
  const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const today=R.todayISO();
  const final=g=>R.isVerifiedFinal(g,today);
  const scheduled=g=>!g.completed&&R.validDate(g.dateISO)&&g.dateISO>=today&&!g.reviewNote&&!/cancel|postpon|suspend/i.test(g.status||'');
  const sourceLink=(url,label='Source ↗')=>R.safeURL(url)?`<a class="src-link" href="${esc(url)}" target="_blank" rel="noopener">${esc(label)}</a>`:'';
  async function copyText(area,status,message){
    status.textContent='';
    try{
      if(!navigator.clipboard?.writeText) throw new Error('Clipboard unavailable');
      await navigator.clipboard.writeText(area.value);
      status.textContent=message;
    }catch{
      area.hidden=false;area.focus();area.select();
      try{if(document.execCommand('copy')){status.textContent=message;return;}}catch{}
      status.textContent=' Text selected. Press Ctrl+C (Command+C on Mac), or use your device’s Copy command.';
    }
  }

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
  function sportChip(s){const c=sportColor(s);return `<span class="sport-chip"><span class="sw" style="background:${c}"></span>${esc(sportShort(s))}</span>`;}

  /* ---- Meta / KPIs ---- */
  $('#genDate').textContent=D.meta.generated;
  $('#updatedLabel').textContent='Snapshot '+D.meta.checked;
  $('#coverageNote').textContent=D.meta.coverageNote;
  $('#standUpdated').textContent='Captured '+R.dateLabel(D.standings.lastUpdated);

  const official=R.standingsRows(D.standings.rows).filter(s=>s.status==='Verified MPA snapshot');
  const kpis=[
    {v:D.schedule.filter(final).length,l:'Confirmed finals',s:'Reviewed scores; disputed results withheld'},
    {v:D.schedule.filter(scheduled).length,l:'Next listed games',s:'Confirm changes with schools'},
    {v:D.teams.length,l:'Coverage schools',s:'WMR local coverage',accent:true},
    {v:official.length||'Pending',l:'Official MPA rankings',s:official.length?'Captured '+R.dateLabel(D.standings.lastUpdated)+' · not live':'MPA verification required'},
  ];
  $('#kpiGrid').innerHTML=kpis.map(k=>`<div class="kpi"><div class="v ${k.accent?'accent':''}">${k.v}</div><div class="l">${k.l}</div><div class="s">${k.s}</div></div>`).join('');

  /* ---- Key matchups (Oxford Hills + Fryeburg pinned) ---- */
  const matchups=D.schedule.filter(scheduled).sort((a,b)=>a.dateISO.localeCompare(b.dateISO)||timeMinutes(a.time)-timeMinutes(b.time)).slice(0,8);
  $('#matchupGrid').innerHTML=matchups.map(g=>`
    <div class="matchup pinned" style="border-left-color:${sportColor(g.sport)}">
      <div class="tag">${esc(g.date)} · ${esc(g.time)}</div>
      <div class="teams">${esc(g.away)} <span class="vs">${g.venueKnown===true?'at':'vs.'}</span> ${esc(g.home)}</div>
      <div class="meta">${sportChip(g.sport)} ${sourceLink(g.sourceUrl)}</div>
    </div>`).join('')||'<p>No upcoming games verified in this snapshot.</p>';

  /* ---- Schedule table ---- */
  const tbody=$('#schedBody');
  let sortKey='date', sortDir=1, activeSport='All', searchTerm='', westOnly=false, gameStatus='upcoming';

  const SPORTS_ALL=['All',...Object.keys(SPORT_META)];
  $('#sportChips').innerHTML=SPORTS_ALL.map(s=>`<button class="chip${s==='All'?' active':''}" data-sport="${s}" aria-pressed="${s==='All'}">${s}</button>`).join('');
  $$('#sportChips .chip').forEach(c=>c.addEventListener('click',()=>{
    activeSport=c.dataset.sport;
    $$('#sportChips .chip').forEach(x=>{x.classList.toggle('active',x===c);x.setAttribute('aria-pressed',String(x===c));});
    renderSched();
  }));
  $('#resultFilter').addEventListener('change',e=>{gameStatus=e.target.value;sortDir=gameStatus==='completed'?-1:1;renderSched();});
  $('#teamSearch').addEventListener('input',e=>{searchTerm=e.target.value.toLowerCase();renderSched();});
  $('#westOnly').addEventListener('change',e=>{westOnly=e.target.checked;renderSched();});
  $('#sortSelect').addEventListener('change',e=>{sortKey=e.target.value;renderSched();});

  function dateSortVal(g){return R.validDate(g.dateISO)?Date.parse(g.dateISO+'T12:00:00Z'):0;}
  function timeMinutes(t){
    const text=String(t||'').toLowerCase().trim();if(text==='noon')return 720;if(text==='midnight')return 0;
    const m=text.match(/^(\d{1,2})(?::(\d{2}))?\s*(am|pm)$/);if(!m||+m[1]>12||+m[1]<1||+(m[2]||0)>59)return 1440;
    return (+m[1]%12+(m[3]==='pm'?12:0))*60+ +(m[2]||0);
  }

  function filtered(){
    return D.schedule.filter(g=>{
      if(!R.coveredTeams(g).length) return false;
      if(gameStatus==='upcoming'&&!scheduled(g)) return false;
      if(gameStatus==='completed'&&!final(g)) return false;
      if(gameStatus==='pending'&&(final(g)||g.dateISO>today&&!g.reviewNote&&g.verification!=='disputed')) return false;
      if(activeSport!=='All'&&g.sport!==activeSport) return false;
      if(westOnly&&g.region!=='Western ME') return false;
      if(searchTerm){
        const displayTeams=D.teams.filter(t=>R.coveredTeams(g).includes(t.name)).map(t=>t.displayName||t.name);
        const hay=(g.away+' '+g.home+' '+g.sport+' '+(g.location||'')+' '+displayTeams.join(' ')+' '+((g.participants||[]).join(' '))).toLowerCase();
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
      else if(sortKey==='time') v=timeMinutes(a.time)-timeMinutes(b.time);
      else v=String(a[sortKey]).localeCompare(String(b[sortKey]));
      return (v||dateSortVal(a)-dateSortVal(b)||timeMinutes(a.time)-timeMinutes(b.time)||String(a.away).localeCompare(String(b.away)))*sortDir;
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
      const src=sourceLink(g.sourceUrl,'↗ source');
      let regionCell=esc(g.region||'—');
      if(isMeet){
        const shown=ct.slice(0,5).join(', ')+(ct.length>5?` +${ct.length-5} more`:"");
        regionCell=`${esc(g.region||'—')} <span class="meet-tag">${esc(g.meetInfo||'')}</span><div class="meet-teams">${esc(shown)}</div>${src}`;
      } else {
        regionCell=`${esc(g.region||'—')}${src?` <br>${src}`:''}`;
      }
      if(g.reviewNote) regionCell+=`<div class="meet-teams">${esc(g.reviewNote)}</div>`;
      if(g.verification==='disputed') regionCell+=' '+(g.sourceUrls||[]).filter(u=>u!==g.sourceUrl).map(u=>sourceLink(u,'↗ other source')).join(' ');
      const at=g.location&&!isMeet?`<span class="loc-sub">${esc(g.location)}</span>`:'';
      const confirmed=final(g);
      const status=confirmed?'Final · reviewed':g.verification==='disputed'?'Disputed · withheld':g.completed?'Unverified · withheld':g.reviewNote?'Review pending':g.dateISO<=today?'Result pending':esc(g.time);
      return `<tr class="${pin?'pinned-row':''}${isMeet?' meet-row':''}">
        <td>${esc(g.date)}</td>
        <td>${sportChip(g.sport)}</td>
        <td class="teams-cell">${esc(g.away)}</td>
        <td style="font-variant-numeric:tabular-nums">${confirmed?`${g.awayScore}–${g.homeScore}`:g.completed?'Withheld':g.venueKnown===true?'at':'vs.'}</td>
        <td class="teams-cell">${esc(g.home)}${at?`<br>${at}`:''}</td>
        <td>${status}</td>
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

  $('#athGrid').innerHTML=D.teams.map(t=>`<div class="ath"><div class="name">${esc(t.displayName||t.name)}</div><div class="note">${D.schedule.filter(g=>R.coveredTeams(g).includes(t.name)).length} source-linked entries</div></div>`).join('');

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
  const schoolOptions=D.teams.map(t=>`<option value="${esc(t.name)}">${esc(t.displayName||t.name)}</option>`).join('');
  $('#standSchool').insertAdjacentHTML('beforeend',schoolOptions);
  function renderStandings(){
    const sport=$('#standSport').value||'all';
    const school=$('#standSchool').value||'all';
    const rows=R.standingsRows(D.standings.rows,{sport,school});
    $('#standCopyStatus').textContent='';
    $('#standBody').innerHTML=rows.map(s=>{
      const rank=s.status==='Verified MPA snapshot'&&R.safeURL(s.sourceUrl,true)?sourceLink(s.sourceUrl,'No. '+s.rank+' ↗'):esc(s.rank);
      const playoff=R.playoffText(s,today);
      const playoffCell=playoff==='Not confirmed'?playoff:esc(playoff)+' '+sourceLink(s.playoff.sourceUrl);
      return `<tr><td class="team">${esc(s.standingTeam||s.team)}</td><td>${esc(s.sport)}</td><td>${esc(s.classification)} / ${esc(s.region)}</td><td>${rank}</td><td>${esc(s.record)}</td><td>${esc(s.checked)}</td><td>${esc(s.status)}${s.standingTeam?'<br>Supplied MPA record differs from score listings; review pending.':''}</td><td>${playoffCell}</td><td>${esc(s.latest)}</td></tr>`;
    }).join('')||'<tr class="empty-row"><td colspan="9">No standings captured for these filters.</td></tr>';
    const verified=rows.filter(s=>s.status==='Verified MPA snapshot');
    $('#standBrief').value=verified.length?verified.map(s=>`In MPA standings captured ${R.dateLabel(s.checked)}, ${s.standingTeam||s.team} ranked No. ${s.rank} in ${s.sport}, ${s.classification==='8 Person'?'8-person':s.classification.includes('8 Man')?s.classification:'Class '+s.classification} ${s.region}, with a ${s.record} record.`).join('\n\n')+(verified.some(s=>s.standingTeam)?'\n\nThe supplied Oxford Hills/Buckfield football record differs from the score listings and remains under review.':'')+'\n\nThese are historical rankings, not live standings or confirmed playoff seeds.':rows.some(s=>s.team==='Gould Academy')?'Gould Academy follows separate prep-school standings. No verified prep-school rank or full-season record is available in this snapshot.':`No official MPA rankings were captured for these filters in the ${R.dateLabel(D.meta.checked)} snapshot. Missing results are not losses.`;
  }
  renderStandings();
  $('#standSport').addEventListener('change',renderStandings);
  $('#standSchool').addEventListener('change',renderStandings);
  $('#copyStandBrief').addEventListener('click',()=>copyText($('#standBrief'),$('#standCopyStatus'),' Update copied.'));

  /* ---- Weekly report generator ---- */
  $('#reportSchool').insertAdjacentHTML('beforeend',schoolOptions);
  $('#reportSport').insertAdjacentHTML('beforeend',R.SPORTS.map(s=>`<option>${esc(s)}</option>`).join(''));
  const reportEnd=R.validDate(D.meta.checked)&&D.meta.checked<today?D.meta.checked:today;
  const reportStart=new Date(reportEnd+'T12:00:00Z');reportStart.setUTCDate(reportStart.getUTCDate()-6);
  $('#reportStart').value=reportStart.toISOString().slice(0,10);
  $('#reportEnd').value=reportEnd;
  function clearReports(){
    $('#reportWritten').value='';$('#reportNarration').value='';
    $('#copyReportWritten').disabled=true;$('#copyReportNarration').disabled=true;
    $('#writtenCopyStatus').textContent='';$('#narrationCopyStatus').textContent='';
    $('#reportSources').innerHTML='';$('#reportOmitted').innerHTML='';
    $('#reportSourcesSummary').textContent='Sources for included finals';
    $('#reportOmittedSummary').textContent='Omitted games needing review';
  }
  function generateReports(){
    clearReports();
    const report=R.generate(D,{start:$('#reportStart').value,end:$('#reportEnd').value,sport:$('#reportSport').value,school:$('#reportSchool').value,asOf:today});
    if(report.error){$('#reportStatus').textContent=report.error;return;}
    $('#reportWritten').value=report.written;$('#reportNarration').value=report.narration;
    $('#copyReportWritten').disabled=!report.written;$('#copyReportNarration').disabled=!report.narration;
    $('#reportStatus').textContent=(report.games.length?`${report.games.length} confirmed final${report.games.length===1?'':'s'} included.`:'No confirmed final scores in this date range and these filters.')+` ${report.excluded.length} entr${report.excluded.length===1?'y':'ies'} omitted. Source snapshot: ${R.dateLabel(D.meta.checked)}.`+($('#reportEnd').value>D.meta.checked?' Results after the source snapshot have not been checked.':'');
    $('#reportSourcesSummary').textContent=`Sources for ${report.games.length} included finals`;
    $('#reportOmittedSummary').textContent=`${report.excluded.length} omitted games needing review`;
    $('#reportSources').innerHTML=report.games.map(g=>`<div class="log-item"><b>${esc(g.date)} · ${esc(g.sport)}</b><br>${esc(g.away)} ${g.awayScore}–${g.homeScore} ${esc(g.home)}<br>Result reviewed ${esc(g.resultVerifiedOn)} · ${g.sourceUrls.map(u=>sourceLink(u)).join(' · ')}</div>`).join('')||'<p class="update-note">No finals included.</p>';
    $('#reportOmitted').innerHTML=report.excluded.map(({game:g,reason})=>`<div class="log-item"><b>${esc(g.date)} · ${esc(g.sport)} · ${esc(g.away)} vs. ${esc(g.home)}</b><br>${esc(reason)}<br>${[...new Set([g.sourceUrl,...(g.sourceUrls||[])])].map(u=>sourceLink(u)).join(' · ')}</div>`).join('')||'<p class="update-note">No additional listed games omitted for these dates and filters. The source listings may be incomplete.</p>';
  }
  $('#reportForm').addEventListener('submit',e=>{e.preventDefault();generateReports();});
  ['reportStart','reportEnd','reportSport','reportSchool'].forEach(id=>$('#'+id).addEventListener('change',()=>{clearReports();$('#reportStatus').textContent='Selection changed. Generate reports to refresh the text.';}));
  $('#copyReportWritten').addEventListener('click',()=>copyText($('#reportWritten'),$('#writtenCopyStatus'),' Written report copied.'));
  $('#copyReportNarration').addEventListener('click',()=>copyText($('#reportNarration'),$('#narrationCopyStatus'),' Narration copied.'));
  generateReports();

  /* ---- Update center: log (in-memory) ---- */
  let logEntries=[...D.updateLog];
  function renderLog(){
    $('#logList').innerHTML=logEntries.length?logEntries.map(l=>`<div class="log-item"><b>${esc(l.week)}</b> — ${esc(l.date)}<br>${esc(l.summary)}</div>`).join(''):'<div class="log-item" style="color:var(--color-text-faint)">No entries yet.</div>';
  }
  renderLog();
  $('#addLogBtn').addEventListener('click',()=>{
    const label=$('#wkLabel').value.trim()||'Week '+(logEntries.length+1);
    const summary=$('#wkSummary').value.trim()||'(no summary entered)';
    logEntries.unshift({week:label,date:new Date().toLocaleDateString('en-US',{month:'short',day:'numeric',year:'numeric'}),summary});
    renderLog();
    $('#wkLabel').value='';$('#wkSummary').value='';
  });
  $('#copyDataBtn').addEventListener('click',()=>{
    $('#dataTemplate').value=JSON.stringify([{team:'VERIFY COVERAGE TEAM',sport:'VERIFY SPORT',classification:'VERIFY CLASS',region:'VERIFY REGION',rank:null,record:'VERIFY W-L-T',checked:'YYYY-MM-DD',sourceUrl:'https://www.mpa.cc/TournamentCentralRankings.aspx',sourceNote:'Record the official table and capture date before publication.'}],null,2);
    return copyText($('#dataTemplate'),$('#templateCopyStatus'),' Standings template copied. Replace placeholders after source verification.');
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
    <div class="src-item">${sourceLink(s.url,s.name)}<span class="u">${esc(s.use)}</span></div>`).join('');

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

