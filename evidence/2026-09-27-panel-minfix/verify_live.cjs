// Actual deployed UI, isolated Chrome; never submit a question or generate a scan.
const fs=require('fs'),path=require('path');
const {chromium}=require('/Users/evander/.agents/skills/Browser/node_modules/playwright');
const dir=process.env.EVIDENCE_DIR,url=process.env.PANEL_URL,phase=process.env.CHECK_PHASE;
if(!dir||!url||!['before','after'].includes(phase))throw Error('Missing scoped inputs');
const out={started_at:new Date().toISOString(),phase,new_model_requests:0,submitted:false,console:[],errors:[],network_failures:[],http_errors:[],checks:[]};
const safe=u=>{try{let x=new URL(u);return x.origin+x.pathname}catch{return '[invalid]'}};
(async()=>{let browser;try{
 browser=await chromium.launch({channel:'chrome',headless:true});
 const page=await browser.newPage({viewport:{width:1366,height:900}});
 page.setDefaultTimeout(20000);
 page.on('console',m=>out.console.push({type:m.type(),text:m.text().replace(/sk-[A-Za-z0-9_-]{12,}|Bearer\s+[A-Za-z0-9._-]{12,}/gi,'[REDACTED]').slice(0,400)}));
 page.on('pageerror',e=>out.errors.push(e.message.slice(0,300)));
 page.on('requestfailed',r=>out.network_failures.push({url:safe(r.url()),error:r.failure()?.errorText}));
 page.on('response',r=>{if(r.status()>=400)out.http_errors.push({url:safe(r.url()),status:r.status()})});
 await page.goto(url,{waitUntil:'domcontentloaded',timeout:30000});
 await page.getByRole('heading',{name:/供应链控制塔/}).waitFor();
 await page.getByRole('tab',{name:/实时 Agent/}).click();
 await page.getByRole('textbox',{name:'问句',exact:true}).waitFor();
 const audit=page.getByRole('checkbox',{name:/串审计智能体/});
 await audit.waitFor();
 out.auditor_default=await audit.isChecked();
 out.checks.push({name:'new_session_auditor_default',pass:out.auditor_default===(phase==='before')});
 out.live_text=await page.locator('body').innerText();
 await page.screenshot({path:path.join(dir,`live-${phase}.png`),fullPage:true});
 if(phase==='after'){
  await page.getByRole('tab',{name:/工具证据/}).click();
  async function choose(i,option){await page.getByRole('combobox').nth(i).click();await page.getByRole('option',{name:option}).click();}
  async function check(name,texts){await page.waitForFunction(xs=>xs.every(x=>document.body.innerText.includes(x)),texts);out.checks.push({name,pass:true,texts});await page.screenshot({path:path.join(dir,`${name}.png`),fullPage:true});}
  await choose(0,/13001.*Colombian Coffee/);
  await choose(1,'San Francisco');
  await check('tool-positive-after',['短缺 3268 件','119,282.00','3298 件']);
  await choose(1,'Seattle');
  const slider=page.getByRole('slider');await slider.focus();await slider.press('Home');await slider.press('Tab');
  await check('tool-negative-after',['NO_REORDER:100','300 件','200 件','1 个数据点']);
  await page.getByRole('tab',{name:/每日巡检/}).click();
  await check('scan-preserved-after',['每日补货巡检','生成巡检报告']);
 }
}catch(e){out.failure=e.message;process.exitCode=1;}finally{if(browser)await browser.close();out.finished_at=new Date().toISOString();fs.writeFileSync(path.join(dir,`browser-${phase}.json`),JSON.stringify(out,null,2));}
if(out.checks.some(x=>!x.pass)||out.errors.length||out.network_failures.length||out.http_errors.length)process.exitCode=1;
console.log(JSON.stringify({phase,checks:out.checks,errors:out.errors,network_failures:out.network_failures,http_errors:out.http_errors,failure:out.failure}));})();
