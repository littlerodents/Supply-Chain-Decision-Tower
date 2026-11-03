// Scoped, temporary CDP observer; records no headers, bodies, or console arguments.
import fs from 'node:fs';
import path from 'node:path';
const dir = process.env.EVIDENCE_DIR;
const targetId = process.env.TARGET_ID;
const panelUrl = process.env.PANEL_URL;
if (!dir || !targetId || !panelUrl || !process.env.CDP_ORIGIN) throw new Error('Missing scoped runtime inputs');
const out = path.join(dir, 'browser-events.jsonl');
const log = (event) => fs.appendFileSync(out, JSON.stringify({at:new Date().toISOString(), ...event})+'\n');
const safeUrl = (value) => { try { const u=new URL(value); return u.origin+u.pathname; } catch { return '[invalid URL]'; } };
const version = await fetch(process.env.CDP_ORIGIN+'/json/version').then(r=>r.json());
const ws = new WebSocket(version.webSocketDebuggerUrl);
await new Promise((resolve,reject)=>{ws.addEventListener('open',resolve,{once:true});ws.addEventListener('error',reject,{once:true});});
let id=0, sessionId;
const pending=new Map();
function send(method,params={},session){
  return new Promise((resolve,reject)=>{
    const n=++id;
    const timer=setTimeout(()=>{pending.delete(n);reject(new Error('CDP timeout: '+method));},15000);
    pending.set(n,{resolve,reject,timer});
    ws.send(JSON.stringify({id:n,method,params,...(session?{sessionId:session}:{})}));
  });
}
ws.addEventListener('message', event=>{
  const d=JSON.parse(event.data);
  if(d.id){const p=pending.get(d.id);if(p){clearTimeout(p.timer);pending.delete(d.id);d.error?p.reject(new Error(d.error.message)):p.resolve(d.result);}return;}
  if(d.sessionId!==sessionId)return;
  const p=d.params||{};
  if(d.method==='Network.requestWillBeSent')log({event:d.method,requestId:p.requestId,method:p.request.method,url:safeUrl(p.request.url),type:p.type});
  if(d.method==='Network.responseReceived')log({event:d.method,requestId:p.requestId,status:p.response.status,url:safeUrl(p.response.url),type:p.type});
  if(d.method==='Network.loadingFailed')log({event:d.method,requestId:p.requestId,error:p.errorText,canceled:!!p.canceled});
  if(d.method==='Runtime.exceptionThrown')log({event:d.method,text:p.exceptionDetails.text,line:p.exceptionDetails.lineNumber});
  if(d.method==='Runtime.consoleAPICalled')log({event:d.method,type:p.type});
});
sessionId=(await send('Target.attachToTarget',{targetId,flatten:true})).sessionId;
for(const domain of ['Page','Runtime','Network'])await send(domain+'.enable',{},sessionId);
await send('Emulation.setDeviceMetricsOverride',{width:1920,height:1080,deviceScaleFactor:1,mobile:false},sessionId);
log({event:'CAPTURE_READY',targetId});
fs.writeFileSync(path.join(dir,'browser-capture-ready.json'),JSON.stringify({pid:process.pid,targetId,at:new Date().toISOString()}));
await send('Page.navigate',{url:panelUrl},sessionId);
let closed=false;
async function close(){if(closed)return;closed=true;log({event:'CAPTURE_STOPPED'});try{await send('Target.detachFromTarget',{sessionId});}catch{}ws.close();process.exit(0);}
process.on('SIGTERM',close);
setTimeout(close,15*60*1000);
