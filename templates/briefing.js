'use strict';
const config=JSON.parse(document.getElementById('briefingData').textContent);
const news=config.articles,$=s=>document.querySelector(s);
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const params=new URLSearchParams(location.search),validCats=new Set(['전체',...news.map(n=>n.cat)]);
let selected=validCats.has(params.get('category'))?params.get('category'):'전체';
let activeArticle=null,articleEntryPushed=false,lastTrigger=null;
const search=$('#search'),dialog=$('#articleDialog');search.value=params.get('q')||'';
function render(){
 const q=search.value.trim().toLocaleLowerCase('ko');
 const visible=news.filter(n=>(selected==='전체'||n.cat===selected)&&[n.title,n.summary,n.fact,n.cat,...n.sources.map(s=>s.name)].join(' ').toLocaleLowerCase('ko').includes(q));
 const ids=new Set(visible.map(n=>String(n.id)));
 document.querySelectorAll('#newsList .news-row').forEach(row=>row.hidden=!ids.has(row.dataset.id));
 $('#resultLabel').textContent=`${selected} · ${visible.length}건${q?' · 검색 결과':''}`;
 $('#empty').hidden=visible.length!==0;
 document.querySelectorAll('[data-filter],.nav [data-cat]').forEach(b=>{const on=(b.dataset.filter||b.dataset.cat)===selected;b.classList.toggle('active',on);b.setAttribute('aria-pressed',String(on));});
}
function saveFilters(){const u=new URL(location.href);selected==='전체'?u.searchParams.delete('category'):u.searchParams.set('category',selected);search.value.trim()?u.searchParams.set('q',search.value.trim()):u.searchParams.delete('q');history.replaceState(history.state,'',u);}
function setFilter(c,scroll){selected=c;render();saveFilters();if(scroll)$('#news').scrollIntoView({block:'start'});}
$('.nav').addEventListener('click',e=>{const b=e.target.closest('[data-cat]');if(b)setFilter(b.dataset.cat,true);});
$('#filters').addEventListener('click',e=>{const b=e.target.closest('[data-filter]');if(b)setFilter(b.dataset.filter,false);});
search.addEventListener('input',()=>{render();saveFilters();});
$('#deepMore').addEventListener('click',()=>{const on=$('#deepList').classList.toggle('expanded');$('#deepMore').setAttribute('aria-expanded',String(on));$('#deepMore').textContent=on?'주요 분석만 보기':`심층분석 ${config.deep_count}건 모두 보기`;});
function sourceLinks(sources){return sources.map(s=>`<a href="${esc(s.url)}" target="_blank" rel="noopener noreferrer">${esc(s.name)}</a>`).join('');}
function showArticle(id,route=false){
 const isBrief=id==='brief';let n=isBrief?{...config.brief.detail,cat:'오늘의 핵심 브리핑',meta:config.display_date+' · '+config.edition,sources:[]}:news.find(x=>String(x.id)===String(id));if(!n)return;
 const wasOpen=dialog.open;activeArticle=id;
 if(route){const u=new URL(location.href);u.hash=`article-${id}`;if(wasOpen)history.replaceState(history.state,'',u);else{history.pushState({article:id},'',u);articleEntryPushed=true;}}
 $('#dialogCategory').textContent=n.cat;
 const related=isBrief?`<div class="related"><h3>근거 기사</h3>${n.related.map(i=>{const r=news.find(a=>a.id===i);return `<a href="#article-${i}" data-open="${i}">${esc(r.title)}</a>`;}).join('')}</div>`:'';
 const pos=news.findIndex(x=>String(x.id)===String(id));
 $('#dialogBody').innerHTML=`<h2 id="dialogTitle">${esc(n.title)}</h2><div class="dialog-meta">${esc(n.meta)}${n.status?' · '+esc(n.status):''}</div><div class="dialog-summary">${esc(n.summary)}</div><h3>사실</h3><p>${esc(n.fact)}</p>${n.impact?`<h3>영향 · 분석</h3><p>${esc(n.impact)}</p>`:''}${n.lesson?`<h3>${n.cat==='IT 기술·개발'?'금융IT 적용 관점':'시사점'}</h3><p>${esc(n.lesson)}</p>`:''}${n.action?`<h3>실행과제</h3><p>${esc(n.action)}</p>`:''}${related}${n.sources.length?`<div class="dialog-sources">원문과 출처${sourceLinks(n.sources)}</div>`:''}${!isBrief?`<div class="dialog-next"><button data-prev ${pos===0?'disabled':''}>이전 기사</button><button data-next ${pos===news.length-1?'disabled':''}>다음 기사</button></div>`:''}`;
 if(!wasOpen){dialog.showModal();document.body.classList.add('modal-open');}dialog.scrollTop=0;$('#closeDialog').focus();
}
function closeArticle(){if(!dialog.open)return;dialog.close();if(articleEntryPushed){articleEntryPushed=false;history.back();}else{const u=new URL(location.href);u.hash='';history.replaceState(null,'',u);}}
function syncRoute(){const m=location.hash.match(/^#(?:article|deep|news)-(\d+|brief|main)$/);if(m){showArticle(m[1]==='main'?1:m[1]);}else if(dialog.open){dialog.close();articleEntryPushed=false;}}
document.addEventListener('click',e=>{
 const a=e.target.closest('[data-open]');if(a){e.preventDefault();if(!dialog.open)lastTrigger=a;showArticle(a.dataset.open,true);}
 const pos=news.findIndex(x=>String(x.id)===String(activeArticle));if(e.target.closest('[data-prev]')&&pos>0)showArticle(news[pos-1].id,true);if(e.target.closest('[data-next]')&&pos>=0&&pos<news.length-1)showArticle(news[pos+1].id,true);
});
$('#closeDialog').addEventListener('click',closeArticle);dialog.addEventListener('cancel',e=>{e.preventDefault();closeArticle();});dialog.addEventListener('close',()=>{document.body.classList.remove('modal-open');if(lastTrigger?.isConnected)lastTrigger.focus({preventScroll:true});});
dialog.addEventListener('click',e=>{if(e.target===dialog){const r=dialog.getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)closeArticle();}});
window.addEventListener('popstate',()=>{const p=new URLSearchParams(location.search);selected=validCats.has(p.get('category'))?p.get('category'):'전체';search.value=p.get('q')||'';render();syncRoute();});
function setLarge(on){document.body.classList.toggle('large-type',on);$('#sizeToggle').setAttribute('aria-pressed',String(on));$('#sizeToggle').setAttribute('aria-label',on?'기본 글자 크기로 보기':'글자 크게 보기');}
try{setLarge(localStorage.getItem('tg-reading-large')==='1');}catch{}
$('#sizeToggle').addEventListener('click',()=>{const on=!document.body.classList.contains('large-type');setLarge(on);try{localStorage.setItem('tg-reading-large',on?'1':'0');}catch{}});
render();syncRoute();
