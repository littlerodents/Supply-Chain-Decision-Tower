const fs=require('fs'),path=require('path');
const {chromium}=require('/Users/evander/.agents/skills/Browser/node_modules/playwright');
const out=process.env.EVIDENCE_DIR,url=process.env.PANEL_URL;
if(!out||!url)throw new Error('Missing scoped inputs');
(async()=>{const b=await chromium.launch({channel:'chrome',headless:true,timeout:15000});const r={started_at:new Date().toISOString(),new_model_requests:0,previous_attempt:'External command budget expired at 40s; no result claimed.'};
try{const p=await b.newPage({viewport:{width:1366,height:768}});p.setDefaultTimeout(8000);await p.goto(url,{waitUntil:'domcontentloaded',timeout:20000});await p.getByRole('combobox').first().waitFor();
for(const [i,n] of [[0,'15001 Decaf Espresso'],[1,'Seattle']]){await p.getByRole('combobox').nth(i).click();await p.getByRole('option',{name:n,exact:true}).click();await p.waitForTimeout(700);}
await p.waitForFunction(()=>/IndexError|未出决策|无供应商/.test(document.body.innerText),{},{timeout:12000});
r.text=await p.locator('body').innerText();r.uncaught_error=r.text.includes('IndexError');await p.screenshot({path:path.join(out,'ui-missing-supplier.png'),fullPage:true});
}catch(e){r.error=e.message.slice(0,1500);}finally{await b.close();r.finished_at=new Date().toISOString();fs.writeFileSync(path.join(out,'ui-missing-supplier.json'),JSON.stringify(r,null,2));}
console.log(JSON.stringify({uncaught_error:r.uncaught_error,error:r.error}));})();
