// API-served visual/keyboard evidence, including native Chromium 200% zoom.
const playwrightModule=process.env.PLAYWRIGHT_MODULE??'../apps/web/node_modules/@playwright/test/index.mjs';
const { chromium, expect }=await import(playwrightModule);
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
const origin=process.env.API_BASE_URL??'http://127.0.0.1:8000';
const out=path.resolve(process.env.EVIDENCE_DIR??'test-results/workspace-inspection');
fs.mkdirSync(out,{recursive:true});
const secureOriginArg=`--unsafely-treat-insecure-origin-as-secure=${origin}`;
const browser=await chromium.launch({args:[secureOriginArg]});
const context=await browser.newContext({viewport:{width:1440,height:1000},permissions:['clipboard-read','clipboard-write']});
const page=await context.newPage();
const observations={viewports:[],keyboard:[]};
try {
 await page.goto(origin+'/create');
 await page.getByLabel('Music brief').fill('Original keyboard and visual verification song');
 await page.getByLabel('Lyrics source').selectOption('user');
 const lyrics='  [अंतरा]\nहवा और रोशनी 🎵\n\n[பல்லவி]\n'+ 'வானம் தமிழ் இசை '.repeat(80)+'\t\n';
 await page.getByLabel('Your lyrics',{exact:true}).fill(lyrics);
 await page.getByRole('button',{name:'Generate',exact:true}).click();
 await expect(page.getByRole('region',{name:'Generated result'})).toBeVisible({timeout:45000});
 await page.evaluate(()=>document.fonts.ready);
 observations.projectUrl=page.url();
 const cdp=await context.newCDPSession(page);await cdp.send('DOM.enable');await cdp.send('CSS.enable');
 const documentNode=await cdp.send('DOM.getDocument');const lyricsNode=await cdp.send('DOM.querySelector',{nodeId:documentNode.root.nodeId,selector:'.lyrics'});
 observations.fonts=(await cdp.send('CSS.getPlatformFontsForNode',{nodeId:lyricsNode.nodeId})).fonts;
 expect(observations.fonts.some(f=>f.isCustomFont && f.familyName.includes('Tamil') && f.glyphCount>0)).toBe(true);
 await page.locator('.lyrics').screenshot({path:path.join(out,'native-script-lyrics.png')});
 await page.emulateMedia({reducedMotion:'reduce'});observations.reducedMotion=await page.evaluate(()=>matchMedia('(prefers-reduced-motion:reduce)').matches);

 await page.getByRole('button',{name:'Copy lyrics',exact:true}).click();
 const copyStatus=page.locator('[role="status"]').filter({hasText:/^(Lyrics copied\.|Copy failed\.)/});
 await expect(copyStatus).toBeVisible();
 const copyText=(await copyStatus.textContent())?.trim();
 observations.clipboardStatus=copyText;
 if(copyText==='Lyrics copied.') {
  observations.clipboardExact=(await page.evaluate(()=>navigator.clipboard.readText()))===lyrics;
  expect(observations.clipboardExact).toBe(true);
 } else {
  // Internal Compose hostnames are not secure contexts. The application keeps
  // the explicit manual-copy fallback; record the environment limitation.
  observations.clipboardExact=null;
 }
 await page.getByRole('button',{name:'Play',exact:true}).click();
 for(const width of [1440,390,360,320,768,1199,1200,1399,1600]) {
  await page.setViewportSize({width,height:1000});
  await expect(page.locator('audio')).toHaveCount(1);
  const state=await page.evaluate(()=>({width:innerWidth,scrollWidth:document.documentElement.scrollWidth,audioCount:document.querySelectorAll('audio').length,order:[...document.querySelectorAll('.result-pair>section')].map(x=>x.getAttribute('aria-label'))}));
  expect(state.scrollWidth).toBeLessThanOrEqual(width);
  expect(state.order).toEqual(width>=1200?['Generated Lyrics','Music Preview']:['Music Preview','Generated Lyrics']);
  observations.viewports.push(state);
  if([1440,390,360,320].includes(width))await page.screenshot({path:path.join(out,`workspace-${width}.png`),fullPage:true});
 }
 await page.getByRole('button',{name:'Pause',exact:true}).click();
 await page.setViewportSize({width:1440,height:1000});
 await page.getByLabel('Music brief').focus();
 for(let i=0;i<65;i++) {
  observations.keyboard.push(await page.evaluate(()=>{const e=document.activeElement;return {tag:e.tagName,label:e.getAttribute('aria-label')??e.labels?.[0]?.textContent?.trim().slice(0,70)??e.textContent?.trim().slice(0,70),outline:getComputedStyle(e).outlineStyle};}));
  await page.keyboard.press('Tab');
 }
 await context.close();
 const extension=fs.mkdtempSync(path.join(os.tmpdir(),'museforge-zoom-check-'));
 fs.writeFileSync(path.join(extension,'manifest.json'),JSON.stringify({manifest_version:3,name:'Workspace zoom verification',version:'1.0',permissions:['tabs'],background:{service_worker:'zoom.js'}}));
 fs.writeFileSync(path.join(extension,'zoom.js'),`chrome.tabs.onUpdated.addListener((id,change,tab)=>{if(change.status==='complete' && tab.url?.startsWith(${JSON.stringify(origin)})) chrome.tabs.setZoom(id,2);});`);
 const zoom=await chromium.launchPersistentContext('',{channel:'chromium',headless:true,viewport:null,args:['--window-size=1440,1000',secureOriginArg,'--disable-extensions-except='+extension,'--load-extension='+extension]});
 try {
  const p=await zoom.newPage();await p.goto(observations.projectUrl);await expect(p.getByRole('region',{name:'Generated result'})).toBeVisible();
  await expect.poll(()=>p.evaluate(()=>devicePixelRatio)).toBe(2);
  const history=p.locator('details').filter({has:p.getByText(/^Version History/)});
  if(await history.getAttribute('open')===null)await history.locator('summary').click();
  await p.getByRole('button',{name:'Rename version',exact:true}).scrollIntoViewIfNeeded();
  const button=await p.getByRole('button',{name:'Rename version',exact:true}).boundingBox();const nav=await p.getByRole('navigation').boundingBox();
  expect(button.y+button.height).toBeLessThanOrEqual(nav.y);
  observations.zoom=await p.evaluate(()=>({innerWidth,outerWidth,dpr:devicePixelRatio,scrollWidth:document.documentElement.scrollWidth}));
  expect(observations.zoom.scrollWidth).toBeLessThanOrEqual(observations.zoom.innerWidth);
  const zoomCdp=await zoom.newCDPSession(p);observations.zoomMetrics=await zoomCdp.send('Page.getLayoutMetrics');
  const screenshot=await zoomCdp.send('Page.captureScreenshot',{format:'png',fromSurface:true,captureBeyondViewport:false});
  fs.writeFileSync(path.join(out,'zoom-200-percent.png'),Buffer.from(screenshot.data,'base64'));
 }finally{await zoom.close();fs.rmSync(extension,{recursive:true});}
 fs.writeFileSync(path.join(out,'observations.json'),JSON.stringify(observations,null,2)+'\n');
 console.log('Keyboard, clipboard, viewport and native 200% zoom evidence:',out);
}finally{await browser.close();}
