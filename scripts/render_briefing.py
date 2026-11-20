#!/usr/bin/env python3
"""Render the uploaded-reference decision board from reviewed public-news JSON."""
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

def sources(a):return ''.join(f'<a class="source-link" href="{esc(s["url"])}" target="_blank" rel="noopener noreferrer">{esc(s["name"])}</a>' for s in a['sources'])
def cube(small=False):return '<span class="cube'+(' sm' if small else '')+'">'+''.join(f'<span class="f f{i}">{v}</span>' for i,v in enumerate(['TG','' if small else 'TG','' if small else '&lt;/&gt;','' if small else '{ }','',''],1))+'</span>'
def archive_dates():
 dates={f.stem:f'archive/{f.name}' for f in (ROOT/'archive').glob('????-??-??.html')}
 for f in ROOT.glob('global-tech-daily-????-??-??.html'):dates[f.stem[-10:]]=f.name
 return sorted(dates.items(),reverse=True)
def render(date):
 data=json.loads((ROOT/'data'/f'briefing-{date}.json').read_text());assert data['date']==date
 A=data['articles'];byid={a['id']:a for a in A};assert len(byid)==len(A)
 lanes=data['decision_board'];assert len({x['id'] for x in lanes})==len(lanes)
 assert len(data['insights'])==6
 deep=[a for a in A if a['deep']];counts=collections.Counter(a['cat'] for a in A)
 for a in A:
  assert a['cat'] in CATEGORIES and all(a[k] for k in ['title','summary','fact','meta','published','status'])
  assert a['sources'] and all(s['url'].startswith('https://') for s in a['sources'])
  if a['deep']:assert all(a[k] for k in ['impact','lesson','action'])
 covered=set();laneof={};watchby={w['article']:w for w in data['watch']}
 for L in lanes:
  assert L['action'] and L['title']
  for i in L['evidence']+L['watch']:
   assert i in byid and laneof.get(i,L['id'])==L['id'],(i,'duplicate lane assignment');covered.add(i);laneof[i]=L['id']
  assert all(i in watchby for i in L['watch'])
  assert all(0<=i<len(data['followups']) for i in L['followups'])
  assert all(0<=i<len(data['insights']) for i in L['insights'])
  for st in L.get('stages',[]):assert all(i in L['evidence'] for i in st['ids'])
 assert covered==set(byid),'Every article must belong to a decision board'
 data['lane_of']=laneof;data['deep_count']=len(deep)
 brand=data.get('brand','Tech & Global News Daily');short=date.replace('-','.');brief=data['brief']
 style='\n'.join((ROOT/'templates'/n).read_text() for n in ['scene.css','decision-board.css'])
 js=(ROOT/'templates/decision-board.js').read_text()
 weekday=['MON','TUE','WED','THU','FRI','SAT','SUN'][datetime.date.fromisoformat(date).weekday()]
 out=[f'''<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="theme-color" content="#0C0B09"><title>{esc(brand)} · {short}</title><meta name="description" content="{esc(brief['summary'])}"><meta property="og:title" content="{esc(brand)} · {short}"><meta property="og:description" content="{esc(brief['summary'])}"><meta property="og:type" content="article"><meta property="og:url" content="{BASE}global-tech-daily-{date}.html"><link rel="alternate" type="application/rss+xml" title="{esc(brand)}" href="{BASE}feed.xml"><link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="https://fonts.googleapis.com/css2?family=Geist:wght@400;500;600;700&amp;family=Geist+Mono:wght@400;500;600&amp;family=IBM+Plex+Sans+KR:wght@400;500;600;700&amp;display=swap" rel="stylesheet"><script>document.documentElement.classList.add('js');</script><style>{style}</style></head><body><a class="skip" href="#main">본문으로 이동</a>''']
 out.append(f'''<header class="topbar"><div class="top-inner"><a class="wordmark" href="#main" aria-label="{esc(brand)} 처음으로"><span class="scene mini-scene" aria-hidden="true">{cube(True)}</span><strong>{esc(brand)}</strong></a><span class="date-pill mono">v{short} · {weekday}</span><div class="top-actions"><button type="button" class="utility quick-search" id="quickSearch" aria-label="뉴스 검색"><span>뉴스 검색</span><kbd aria-hidden="true">⌘K</kbd></button><a class="utility" href="{BASE}archive/index.html">지난 브리핑</a><button type="button" class="utility font-button" id="sizeToggle" aria-label="글자 크기 키우기" aria-pressed="false">가+</button></div></div></header><main id="main"><section class="lead" id="lead" aria-labelledby="leadTitle"><div class="hero"><span class="floor" aria-hidden="true"></span><div class="hero-copy"><div class="hero-meta"><span class="hero-kicker mono">THE DAILY INTELLIGENCE</span><span class="mono">{len(A)}개 이슈 · {len(deep)}개 심층분석</span></div><h1 id="leadTitle">{rich(brief['headline'])}</h1><p class="hero-desc">{esc(brief['summary'])}</p><div class="hero-cta"><a class="button primary" href="#board">판단 보드 보기</a><button type="button" class="button" data-show-all>전체 기사 {len(A)}건</button><button type="button" class="button" data-open="brief">핵심 브리핑</button></div></div><div class="scene hero-visual" aria-hidden="true"><span class="ring r1"><span class="dot"></span></span><span class="ring r2"></span><div class="float" style="transform-style:preserve-3d">{cube()}</div><img class="hero-avatar bob" src="assets/tg-wave.svg" width="118" height="106" alt=""><span class="hero-shadow"></span></div></div><div class="stat-grid">''')
 nextstat=data.get('next_stat',{'value':'NEXT','note':'다음 확인사항'})
 stats=[('DECISIONS',str(len(lanes)),'오늘 판단할 것','#board',False),('EVIDENCE',str(len(A)),'근거 기사','#all',True),('RISK_WATCH',str(len(data['watch'])),'사고 모니터링','#board',False),('NEXT',nextstat['value'],nextstat['note'],'#board',False)]
 for label,value,note,href,show in stats:out.append(f'<a class="stat card3d" href="{href}" {"data-show-all" if show else ""}><span class="stat-label mono">{label}</span><span class="stat-value mono extrude">{esc(value)}</span><span class="stat-note">{esc(note)}</span></a>')
 out.append(f'</div></section><section class="board" id="board" aria-labelledby="boardTitle"><span id="watch"></span><div class="board-head"><div class="board-heading"><img class="board-avatar bob" src="assets/tg-guide.svg" width="78" height="70" alt="" aria-hidden="true"><div class="board-title"><span class="speech">오늘은 이 세 가지만 판단하면 돼요</span><h2 id="boardTitle">오늘의 판단 보드</h2><span class="board-meta mono">DECISION_BOARD · 근거 기사 {len(A)} · Watch {len(data["watch"])} · 일정 {len(data["followups"])} · 인사이트 {len(data["insights"])}</span></div></div><div class="segmented" role="group" aria-label="판단 선택"><button type="button" data-lane="0" aria-pressed="true">전체</button>')
 for L in lanes:out.append(f'<button type="button" data-lane="{L["id"]}" aria-pressed="false">판단 {L["id"]:02d}</button>')
 out.append('</div></div><div class="board-columns" id="boardColumns">')
 for L in lanes:
  out.append(f'<article class="decision-card card3d" id="decision-{L["id"]}" data-lane-card="{L["id"]}" aria-labelledby="decision-title-{L["id"]}"><div class="lane-head"><div class="lane-meta"><span class="lane-number mono extrude">{L["id"]:02d}</span><span class="lane-count mono">근거 {len(L["evidence"])} · Watch {len(L["watch"])} · 일정 {len(L["followups"])}</span></div><h3 id="decision-title-{L["id"]}">{esc(L["title"])}</h3><p>{esc(L["description"])}</p></div><div class="lane-content"><div class="action-box"><span class="section-label">ACTION · 실행과제</span><p>{esc(L["action"])}</p></div>')
  stages=L.get('stages',[])
  if stages:
   n=sum(len(x['ids']) for x in stages);mx=max(len(x['ids']) for x in stages) or 1
   out.append(f'<div><span class="section-label">STAGE_MAP · {n}개 이슈의 적용 단계</span><div class="stage-map" aria-label="서로 다른 사업의 발표 단계">')
   for st in stages:out.append(f'<div class="stage"><span class="stage-bar-wrap"><span class="stage-bar" style="height:{14+int(len(st["ids"])/mx*32)}px" aria-hidden="true"></span></span><span class="stage-name mono">{esc(st["name"])}</span><span class="stage-ids mono">{esc(" ".join(f"#{i:02d}" for i in st["ids"]))}</span></div>')
   out.append('</div></div>')
  out.append(f'<div><span class="section-label">EVIDENCE · 근거 기사 {len(L["evidence"])}</span><div class="evidence-list">')
  for i in L['evidence']:
   a=byid[i];tone=' stage-tag' if a['status'] in ['실거래 공개','실거래·실증','첫 적용','PoC 완료','MOU','개발 중','구상','인수 계약'] else '';source=a.get('source_short',a['sources'][0]['name'].split(' · ')[0]);op=' open' if i==A[0]['id'] else ''
   out.append(f'<details class="evidence" name="evidence" id="evidence-{i}" data-evidence-id="{i}"{op}><summary><span class="evidence-meta"><span class="evidence-no mono">#{i:02d}</span><span class="category">{esc(a["cat"])}</span><span class="status{tone}">{esc(a["status"])}</span><span class="evidence-caret mono" aria-hidden="true"></span></span><span class="evidence-title">{esc(a["title"])}</span><span class="source-meta mono">{esc(source)} · {esc(a["published"])}</span></summary><div class="evidence-body"><div class="part"><span class="section-label">FACT · 사실</span><p>{esc(a.get("board_fact",a["summary"]))}</p></div>')
   if a.get('lesson'):out.append(f'<div class="part"><span class="section-label">SO WHAT · 시사점</span><p>{esc(a["lesson"])}</p></div>')
   out.append(f'<button type="button" class="detail-link" data-open="{i}">{"심층분석" if a["deep"] else "기사 상세"} 읽기</button><div class="evidence-links">{sources(a)}</div></div></details>')
  out.append('</div></div>')
  if L['watch']:
   out.append('<div><span class="section-label">RISK_WATCH · 사고 모니터링</span><div class="watch-list">')
   for i in L['watch']:
    w=watchby[i];tone='done' if w['state']=='해결' else 'open' if w['state'] in ['조사·대응','조사 중'] else ''
    out.append(f'<div class="watch-item" id="watch-{i}"><div class="watch-head"><a href="#article-{i}" data-open="{i}">{esc(w["name"])}</a><span class="watch-status {tone}">{esc(w["state"])}</span></div><p>{esc(w["fact"])}</p><p class="todo"><span class="mono">TODO</span>{esc(w["action"])}</p></div>')
   out.append('</div></div>')
  if L['followups']:
   out.append('<div><span class="section-label">NEXT · 다음에 확인할 것</span><div class="next-list">')
   for fi in L['followups']:
    f=data['followups'][fi];out.append(f'<div class="next-item"><span class="next-label mono">{esc(f["label"])}</span><div><a href="#article-{f["article"]}" data-open="{f["article"]}"><h4>{esc(f["title"])}</h4></a><p>{esc(f["body"])}</p></div></div>')
   out.append('</div></div>')
  out.append('<div><span class="section-label">INSIGHT · 관련 인사이트</span><div class="insight-list">')
  for ii in L['insights']:
   g=data['insights'][ii];out.append(f'<div class="insight"><h4><span class="mono">{ii+1:02d}</span>{esc(g["title"])}</h4><p>{esc(g["body"])}</p></div>')
  out.append('</div></div></div></article>')
 out.append(f'</div></section><details class="all-panel" id="all"><summary><span><span class="all-kicker mono">ALL_BRIEFS</span>전체 기사 {len(A)}건 · 분야별로 보기</span><span class="all-caret mono" aria-hidden="true"></span></summary><div class="all-content"><div class="news-tools"><div class="news-filters" id="filters" role="group" aria-label="분야 필터">')
 for c in ['전체']+[c for c in CATEGORIES if counts[c]]:out.append(f'<button type="button" data-filter="{esc(c)}" aria-pressed="{str(c=="전체").lower()}">{esc(c)}<span class="mono">{len(A) if c=="전체" else counts[c]}</span></button>')
 out.append(f'</div><div class="news-search"><label class="sr" for="newsSearch">제목·내용·출처 검색</label><input id="newsSearch" type="search" placeholder="제목·내용·출처 검색" autocomplete="off"></div></div><p class="result-count" id="resultCount" aria-live="polite">전체 · {len(A)}건</p><div class="news-list" id="newsList">')
 for a in A:
  i=a['id'];target=f'evidence-{i}' if any(i in L['evidence'] for L in lanes) else f'watch-{i}';tone=' stage-tag' if a['status'] in ['실거래 공개','실거래·실증','첫 적용','PoC 완료','MOU','개발 중','구상','인수 계약'] else ''
  out.append(f'<a class="news-row" data-news-id="{i}" href="#{target}" data-jump="{i}"><span class="news-no mono">{i:02d}</span><span class="category">{esc(a["cat"])}</span><span class="news-title">{esc(a["title"])}</span><span class="status{tone}">{esc(a["status"])}</span><span class="news-lane mono">판단 {laneof[i]:02d}</span></a>')
 out.append('</div><p class="empty" id="empty" hidden>검색 결과가 없습니다. 다른 키워드로 검색해 주세요.</p></div></details><section class="full-articles" aria-label="기사 전문"><h2>기사 전문</h2>')
 for a in A:
  out.append(f'<details id="article-{a["id"]}"><summary>{esc(a["title"])}</summary><p>{esc(a["meta"])}</p>')
  for k,label in [('fact','사실'),('impact','영향 · 분석'),('lesson','시사점'),('action','실행과제')]:
   if a.get(k):out.append(f'<h3>{label}</h3><p>{esc(a[k])}</p>')
  out.append(f'<div class="evidence-links">{sources(a)}</div></details>')
 out.append(f'</section></main><footer class="footer" id="footer"><div class="footer-inner"><span class="footer-note"><strong>{esc(brand)}</strong> — 글로벌 금융과 기술의 변화, 함께 읽는 인사이트</span><div class="footer-links mono"><a href="{BASE}archive/index.html">archive</a><a href="{BASE}feed.xml">rss</a><a href="#main">top</a></div></div></footer><dialog id="articleDialog" aria-labelledby="dialogTitle"><div class="dialog-bar"><span id="dialogCategory">심층분석</span><button type="button" class="close" id="closeDialog" aria-label="기사 닫기">×</button></div><div class="dialog-body" id="dialogBody"></div></dialog>')
 config=json.dumps(data,ensure_ascii=False).replace('</','<\\/')
 out.append(f'<script type="application/json" id="briefingData">{config}</script><script>{js}</script></body></html>')
 page='\n'.join(out)
 for phrase in ['검증 건수 안내','목표 대비 부족','기사 부족','디자인 샘플','KB GLOBAL ONE TEAM','뉴스데일리','테크 글로벌 뉴스','<x-dc>','support.js']:assert phrase not in page,phrase
 for name in ['index.html','latest.html',f'global-tech-daily-{date}.html','preview-redesign.html']:(ROOT/name).write_text(page)
 # Add/update exactly one RSS entry. Leave every older item intact.
 feed=ROOT/'feed.xml';tree=ET.parse(feed);ch=tree.getroot().find('channel');url=BASE+f'global-tech-daily-{date}.html'
 prior=[ET.tostring(i) for i in ch.findall('item') if i.findtext('link')!=url]
 current=[i for i in ch.findall('item') if i.findtext('link')==url];item=current[0] if current else ET.Element('item')
 for i in current:ch.remove(i)
 title=f'Tech & Global News Daily {short} | 외부업체 고객정보와 결제·AI 적용 단계' if date=='2026-11-20' else f'Tech & Global News Daily {short}'
 vals={'title':title,'link':url,'guid':url,'description':f'{brief["summary"]} 심층분석 {len(deep)}건·전체 뉴스 {len(A)}건.'}
 for k,v in vals.items():
  e=item.find(k)
  if e is None:e=ET.SubElement(item,k)
  e.text=v
 item.find('guid').set('isPermaLink','true')
 if item.find('pubDate') is None:ET.SubElement(item,'pubDate').text=format_datetime(datetime.datetime.now(ZoneInfo('Asia/Seoul')))
 first=next((i for i,e in enumerate(ch) if e.tag=='item'),len(ch));ch.insert(first,item)
 for k,v in [('title','Tech & Global News Daily'),('lastBuildDate',format_datetime(datetime.datetime.now(ZoneInfo('Asia/Seoul'))))]:
  e=ch.find(k)
  if e is None:e=ET.SubElement(ch,k)
  e.text=v
 tree.write(feed,encoding='utf-8',xml_declaration=True)
 assert [ET.tostring(i) for i in ch.findall('item')[1:]]==prior
 assert len({i.findtext('link') for i in ch.findall('item')})==len(ch.findall('item'))
 assert len({i.findtext('guid') for i in ch.findall('item')})==len(ch.findall('item'))
 # Real, existing archive URLs only.
 dates=archive_dates();archive=['<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>지난 브리핑 | Tech &amp; Global News Daily</title><style>body{margin:0;background:#0C0B09;color:#EFEBE2;font:17px/1.7 system-ui,sans-serif}.wrap{max-width:850px;margin:40px auto;padding:0 22px}a{color:#FFBC00;text-decoration:none}h1{font-size:30px;line-height:1.4}ul{list-style:none;padding:0}li{border-top:1px solid #2A261F}li a{display:flex;justify-content:space-between;padding:18px 0;gap:20px}li span{color:#acbac7;font-size:15px}a:focus-visible{outline:2px solid #FFBC00}p{color:#acbac7}</style></head><body><main class="wrap"><a href="../latest.html">Tech &amp; Global News Daily</a><h1>지난 브리핑</h1><p>날짜를 선택해 해당 일자의 브리핑을 읽으세요.</p><ul>']
 for d,path in dates:archive.append(f'<li><a href="../{path}"><strong>{d}</strong><span>{"최신 브리핑" if d==date else "브리핑 읽기"}</span></a></li>')
 archive.append('</ul></main></body></html>');(ROOT/'archive/index.html').write_text('\n'.join(archive))
 print(json.dumps({'date':date,'articles':len(A),'deep':len(deep),'categories':dict(counts),'archive_dates':len(dates),'rss_items':len(ch.findall('item'))},ensure_ascii=False))
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--date',required=True);args=ap.parse_args();datetime.date.fromisoformat(args.date);render(args.date)
