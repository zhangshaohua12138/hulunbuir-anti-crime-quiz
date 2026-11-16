import fs from 'node:fs';
const screens=[
  ['01-home','01-home.html','活动首页'],
  ['02-rules','02-rules.html','活动规则'],
  ['03-quiz','03-quiz.html','答题页 · 单选'],
  ['04-quiz-multi','04-quiz-multi.html','答题页 · 多选'],
  ['05-result','05-result.html','结果页 · 达标'],
  ['06-result','06-result.html','结果页 · 未达标'],
  ['07-lottery','07-lottery.html','抽奖页'],
  ['08-ranking','08-ranking.html','排行榜'],
  ['09-awards','09-awards.html','我的奖品'],
  ['10-modal-screen','10-modal-screen.html','领奖信息登记']
];
const targets=await (await fetch('http://127.0.0.1:9228/json')).json();
const ws=new WebSocket(targets.find(t=>t.type==='page').webSocketDebuggerUrl);
await new Promise(r=>ws.addEventListener('open',r,{once:true}));let seq=0;const pending=new Map();const errors=[];
ws.addEventListener('message',({data})=>{const x=JSON.parse(data);if(x.id){pending.get(x.id)?.(x);pending.delete(x.id);}if(x.method==='Runtime.exceptionThrown')errors.push(x.params.exceptionDetails.text);});
function send(method,params={}){return new Promise((resolve,reject)=>{const id=++seq;pending.set(id,x=>x.error?reject(x.error):resolve(x.result));ws.send(JSON.stringify({id,method,params}));});}
async function evaluate(expression){const r=await send('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true});if(r.exceptionDetails)throw new Error(JSON.stringify(r.exceptionDetails));return r.result.value;}
async function waitFor(expression,timeout=8000){const end=Date.now()+timeout;while(Date.now()<end){if(await evaluate(expression))return;await new Promise(r=>setTimeout(r,80));}throw new Error('Timeout '+expression);}
await send('Runtime.enable');await send('Page.enable');await send('Emulation.setDeviceMetricsOverride',{width:375,height:812,deviceScaleFactor:2,mobile:true});await send('Emulation.setScrollbarsHidden',{hidden:true});
const outDir='static/prototype/screens';fs.mkdirSync(outDir,{recursive:true});
const report=[];
for(const [name,file,title] of screens){
  const url='http://127.0.0.1:8080/static/prototype/'+file;
  await send('Page.navigate',{url});await waitFor("document.querySelector('.site-header')!==null");await new Promise(r=>setTimeout(r,450));
  const metrics=await evaluate(`(()=>{const vw=innerWidth,vh=innerHeight;const nav=document.querySelector('.mobile-nav');const navTop=nav?nav.getBoundingClientRect().top:null;const cards=[...document.querySelectorAll('.page .card')];const last=cards[cards.length-1];const bottom=last?last.getBoundingClientRect().bottom:null;const overflow=[...document.querySelectorAll('body *')].filter(e=>{const r=e.getBoundingClientRect();return r.width>1&&r.height>1&&r.right>vw+1&&!e.closest('.hero-art')}).length;return {vw,vh,scrollH:document.documentElement.scrollHeight,navTop:navTop&&Math.round(navTop),lastBottom:bottom&&Math.round(bottom),overflow}})()`);
  const shot=await send('Page.captureScreenshot',{format:'png',fromSurface:true,captureBeyondViewport:false});
  fs.writeFileSync(`${outDir}/${name}.png`,Buffer.from(shot.data,'base64'));
  report.push({name,title,file,...metrics});
}
fs.writeFileSync('static/prototype/capture-report.json',JSON.stringify({report,errors},null,2));
console.log(JSON.stringify({report,errors},null,2));ws.close();
