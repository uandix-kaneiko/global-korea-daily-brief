'use strict';
const config=JSON.parse(document.getElementById('briefingData').textContent);
const articles=config.articles,byId=new Map(articles.map(a=>[String(a.id),a])),lanes=config.decision_board;
const $=s=>document.querySelector(s),esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const validCategories=new Set(['전체',...articles.map(a=>a.cat)]),validLanes=new Set([0,...lanes.map(l=>l.id)]);
const query=new URLSearchParams(location.search),allPanel=$('#all'),dialog=$('#articleDialog');
let category=validCategories.has(query.get('category'))?query.get('category'):'전체';
let lane=validLanes.has(Number(query.get('lane')))?Number(query.get('lane')):0;
let activeArticle=null,articleEntryPushed=false,lastTrigger=null;

function renderFilters(){
 const ids=new Set(articles.filter(a=>category==='전체'||a.cat===category).map(a=>String(a.id)));
 document.querySelectorAll('[data-news-id]').forEach(el=>el.hidden=!ids.has(el.dataset.newsId));
 document.querySelectorAll('[data-filter]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.filter===category)));
 $('#resultCount').textContent=`${category} · ${ids.size}건`;$('#empty').hidden=ids.size!==0;
}
function renderLane(){document.querySelectorAll('[data-lane-card]').forEach(card=>card.hidden=lane!==0&&Number(card.dataset.laneCard)!==lane);document.querySelectorAll('[data-lane]').forEach(b=>b.setAttribute('aria-pressed',String(Number(b.dataset.lane)===lane)));$('#boardColumns').classList.toggle('is-focused',lane!==0);}
function saveQuery(){const u=new URL(location.href);category==='전체'?u.searchParams.delete('category'):u.searchParams.set('category',category);lane===0?u.searchParams.delete('lane'):u.searchParams.set('lane',String(lane));u.searchParams.delete('q');history.replaceState(history.state,'',u);}
function openAll(){allPanel.open=true;allPanel.scrollIntoView({block:'start'});}
function chooseLane(n){lane=validLanes.has(n)?n:0;renderLane();const u=new URL(location.href);u.hash='board';lane===0?u.searchParams.delete('lane'):u.searchParams.set('lane',String(lane));history.replaceState(null,'',u);$('#board').scrollIntoView({block:'start'});}
function showEvidence(id,route=true){
 const a=byId.get(String(id));if(!a)return;
 lane=Number(config.lane_of[a.id]);renderLane();const ev=document.getElementById('evidence-'+a.id);
 if(ev){document.querySelectorAll('.evidence').forEach(x=>{if(x!==ev)x.open=false;});ev.open=true;requestAnimationFrame(()=>requestAnimationFrame(()=>{ev.scrollIntoView({block:'start'});ev.querySelector('summary').focus({preventScroll:true});}));}
 else{const w=document.getElementById('watch-'+a.id);if(w)w.scrollIntoView({block:'start'});showArticle(a.id,route);return;}
 if(route){const u=new URL(location.href);u.searchParams.set('lane',String(lane));u.hash='evidence-'+a.id;history.pushState({evidence:a.id},'',u);}
}
$('.segmented').addEventListener('click',e=>{const b=e.target.closest('[data-lane]');if(b)chooseLane(Number(b.dataset.lane));});
$('#filters').addEventListener('click',e=>{const b=e.target.closest('[data-filter]');if(b){category=b.dataset.filter;renderFilters();saveQuery();}});
// Native details remain readable without JavaScript; only one evidence item opens at once.
document.querySelectorAll('.evidence').forEach(d=>d.addEventListener('toggle',()=>{if(d.open)document.querySelectorAll('.evidence').forEach(x=>{if(x!==d)x.open=false;});}));
function sourceLinks(sources){return sources.map(s=>`<a href="${esc(s.url)}" target="_blank" rel="noopener noreferrer">${esc(s.name)}</a>`).join('');}
function showArticle(id,route=true){
 const brief=id==='brief';const a=brief?{...config.brief.detail,cat:'오늘의 핵심 브리핑',meta:config.display_date+' · '+config.edition,sources:[]}:byId.get(String(id));if(!a)return;
 const wasOpen=dialog.open;activeArticle=id;
 if(route){const u=new URL(location.href);u.hash=`article-${id}`;if(wasOpen)history.replaceState(history.state,'',u);else{history.pushState({article:id},'',u);articleEntryPushed=true;}}
 $('#dialogCategory').textContent=a.cat;
 const related=brief?`<div class="related"><h3>근거 기사</h3>${a.related.map(i=>`<a href="#article-${i}" data-open="${i}">${esc(byId.get(String(i)).title)}</a>`).join('')}</div>`:'';
 const pos=articles.findIndex(x=>String(x.id)===String(id));
 $('#dialogBody').innerHTML=`<h2 id="dialogTitle">${esc(a.title)}</h2><div class="dialog-meta">${esc(a.meta)}${a.status?' · '+esc(a.status):''}</div><div class="dialog-summary">${esc(a.summary)}</div><h3>사실</h3><p>${esc(a.fact)}</p>${a.impact?`<h3>영향 · 분석</h3><p>${esc(a.impact)}</p>`:''}${a.lesson?`<h3>${a.cat==='IT 기술'?'금융IT 적용 관점':'시사점'}</h3><p>${esc(a.lesson)}</p>`:''}${a.action?`<h3>실행과제</h3><p>${esc(a.action)}</p>`:''}${related}${a.sources.length?`<div class="dialog-sources">원문과 출처${sourceLinks(a.sources)}</div>`:''}${!brief?`<div class="dialog-next"><button type="button" data-prev ${pos===0?'disabled':''}>이전 기사</button><button type="button" data-next ${pos===articles.length-1?'disabled':''}>다음 기사</button></div>`:''}`;
 if(!wasOpen){dialog.showModal();document.body.classList.add('modal-open');}dialog.scrollTop=0;$('#closeDialog').focus();
}
function closeArticle(){if(!dialog.open)return;dialog.close();if(articleEntryPushed){articleEntryPushed=false;history.back();}else{const u=new URL(location.href);u.hash='';history.replaceState(null,'',u);}}
function syncRoute(){const article=location.hash.match(/^#(?:article|deep|news)-(\d+|brief|main)$/);const ev=location.hash.match(/^#evidence-(\d+)$/);if(article){showArticle(article[1]==='main'?1:article[1],false);}else{if(dialog.open){dialog.close();articleEntryPushed=false;}if(ev)showEvidence(ev[1],false);if(['#all','#news'].includes(location.hash))allPanel.open=true;}}
document.addEventListener('click',e=>{
 const cat=e.target.closest('[data-category-jump]');if(cat){e.preventDefault();chooseLane(Number(cat.dataset.categoryJump));return;}
 const jump=e.target.closest('[data-jump]');if(jump){e.preventDefault();showEvidence(jump.dataset.jump);return;}
 const all=e.target.closest('[data-show-all]');if(all){e.preventDefault();const u=new URL(location.href);u.hash='all';history.replaceState(history.state,'',u);openAll(false);return;}
 const a=e.target.closest('[data-open]');if(a){e.preventDefault();if(!dialog.open)lastTrigger=a;showArticle(a.dataset.open);}
 const pos=articles.findIndex(x=>String(x.id)===String(activeArticle));if(e.target.closest('[data-prev]')&&pos>0)showArticle(articles[pos-1].id);if(e.target.closest('[data-next]')&&pos>=0&&pos<articles.length-1)showArticle(articles[pos+1].id);
});
$('#closeDialog').addEventListener('click',closeArticle);dialog.addEventListener('cancel',e=>{e.preventDefault();closeArticle();});dialog.addEventListener('close',()=>{document.body.classList.remove('modal-open');if(lastTrigger?.isConnected)lastTrigger.focus({preventScroll:true});});
dialog.addEventListener('click',e=>{if(e.target===dialog){const r=dialog.getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)closeArticle();}});
window.addEventListener('popstate',()=>{const p=new URLSearchParams(location.search);category=validCategories.has(p.get('category'))?p.get('category'):'전체';lane=validLanes.has(Number(p.get('lane')))?Number(p.get('lane')):0;renderLane();renderFilters();syncRoute();});window.addEventListener('hashchange',syncRoute);
function setLarge(on){document.body.classList.toggle('large-type',on);$('#sizeToggle').setAttribute('aria-pressed',String(on));$('#sizeToggle').setAttribute('aria-label',on?'기본 글자 크기로 보기':'글자 크기 키우기');}
try{setLarge(localStorage.getItem('tg-reading-large')==='1');}catch{}
$('#sizeToggle').addEventListener('click',()=>{const on=!document.body.classList.contains('large-type');setLarge(on);try{localStorage.setItem('tg-reading-large',on?'1':'0');}catch{}});
renderLane();renderFilters();if(category!=='전체')allPanel.open=true;syncRoute();

// Optional decorative motion; reading layout and article content stay fixed.
const motionPreference=window.matchMedia('(prefers-reduced-motion: reduce)');
const motionButton=$('#motionToggle');let motionWanted=true;const revealAnimations=new Set();
try{motionWanted=localStorage.getItem('tg-motion')!=='off';}catch{}
function updateMotion(){
 const on=motionWanted&&!motionPreference.matches;
 document.documentElement.classList.toggle('motion-on',on);
 motionButton.disabled=motionPreference.matches;
 motionButton.textContent=motionPreference.matches?'모션 줄임':on?'모션 켬':'모션 끔';
 motionButton.setAttribute('aria-pressed',String(on));
 motionButton.setAttribute('aria-label',motionPreference.matches?'기기 설정에 따라 모션 줄임':on?'화면 모션 끄기':'화면 모션 켜기');
 if(!on){revealAnimations.forEach(a=>a.cancel());revealAnimations.clear();}
}
motionButton.addEventListener('click',()=>{motionWanted=!motionWanted;updateMotion();try{localStorage.setItem('tg-motion',motionWanted?'on':'off');}catch{}});
motionPreference.addEventListener('change',updateMotion);updateMotion();
if('IntersectionObserver'in window){
 const observer=new IntersectionObserver(entries=>{entries.forEach(entry=>{
  if(!entry.isIntersecting)return;observer.unobserve(entry.target);
  if(!document.documentElement.classList.contains('motion-on'))return;
  const a=entry.target.animate([{opacity:.3,transform:'translateY(14px)'},{opacity:1,transform:'translateY(0)'}],{duration:650,easing:'cubic-bezier(.22,1,.36,1)'});
  revealAnimations.add(a);a.onfinish=()=>revealAnimations.delete(a);
 });},{threshold:.06});
 document.querySelectorAll('.decision-card,.all-panel').forEach(el=>observer.observe(el));
}
