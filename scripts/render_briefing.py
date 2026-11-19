#!/usr/bin/env python3
"""Render the public daily edition from reviewed public-news JSON. Standard library only."""
import argparse,collections,datetime,html,json,re,xml.etree.ElementTree as ET
from pathlib import Path
from zoneinfo import ZoneInfo
from email.utils import format_datetime
ROOT=Path(__file__).resolve().parents[1]
BASE='https://uandix-kaneiko.github.io/global-korea-daily-brief/'
CATEGORIES=['금융·경제','글로벌 금융','지급결제','IT 기술·개발','AI·데이터','보안·장애']
def esc(s):return html.escape(str(s),quote=True)
def rich(s):
 s=esc(s)
 for tag in ['br','em','/em']:s=s.replace('&lt;'+tag+'&gt;','<'+tag+'>')
 return s

def sources(a):return ''.join(f'<a href="{esc(s["url"])}" target="_blank" rel="noopener noreferrer">{esc(s["name"])}</a>' for s in a['sources'])
def article_link(a,label=None,cls='story-link'):return f'<a class="{cls}" href="#article-{a["id"]}" data-open="{a["id"]}">{label or esc(a["title"])}</a>'

def archive_dates():
 dates={f.stem:f'archive/{f.name}' for f in (ROOT/'archive').glob('????-??-??.html')}
 for f in ROOT.glob('global-tech-daily-????-??-??.html'):dates[f.stem[-10:]]=f.name
 return sorted(dates.items(),reverse=True)

def render(date):
 data=json.loads((ROOT/'data'/f'briefing-{date}.json').read_text());assert data['date']==date
 A=data['articles']; byid={a['id']:a for a in A};assert len(byid)==len(A)
 assert len(data['insights'])==6
 for a in A:
  assert a['cat'] in CATEGORIES and all(a[k] for k in ['title','summary','fact','meta','published','status'])
  assert a['sources'] and all(s['url'].startswith('https://') for s in a['sources'])
  if a['deep']:assert all(a[k] for k in ['impact','lesson','action'])
 deep=[byid[i] for i in data['deep_order']];assert all(a['deep'] for a in deep)
 assert {a['id'] for a in deep}=={a['id'] for a in A if a['deep']}
 counts=collections.Counter(a['cat'] for a in A);data['deep_count']=len(deep)
 style='\n'.join((ROOT/'templates'/name).read_text() for name in ['base-style.css','production-style.css'])
 js=(ROOT/'templates/briefing.js').read_text();short=date.replace('-','.')
 head=f'''<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="theme-color" content="#101721"><title>Tech &amp; Global New Daily | {short}</title><meta name="description" content="{esc(data['brief']['summary'])}"><meta property="og:title" content="Tech &amp; Global New Daily · {short}"><meta property="og:description" content="{esc(data['brief']['summary'])}"><meta property="og:type" content="article"><meta property="og:url" content="{BASE}global-tech-daily-{date}.html"><link rel="alternate" type="application/rss+xml" title="Tech &amp; Global New Daily" href="{BASE}feed.xml"><link rel="preconnect" href="https://cdn.jsdelivr.net" crossorigin><link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/pretendard@1.3.9/dist/web/static/pretendard.css"><script>document.documentElement.classList.add('js');</script><style>{style}</style></head><body><a class="skip" href="#main">본문으로 이동</a>'''
 nav=''.join(f'<button type="button" data-cat="{esc(c)}" aria-pressed="{str(c=="전체").lower()}">{esc(c)}</button>' for c in ['전체']+[c for c in CATEGORIES if counts[c]])+'<a class="nav-watch" href="#watch">사고 Watch</a>'
 out=[head,f'''<header class="top"><div class="shell mast"><a class="brand" href="#main" aria-label="Tech &amp; Global New Daily 처음으로"><span class="brand-mark" aria-hidden="true">TG</span><span class="brand-name">Tech &amp; Global<span class="brand-edition">New Daily</span></span></a><div class="mast-right"><div class="issue"><b>{esc(data['display_date'])}</b><br>글로벌 금융과 기술을 읽는 아침</div><a class="archive-link" href="{BASE}archive/index.html">지난 브리핑</a><button type="button" class="reading-size" id="sizeToggle" aria-pressed="false" aria-label="글자 크게 보기">가<sup>+</sup></button></div></div><div class="navrow"><div class="shell navinner"><nav class="nav" aria-label="분야별 뉴스">{nav}</nav><a class="watch-link" href="#watch"><span>WATCH</span>금융IT 사고</a></div></div></header><main class="shell" id="main"><div class="edition"><span class="eyebrow">THE DAILY INTELLIGENCE</span><p class="issue-count">{len(A)}개 이슈 · {len(deep)}개 심층분석</p><p class="mobile-issue">{short} · {esc(data['edition'])}</p></div>''']
 brief=data['brief'];out.append(f'<section class="brief" aria-labelledby="briefTitle"><div><h1 id="briefTitle">{rich(brief["headline"])}</h1><p class="brief-intro">{esc(brief["summary"])}</p><button type="button" class="brief-more" data-open="brief">오늘의 핵심 브리핑 읽기</button></div><div class="brief-points"><h2>오늘 판단할 세 가지</h2>')
 for i,t in enumerate(brief['points'],1):out.append(f'<div class="priority"><span class="no" aria-hidden="true">{i}</span><div><a href="#article-{t["article"]}" data-open="{t["article"]}"><strong>{esc(t["title"])}</strong></a><p>{esc(t["body"])}</p></div></div>')
 out.append('</div></section><section class="content-section" aria-labelledby="topStories"><div class="section-head"><div><p class="section-kicker">TOP STORIES</p><h2 id="topStories">오늘의 주요 이슈</h2></div><a class="quiet-link" href="#news">전체 뉴스 보기</a></div><div class="lead-grid">')
 h=data['highlights'][0];a=byid[h['id']]
 out.append(f'<article class="lead-card"><div class="tags"><span class="tag">메인 이슈</span><span class="tag secondary">{esc(a["cat"])}</span></div>{article_link(a,"<h3>"+rich(h["title"])+"</h3>")}<p>{esc(h["summary"])}</p><div class="card-foot"><span>{esc(a["sources"][0]["name"].split(" · ")[0])} · {esc(a["published"])}</span>{article_link(a,"심층분석 읽기","read-label")}</div></article><div class="side-stories">')
 for h in data['highlights'][1:]:
  a=byid[h['id']];out.append(f'<article class="side-story"><div class="small-kicker">{esc(h["kicker"])}</div>{article_link(a,"<h3>"+rich(h["title"])+"</h3>")}<p>{esc(h["summary"])}</p></article>')
 out.append(f'</div></div></section><div class="dual-main"><section aria-labelledby="deepHeading"><div class="section-head deep-head"><div><p class="section-kicker">IN DEPTH</p><h2 id="deepHeading">심층분석</h2><p class="section-desc">사실·영향·시사점·실행과제를 연결합니다.</p></div><span class="quiet-link">{len(deep)}건</span></div><div id="deepList" class="deep-list">')
 for a in deep:out.append(f'<article class="deep-row"><div><span class="row-cat">{esc(a["cat"])} · {esc(a["status"])}</span>{article_link(a,"<h3>"+esc(a["title"])+"</h3>")}<p>{esc(a["lesson"])}</p></div>{article_link(a,"분석 읽기","read-label")}</article>')
 out.append(f'</div><button type="button" class="wide-button" id="deepMore" aria-expanded="false" aria-controls="deepList">심층분석 {len(deep)}건 모두 보기</button></section><aside class="rail" aria-labelledby="nextHeading"><h2 id="nextHeading">다음에 확인할 것</h2><div class="rail-inner">')
 for t in data['followups']:out.append(f'<div class="rail-item"><span class="rail-label">{esc(t["label"])}</span><a href="#article-{t["article"]}" data-open="{t["article"]}"><h3>{esc(t["title"])}</h3></a><p>{esc(t["body"])}</p></div>')
 out.append('</div></aside></div>')
 tech=[a for a in A if a['cat']=='IT 기술·개발']
 if tech:
  out.append('<section class="tech" aria-labelledby="techHeading"><div class="tech-top"><div><p class="section-kicker">TECHNOLOGY &amp; ENGINEERING</p><h2 id="techHeading">IT 기술·개발</h2><p>기술 변화와 금융IT의 적용 조건을 함께 읽습니다.</p></div><span class="tech-label" aria-hidden="true">&lt;/&gt;</span></div><div class="tech-grid">')
  for a in tech[:2]:out.append(f'<article class="tech-story">{article_link(a,"<h3>"+esc(a["title"])+"</h3>")}<p>{esc(a["summary"])}</p><p class="tech-question">적용 관점 · {esc(a["lesson"])}</p><div class="meta">{esc(a["sources"][0]["name"])} · {esc(a["status"])}</div></article>')
  out.append('</div></section>')
 out.append('<section class="content-section" id="news" aria-labelledby="newsHeading"><div class="section-head news-head"><div><p class="section-kicker">NEWS DESK</p><h2 id="newsHeading">분야별 전체 뉴스</h2><p class="section-desc">제목·내용·출처로 검색하고 관심 분야를 선택하세요.</p></div><div class="search"><label class="sr" for="search">뉴스 제목·내용·출처 검색</label><input id="search" type="search" placeholder="제목·키워드·출처 검색" autocomplete="off"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" aria-hidden="true"><circle cx="10" cy="10" r="6.5"/><path d="m15 15 6 6"/></svg></div></div><div class="news-filter" id="filters" aria-label="기사 분야 필터">')
 for c in ['전체']+[c for c in CATEGORIES if counts[c]]:out.append(f'<button type="button" data-filter="{esc(c)}" aria-pressed="{str(c=="전체").lower()}" class="{"active" if c=="전체" else ""}">{esc(c)} <span>{len(A) if c=="전체" else counts[c]}</span></button>')
 out.append(f'</div><p class="result-label" id="resultLabel" aria-live="polite">전체 · {len(A)}건</p><div class="news-list" id="newsList">')
 for a in A:out.append(f'<article class="news-row" data-id="{a["id"]}"><span class="category">{esc(a["cat"])}</span><div><span class="row-meta">{esc(a["status"])}</span>{article_link(a,"<h3>"+esc(a["title"])+"</h3>")}<p>{esc(a["summary"])}</p></div><div class="source-name"><span>{esc(a["sources"][0]["name"].split(" · ")[0])}</span><span class="source-date">{esc(a["published"])}</span><span>{"심층분석" if a["deep"] else "뉴스 브리프"}</span></div></article>')
 out.append('</div><p class="empty" id="empty" hidden>검색 결과가 없습니다. 다른 키워드로 검색해 주세요.</p></section><section class="watch-section" id="watch" aria-labelledby="watchHeading"><div class="section-head"><div><p class="section-kicker">RISK MONITOR</p><div class="watch-heading"><h2 id="watchHeading">금융IT 사고·금융사기</h2><span class="watch-badge">WATCH</span></div></div></div><div class="table-wrap"><table class="watch-table"><thead><tr><th scope="col">대상</th><th scope="col">상태</th><th scope="col">현재 확인 내용</th><th scope="col">확인할 과제</th></tr></thead><tbody>')
 for w in data['watch']:out.append(f'<tr><td><a href="#article-{w["article"]}" data-open="{w["article"]}">{esc(w["name"])}</a></td><td><span class="state {esc(w["tone"])}">{esc(w["state"])}</span></td><td data-label="현황">{esc(w["fact"])}</td><td data-label="과제">{esc(w["action"])}</td></tr>')
 out.append('</tbody></table></div></section><section class="insights" aria-labelledby="insightHeading"><div class="section-head"><div><p class="section-kicker">PERSPECTIVES</p><h2 id="insightHeading">6대 인사이트</h2></div></div><div class="insight-grid">')
 for t in data['insights']:out.append(f'<article class="insight"><h3>{esc(t["title"])}</h3><p>{esc(t["body"])}</p></article>')
 out.append('</div></section><section class="full-articles" aria-label="기사 전문"><h2>기사 전문</h2>')
 for a in A:
  out.append(f'<details id="article-{a["id"]}"><summary>{esc(a["title"])}</summary><p>{esc(a["meta"])}</p>')
  for key,label in [('fact','사실'),('impact','영향 · 분석'),('lesson','시사점'),('action','실행과제')]:
   if a.get(key):out.append(f'<h3>{label}</h3><p>{esc(a[key])}</p>')
  out.append(f'<div class="dialog-sources">원문과 출처{sources(a)}</div></details>')
 out.append(f'</section><footer class="footer"><div><b>Tech &amp; Global New Daily</b>글로벌 금융과 기술의 변화, 함께 읽는 인사이트.</div><div class="footer-links"><a href="{BASE}archive/index.html">지난 브리핑</a><a href="{BASE}feed.xml">RSS</a><a href="#main">맨 위로</a></div></footer></main><dialog id="articleDialog" aria-labelledby="dialogTitle"><div class="dialog-bar"><span id="dialogCategory">심층분석</span><button type="button" class="close" aria-label="기사 닫기" id="closeDialog">×</button></div><div class="dialog-body" id="dialogBody"></div></dialog>')
 config=json.dumps(data,ensure_ascii=False).replace('</','<\\/')
 out.append(f'<script id="briefingData" type="application/json">{config}</script><script>{js}</script></body></html>')
 page='\n'.join(out)
 for phrase in ['검증 건수 안내','목표 대비 부족','기사 부족','디자인 샘플','KB GLOBAL ONE TEAM','뉴스데일리','테크 글로벌 뉴스']:assert phrase not in page,phrase
 for name in ['index.html','latest.html',f'global-tech-daily-{date}.html','preview-redesign.html']:(ROOT/name).write_text(page)
 # Add/update exactly one RSS entry. Leave every older item intact.
 feed=ROOT/'feed.xml';tree=ET.parse(feed);ch=tree.getroot().find('channel');url=BASE+f'global-tech-daily-{date}.html'
 prior=[ET.tostring(i) for i in ch.findall('item') if i.findtext('link')!=url]
 current=[i for i in ch.findall('item') if i.findtext('link')==url];item=current[0] if current else ET.Element('item')
 for i in current:ch.remove(i)
 title=f'Tech & Global New Daily {short} | 외부업체 고객정보와 결제·AI 적용 단계' if date=='2026-11-20' else f'Tech & Global New Daily {short}'
 vals={'title':title,'link':url,'guid':url,'description':f'{brief["summary"]} 심층분석 {len(deep)}건·전체 뉴스 {len(A)}건.'}
 for k,v in vals.items():
  e=item.find(k)
  if e is None:e=ET.SubElement(item,k)
  e.text=v
 item.find('guid').set('isPermaLink','true')
 if item.find('pubDate') is None:ET.SubElement(item,'pubDate').text=format_datetime(datetime.datetime.now(ZoneInfo('Asia/Seoul')))
 first=next((i for i,e in enumerate(ch) if e.tag=='item'),len(ch));ch.insert(first,item)
 for k,v in [('title','Tech & Global New Daily'),('lastBuildDate',format_datetime(datetime.datetime.now(ZoneInfo('Asia/Seoul'))))]:
  e=ch.find(k)
  if e is None:e=ET.SubElement(ch,k)
  e.text=v
 tree.write(feed,encoding='utf-8',xml_declaration=True)
 assert [ET.tostring(i) for i in ch.findall('item')[1:]]==prior
 assert len({i.findtext('link') for i in ch.findall('item')})==len(ch.findall('item'))
 assert len({i.findtext('guid') for i in ch.findall('item')})==len(ch.findall('item'))
 # Real, existing archive URLs only.
 dates=archive_dates();archive=['<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>지난 브리핑 | Tech &amp; Global New Daily</title><style>body{margin:0;background:#0c121a;color:#ecf0f4;font:17px/1.7 system-ui,sans-serif}.wrap{max-width:850px;margin:40px auto;padding:0 22px}a{color:#e7c787;text-decoration:none}h1{font-size:30px;line-height:1.4}ul{list-style:none;padding:0}li{border-top:1px solid #293440}li a{display:flex;justify-content:space-between;padding:18px 0;gap:20px}li span{color:#acbac7;font-size:15px}a:focus-visible{outline:2px solid #e7c787}p{color:#acbac7}</style></head><body><main class="wrap"><a href="../latest.html">Tech &amp; Global New Daily</a><h1>지난 브리핑</h1><p>날짜를 선택해 해당 일자의 브리핑을 읽으세요.</p><ul>']
 for d,path in dates:archive.append(f'<li><a href="../{path}"><strong>{d}</strong><span>{"최신 브리핑" if d==date else "브리핑 읽기"}</span></a></li>')
 archive.append('</ul></main></body></html>');(ROOT/'archive/index.html').write_text('\n'.join(archive))
 print(json.dumps({'date':date,'articles':len(A),'deep':len(deep),'categories':dict(counts),'archive_dates':len(dates),'rss_items':len(ch.findall('item'))},ensure_ascii=False))
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--date',required=True);args=ap.parse_args();datetime.date.fromisoformat(args.date);render(args.date)
