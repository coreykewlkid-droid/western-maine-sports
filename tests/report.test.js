/* Synthetic fixtures here are tests only; they are never published as games. */
const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const R=require('../js/report.js');
const fixture=(changes={})=>({sport:'Boys Soccer',dateISO:'2026-10-05',dateRaw:'10.5.2026',date:'Oct 5, 2026',away:'Telstar',home:'Gould Academy',awayScore:3,homeScore:2,completed:true,eventType:'game',verification:'verified',resultVerifiedOn:'2026-10-06',sourceUrl:'https://school.example/results',...changes});
const data=games=>({meta:{checked:'2026-10-10'},schedule:games});
const options={start:'2026-10-05',end:'2026-10-10',asOf:'2026-10-11'};

test('Inclusive dates, chronological days, and day/sport grouping in both versions',()=>{
  const report=R.generate(data([fixture({dateISO:'2026-10-10',dateRaw:'10.10.2026',resultVerifiedOn:'2026-10-10',sport:'Football'}),fixture()]),options);
  assert.equal(report.games.length,2);
  assert(report.written.indexOf('Monday, October 5')<report.written.indexOf('Saturday, October 10'));
  assert.match(report.written,/Telstar, Monday, defeated Gould Academy in boys' soccer, 3-2\./);
  assert.match(report.narration,/boys' soccer on Monday, Telstar defeated Gould Academy, 3 to 2/);
  assert.match(report.narration,/football on Saturday/);
  assert.match(report.narration,/October 10, 2026 snapshot/);
});
test('Never report missing, unreviewed, disputed, non-varsity, exhibition, future, incomplete or source-free finals',()=>{
  for(const changes of [
    {completed:false},{verification:'pending'},{verification:'disputed'},
    {reviewNote:'Conflicting official scores'},{awayScore:null},{homeScore:'2'},
    {awayScore:-1},{awayScore:true},{sourceUrl:''},{sourceUrl:'javascript:alert(1)'},
    {resultVerifiedOn:'2026-10-12'},{resultVerifiedOn:undefined},
    {dateISO:'2026-10-12',dateRaw:'10.12.2026'},
    {dateRaw:'10.6.2026'},{level:'JV'},{exhibition:true},{eventType:'meet'},
    {sport:'Cross Country'},{status:'Postponed'},{away:'Hebron Academy',home:'Hyde School'},
  ]){
    const report=R.generate(data([fixture(changes)]),{...options,end:'2026-10-15'});
    assert.equal(report.games.length,0,JSON.stringify(changes));
    assert.equal(report.written,'');assert.equal(report.narration,'');
  }
});
test('Deduplicates reversed teams and withholds conflicting scores regardless of review marker',()=>{
  const reversed=fixture({away:'Gould Academy',home:'Telstar',awayScore:2,homeScore:3});
  assert.equal(R.generate(data([fixture(),reversed,fixture({completed:false,verification:'pending'})]),options).games.length,1);
  const disputed=R.generate(data([fixture(),{...reversed,awayScore:4,verification:'pending'}]),options);
  assert.equal(disputed.games.length,0);assert.match(disputed.excluded[0].reason,/Conflicting/);
});
test('A local loss leads with the local team, and tied scores are not wins or losses',()=>{
  const loss=R.resultSentence(fixture({away:'Hyde School',home:'Gould Academy',awayScore:8,homeScore:1}),true);
  assert.match(loss,/Gould Academy lost to Hyde School, 8 to 1/);
  const tie=R.resultSentence(fixture({awayScore:0,homeScore:0}),true);
  assert.match(tie,/scoreless tie/);assert.doesNotMatch(tie,/defeated|lost to/);
});
test('Exactly nine covered schools; shared football game is included once for either school',()=>{
  assert.equal(R.COVERAGE.length,9);
  const coop=fixture({sport:'Football',away:'Oxford Hills/Buckfield',home:'Lewiston',awayScore:35,homeScore:6});
  for(const school of ['Oxford Hills','Oxford Hills Comprehensive','Buckfield']){
    const report=R.generate(data([coop,coop]),{...options,school});
    assert.equal(report.games.length,1);
    assert.match(report.narration,/Oxford Hills and Buckfield cooperative team/);
  }
  assert.equal(R.generate(data([coop]),{...options,school:'Telstar'}).games.length,0);
});
test('Rejects impossible dates and reversed ranges; New York dates cross midnight correctly',()=>{
  assert.equal(R.validDate('2026-02-30'),false);
  assert.equal(R.generate(data([fixture()]),{...options,start:'2026-10-12'}).games.length,0);
  assert.match(R.generate(data([]),{start:'',end:''}).error,/valid/);
  assert.equal(R.todayISO(new Date('2026-10-11T03:59:00Z')),'2026-10-10');
  assert.equal(R.todayISO(new Date('2026-10-11T04:01:00Z')),'2026-10-11');
});
test('Routine reports ignore all athlete and descriptive metadata',()=>{
  const d={...data([fixture({athlete:'TEST ATHLETE',summary:'TEST QUOTATION'})]),athletes:[{name:'TEST ATHLETE'}]};
  const report=R.generate(d,options);
  assert.doesNotMatch(report.written+report.narration,/TEST ATHLETE|TEST QUOTATION/);
});
test('Rank does not imply a berth or seed; confirmations require dated official evidence',()=>{
  assert.equal(R.playoffText({rank:1,record:'10-0'}),'Not confirmed');
  const playoff={confirmed:true,status:'Qualified',seed:2,checked:'2026-10-10',sourceUrl:'https://www.mpa.cc/brackets'};
  assert.match(R.playoffText({playoff},'2026-10-11'),/confirmed seed 2/);
  for(const changes of [{confirmed:false},{sourceUrl:'https://mpa.cc.evil.example/brackets'},{checked:'2026-10-12'},{seed:0}]){
    assert.equal(R.playoffText({playoff:{...playoff,...changes}},'2026-10-11'),'Not confirmed');
  }
});
test('Standings collapse the cooperative entry, while Gould remains outside MPA ranks',()=>{
  const common={sport:'Football',standingTeam:'Oxford Hills/Buckfield Coop',classification:'A',region:'North',checked:'2026-10-10'};
  const rows=[{...common,team:'Buckfield'},{...common,team:'Oxford Hills'}];
  assert.equal(R.standingsRows(rows).length,1);
  assert.equal(R.standingsRows(rows,{school:'Oxford Hills Comprehensive'}).length,1);
});
test('Published snapshot retains every MPA rank/record/date and quarantines the conflicting Gould result',()=>{
  const c={window:{}};vm.runInNewContext(fs.readFileSync(require.resolve('../js/data.js'),'utf8'),c);
  const d=c.window.WM_DATA,standings=JSON.parse(fs.readFileSync(require.resolve('../standings_verified.json'),'utf8'));
  for(const expected of standings){
    const s=d.standings.rows.find(s=>s.team===expected.team&&s.sport===expected.sport);
    for(const key of ['rank','record','checked','sourceUrl','classification','region']) assert.equal(s[key],expected[key]);
  }
  const g=d.schedule.find(g=>g.sport==='Boys Soccer'&&g.dateISO==='2026-10-07'&&g.away==='Gould Academy');
  assert.equal(g.awayScore,1);assert.equal(g.homeScore,8);assert.equal(g.verification,'disputed');
  assert.equal(R.isVerifiedFinal(g,'2026-10-11'),false);
  const report=R.generate(d,{...options,start:'2026-09-01'});
  assert(!report.games.some(x=>R.gameKey(x)===R.gameKey(g)));
  assert(report.excluded.some(x=>R.gameKey(x.game)===R.gameKey(g)));
});
