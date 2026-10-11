/* Deterministic reporting rules: only explicitly reviewed, source-linked finals. */
(function(root, factory){
  const api=factory();
  if(typeof module==='object'&&module.exports) module.exports=api;
  if(root) root.WM_REPORT=api;
})(typeof window!=='undefined'?window:null,function(){
  'use strict';
  const COVERAGE=['Mountain Valley','Dirigo','Telstar','Buckfield','Oxford Hills','Gould Academy','Fryeburg Academy','Sacopee Valley','Poland Regional'];
  const SPORTS=['Football','Boys Soccer','Girls Soccer','Field Hockey','Volleyball','Girls Volleyball','Golf'];
  const ALIASES={
    'oxford hills comprehensive':'Oxford Hills','poland':'Poland Regional',
    'telstar regional':'Telstar','fryeburg':'Fryeburg Academy','gould':'Gould Academy',
    'oxford hills/buckfield coop':'Oxford Hills/Buckfield',
    'oxford hills/buckfield cooperative':'Oxford Hills/Buckfield',
  };
  const canonical=name=>{const clean=String(name??'').replace(/\s+/g,' ').trim();return ALIASES[clean.toLowerCase()]||clean;};
  const sportName=s=>({'Boys Soccer':"boys' soccer",'Girls Soccer':"girls' soccer",'Girls Volleyball':"girls' volleyball"}[s]||s.toLowerCase());
  function validDate(value){
    if(typeof value!=='string'||!/^\d{4}-\d{2}-\d{2}$/.test(value)) return false;
    const date=new Date(value+'T12:00:00Z');
    return !Number.isNaN(date.getTime())&&date.toISOString().slice(0,10)===value;
  }
  function todayISO(now=new Date()){
    const parts=new Intl.DateTimeFormat('en-US',{timeZone:'America/New_York',year:'numeric',month:'2-digit',day:'2-digit'}).formatToParts(now);
    const part=t=>parts.find(p=>p.type===t).value;
    return `${part('year')}-${part('month')}-${part('day')}`;
  }
  function dateLabel(iso,options={month:'long',day:'numeric',year:'numeric'}){
    return validDate(iso)?new Intl.DateTimeFormat('en-US',{...options,timeZone:'UTC'}).format(new Date(iso+'T12:00:00Z')):'Unknown date';
  }
  function safeURL(value,official=false){
    try{const u=new URL(value);return u.protocol==='https:'&&!u.username&&!u.password&&(!official||['mpa.cc','www.mpa.cc'].includes(u.hostname));}
    catch{return false;}
  }
  function coveredTeams(game){
    const names=[canonical(game.away),canonical(game.home)];
    const teams=COVERAGE.filter(t=>names.includes(t));
    if(game.sport==='Football'&&names.includes('Oxford Hills/Buckfield')) teams.push('Oxford Hills','Buckfield');
    if(['Volleyball','Girls Volleyball'].includes(game.sport)&&names.includes('Massabesic/Sacopee Coop')) teams.push('Sacopee Valley');
    return [...new Set(teams)];
  }
  const gameKey=g=>JSON.stringify([g.sport,g.dateISO,...[canonical(g.away),canonical(g.home)].sort()]);
  function invalidReason(g,asOf){
    if(!coveredTeams(g).length) return 'Outside WMR coverage';
    if(g.eventType&&g.eventType!=='game') return 'Meet results need separate team verification';
    if(g.exhibition||g.level&&g.level!=='Varsity') return 'Exhibition or non-varsity entry';
    if(!SPORTS.includes(g.sport)) return 'Sport needs separate result verification';
    if(!validDate(g.dateISO)||g.dateISO>asOf) return 'Invalid or future game date';
    if(g.dateRaw){const d=new Date(g.dateISO+'T12:00:00Z');if(g.dateRaw!==`${d.getUTCMonth()+1}.${d.getUTCDate()}.${d.getUTCFullYear()}`) return 'Conflicting game dates';}
    if(g.reviewNote||g.verification==='disputed') return g.reviewNote||'Disputed final score';
    if(/cancel|postpon|suspend/i.test(g.status||'')) return 'Game not confirmed complete';
    if(g.completed!==true) return 'Final score missing';
    if(![g.awayScore,g.homeScore].every(s=>Number.isSafeInteger(s)&&s>=0)) return 'Incomplete or invalid final score';
    if(g.verification!=='verified') return 'Final has not been reviewed';
    if(!validDate(g.resultVerifiedOn)||g.resultVerifiedOn>asOf||g.resultVerifiedOn<g.dateISO) return 'Result review date missing or invalid';
    if(!safeURL(g.sourceUrl)) return 'Result source link missing';
    return '';
  }
  const isVerifiedFinal=(g,asOf=todayISO())=>!invalidReason(g,asOf);
  const signature=g=>JSON.stringify([[canonical(g.away),g.awayScore],[canonical(g.home),g.homeScore]].sort((a,b)=>a[0].localeCompare(b[0])));
  function selectFinals(schedule,{start,end,sport='all',school='all',asOf=todayISO()}){
    const groups=new Map(),games=[],excluded=[];
    for(const g of schedule){
      if(!coveredTeams(g).length||g.dateISO<start||g.dateISO>end) continue;
      if(sport!=='all'&&g.sport!==sport) continue;
      if(school!=='all'&&!coveredTeams(g).includes(canonical(school))) continue;
      const key=gameKey(g);
      if(!groups.has(key)) groups.set(key,[]);
      groups.get(key).push(g);
    }
    for(const items of groups.values()){
      const finals=items.filter(g=>g.completed===true&&[g.awayScore,g.homeScore].every(s=>Number.isSafeInteger(s)&&s>=0));
      const conflicting=new Set(finals.map(signature)).size>1;
      const disputed=items.find(g=>g.verification==='disputed'||g.reviewNote&&/conflict|disput/i.test(g.reviewNote));
      const confirmed=items.find(g=>isVerifiedFinal(g,asOf));
      if(conflicting||disputed||!confirmed){
        const g=disputed||items[0];
        excluded.push({game:g,reason:conflicting?'Conflicting final scores; result withheld':invalidReason(g,asOf)||'Final has not been reviewed'});
        continue;
      }
      games.push({...confirmed,sourceUrls:[...new Set([confirmed.sourceUrl,...(confirmed.sourceUrls||[])].filter(u=>safeURL(u)))]});
    }
    const compare=(a,b)=>a.dateISO.localeCompare(b.dateISO)||(SPORTS.indexOf(a.sport)-SPORTS.indexOf(b.sport))||canonical(a.away).localeCompare(canonical(b.away))||canonical(a.home).localeCompare(canonical(b.home));
    games.sort(compare);excluded.sort((a,b)=>compare(a.game,b.game));
    return {games,excluded};
  }
  function outcome(g){
    const away=canonical(g.away),home=canonical(g.home);
    const covered=n=>COVERAGE.includes(n)||n==='Oxford Hills/Buckfield'||n==='Massabesic/Sacopee Coop';
    if(g.awayScore===g.homeScore) return {subject:covered(away)?away:home,opponent:covered(away)?home:away,tie:true,own:g.awayScore,other:g.homeScore};
    const awayWon=g.awayScore>g.homeScore;
    const winner=awayWon?away:home,loser=awayWon?home:away;
    const winScore=Math.max(g.awayScore,g.homeScore),loseScore=Math.min(g.awayScore,g.homeScore);
    return {subject:covered(winner)?winner:loser,opponent:covered(winner)?loser:winner,won:covered(winner),winScore,loseScore};
  }
  function spokenTeam(name){
    if(name==='Oxford Hills/Buckfield') return 'the Oxford Hills and Buckfield cooperative team';
    if(name==='Massabesic/Sacopee Coop') return 'the Massabesic and Sacopee Valley cooperative team';
    return name.replace(/^Mt\. /,'Mount ').replaceAll('/',' and ');
  }
  function resultSentence(g,narration=false,index=0){
    const o=outcome(g),day=dateLabel(g.dateISO,{weekday:'long'}),sport=sportName(g.sport);
    const a=narration?spokenTeam(o.subject):o.subject,b=narration?spokenTeam(o.opponent):o.opponent;
    if(!narration){
      if(o.tie) return `${a}, ${day}, tied ${b} in ${sport}, ${o.own}-${o.other}.`;
      return `${a}, ${day}, ${o.won?'defeated':'lost to'} ${b} in ${sport}, ${o.winScore}-${o.loseScore}.`;
    }
    const result=o.tie?(o.own===0?`${a} and ${b} finished in a scoreless tie`:`${a} and ${b} finished tied at ${o.own} apiece`):`${a} ${o.won?'defeated':'lost to'} ${b}, ${o.winScore} to ${o.loseScore}`;
    const open=index===0?`In ${sport} on ${day}`:index%2?`Also ${day} in ${sport}`:`In another ${sport} game on ${day}`;
    return `${open}, ${result}.`;
  }
  function generate(data,options){
    const {start,end}=options;
    if(!validDate(start)||!validDate(end)) return {error:'Choose a valid start and end date.',written:'',narration:'',games:[],excluded:[]};
    if(start>end) return {error:'Start date must be on or before end date.',written:'',narration:'',games:[],excluded:[]};
    const selected=selectFinals(data.schedule,options);
    if(!selected.games.length) return {...selected,error:'',written:'',narration:''};
    const range=start===end?dateLabel(start):`${dateLabel(start,start.slice(0,4)===end.slice(0,4)?{month:'long',day:'numeric'}:undefined)} through ${dateLabel(end)}`;
    const captured=dateLabel(data.meta.checked);
    const written=['Western Maine Report — Weekly Sports Results',range,`Source snapshot: ${captured}. Confirmed finals only.`, ''];
    const narration=[`Here are the confirmed local high school sports results for ${range}. These results come from the ${captured} snapshot.`];
    const days=[...new Set(selected.games.map(g=>g.dateISO))];
    for(const day of days){
      written.push(dateLabel(day,{weekday:'long',month:'long',day:'numeric',year:'numeric'}));
      const dayGames=selected.games.filter(g=>g.dateISO===day);
      for(const sport of [...new Set(dayGames.map(g=>g.sport))]){
        written.push(sport);
        const games=dayGames.filter(g=>g.sport===sport);
        written.push(...games.map(g=>resultSentence(g)), '');
        narration.push(games.map((g,i)=>resultSentence(g,true,i)).join(' '));
      }
    }
    return {...selected,error:'',written:written.join('\n').trim(),narration:narration.join('\n\n')};
  }
  function standingsRows(rows,{sport='all',school='all'}={}){
    const selected=rows.filter(s=>(sport==='all'||s.sport===sport)&&(school==='all'||s.team===canonical(school)||s.team==='Massabesic/Sacopee Coop'&&canonical(school)==='Sacopee Valley'));
    const seen=new Set();
    return selected.filter(s=>{const key=JSON.stringify([s.standingTeam||s.team,s.sport,s.classification,s.region,s.checked]);if(seen.has(key))return false;seen.add(key);return true;});
  }
  function playoffText(s,asOf=todayISO()){
    const p=s.playoff;
    if(!p||p.confirmed!==true||!p.status||!safeURL(p.sourceUrl,true)||!validDate(p.checked)||p.checked>asOf||p.seed!=null&&(!Number.isSafeInteger(p.seed)||p.seed<1)) return 'Not confirmed';
    return `${p.status}${p.seed!=null?`; confirmed seed ${p.seed}`:''} (captured ${dateLabel(p.checked)})`;
  }
  return {COVERAGE,SPORTS,canonical,coveredTeams,validDate,todayISO,dateLabel,safeURL,invalidReason,isVerifiedFinal,gameKey,selectFinals,resultSentence,generate,standingsRows,playoffText};
});
