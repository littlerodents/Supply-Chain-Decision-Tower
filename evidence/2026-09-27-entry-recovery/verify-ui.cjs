// Read-only tool-panel acceptance; never clicks live submit or invokes any agent.
const fs = require('fs');
const path = require('path');
const {chromium} = require('/Users/evander/.agents/skills/Browser/node_modules/playwright');
const dir = process.env.EVIDENCE_DIR;
const url = process.env.PANEL_URL;
if (!dir || !url) throw new Error('Missing scoped inputs');
const result = {started_at:new Date().toISOString(), isolated_browser:true, new_model_requests:0, cases:[], console:[], page_errors:[], network_failures:[], http_errors:[]};
const safeUrl = v=>{try{const u=new URL(v);return u.origin+u.pathname;}catch{return '[invalid URL]';}};
(async()=>{
  let browser;
  try {
    browser=await chromium.launch({channel:'chrome',headless:true});
    const page=await browser.newPage({viewport:{width:1920,height:1080}});
    page.setDefaultTimeout(15000);
    page.on('console',m=>result.console.push({type:m.type(),text:m.text().replace(/sk-[A-Za-z0-9_-]{12,}|Bearer\s+[A-Za-z0-9._-]{12,}/gi,'[REDACTED]').slice(0,500)}));
    page.on('pageerror',e=>result.page_errors.push({name:e.name,message:e.message.slice(0,300)}));
    page.on('requestfailed',r=>result.network_failures.push({url:safeUrl(r.url()),error:r.failure()?.errorText}));
    page.on('response',r=>{if(r.status()>=400)result.http_errors.push({url:safeUrl(r.url()),status:r.status()});});
    await page.goto(url,{waitUntil:'domcontentloaded',timeout:30000});
    await page.getByRole('heading',{name:/供应链控制塔/}).waitFor();
    await page.getByRole('combobox').first().waitFor();
    result.initial_dom=await page.locator('body').innerText();
    result.controls=await page.locator('input,textarea,[role=slider]').evaluateAll(es=>es.map(e=>({tag:e.tagName,role:e.getAttribute('role'),label:e.getAttribute('aria-label'),type:e.type,value:e.value,now:e.getAttribute('aria-valuenow')})));
    async function snap(name,expected){
      try { await page.waitForFunction(xs=>xs.every(s=>document.body.innerText.includes(s)),expected,{timeout:10000}); } catch {}
      await page.waitForTimeout(300);
      const text=await page.locator('body').innerText();
      const pass=expected.every(s=>text.includes(s));
      const file=name+'.png';
      await page.screenshot({path:path.join(dir,file),fullPage:true});
      result.cases.push({name,at:new Date().toISOString(),pass,expected,text,screenshot:file});
      console.log(name,pass?'PASS':'FAIL');
      fs.writeFileSync(path.join(dir,'browser-results.json'),JSON.stringify(result,null,2));
    }
    async function choose(index,name){
      await page.getByRole('combobox').nth(index).click();
      await page.getByRole('option',{name,exact:true}).click();
      await page.waitForTimeout(650);
    }
    async function weeks(n){
      const slider=page.getByRole('slider');
      await slider.focus();
      await slider.press('Home');
      for(let i=1;i<n;i++)await slider.press('ArrowRight');
      await slider.press('Tab');
      await page.waitForTimeout(900);
    }
    await snap('ui-initial',['本地样本','合成预测']);
    await choose(0,'13001 Colombian Coffee');
    await choose(1,'San Francisco');
    await snap('ui-positive-tool',['短缺 3268 件','119,282.00','Nature Source Coffee','当前库存','30 件','3298 件','12 个数据点']);
    await choose(1,'Seattle');
    await weeks(1);
    await snap('ui-negative-tool',['NO_REORDER:100','300 件','200 件','1 个数据点']);
    await choose(1,'Portland');
    await snap('ui-missing-record',['无 SKU 13001 的库存记录','不把未知库存当作真实零库存']);
    await weeks(26);
    await snap('ui-horizon-26',['未来 26 周需求预测','26 个数据点']);
    await choose(0,'11001 House Blend');
    await choose(1,'San Francisco');
    await snap('ui-supplier-origin',['Coffee Wholesale USA（San Francisco）']);
    await page.getByRole('tab',{name:/实时 Agent/}).click();
    result.live_auditor_default=await page.getByRole('checkbox',{name:/串审计智能体/}).isChecked();
    result.live_submit_present=await page.getByRole('button',{name:/提交（单次）/}).count();
    await snap('ui-live-observed-not-submitted',['自然问句','审计智能体']);
    // Disable only this browser session's optional auditor; do not submit.
    const auditCheckbox=page.getByRole('checkbox',{name:/串审计智能体/});
    await auditCheckbox.focus();
    await auditCheckbox.press('Space');
    await page.waitForTimeout(700);
    result.live_auditor_after_uncheck=await auditCheckbox.isChecked();
    if(result.live_auditor_after_uncheck)throw new Error('Keyboard toggle did not disable auditor; no submission attempted');
    await page.setViewportSize({width:1366,height:768});
    await snap('ui-live-1366-not-submitted',['问句','提交']);
  } catch(e) {
    result.error={name:e.name,message:e.message.slice(0,1500)};
    console.error(e.message);
  } finally {
    if(browser)await browser.close();
    result.finished_at=new Date().toISOString();
    fs.writeFileSync(path.join(dir,'browser-results.json'),JSON.stringify(result,null,2));
  }
  if(result.error || result.cases.some(c=>!c.pass))process.exitCode=1;
})();
