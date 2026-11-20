from urllib.parse import urlparse
import re
import requests
from bs4 import BeautifulSoup

URL='https://rollcall.com/factbase/trump/topic/social/'

def inspect(html, label):
    soup=BeautifulSoup(html,'html.parser')
    text=soup.get_text(' ',strip=True)
    dates=re.findall(r'202[0-9]-\d\d-\d\d[T ]\d\d:\d\d(?::\d\d)?',html)
    print(f'{label}: html_bytes={len(html.encode())}, date_like={len(dates)}, article_tags={len(soup.find_all("article"))}, time_tags={len(soup.find_all("time"))}, says_no_posts={"No posts found" in text}, says_no_archive={"No social media archive available" in text}',flush=True)
    return dates

try:
    robots=requests.get('https://rollcall.com/robots.txt',timeout=15)
    print('robots:',robots.status_code,'chars=',len(robots.content),flush=True)
except Exception as exc:
    print('robots request failed:',str(exc)[:160],flush=True)

try:
    r=requests.get(URL,timeout=25,headers={'User-Agent':'Mozilla/5.0'})
    print('requests status:',r.status_code,'final URL:',r.url,flush=True)
    inspect(r.text,'plain HTML')
except Exception as exc:
    print('requests failed:',repr(exc),flush=True)


def structure(obj,depth=0):
    if depth>2:
        return type(obj).__name__
    if isinstance(obj,dict):
        return {k:structure(v,depth+1) for k,v in list(obj.items())[:25]}
    if isinstance(obj,list):
        return {'length':len(obj),'first_item_structure':structure(obj[0],depth+1) if obj else None}
    if isinstance(obj,str):
        return {'type':'string','length':len(obj)} if len(obj)>90 else obj
    return obj

try:
    direct=requests.get('https://rollcall.com/api/factbase/social',timeout=20,headers={'Accept':'application/json'})
    print('new API direct:',direct.status_code,'bytes:',len(direct.content),'content_type:',direct.headers.get('content-type'),flush=True)
    try:
        print('new API structure:',structure(direct.json()),flush=True)
    except ValueError:
        print('new API non-JSON body prefix:',repr(direct.text[:140]),flush=True)
except Exception as exc:
    print('new API direct failed:',repr(exc),flush=True)



print('--- API stats & filtered-query checks ---',flush=True)
base='https://rollcall.com/api/factbase/social'
params_tests=[
    ('default',None),
    ('last_hour date_range',{'date_range':'last_hour'}),
    ('last_hour dateFilter',{'dateFilter':'last_hour'}),
    ('last_hour range',{'range':'last_hour'}),
    ('platform all latest',{'platform':'all','sort':'date','sort_order':'desc','limit':'50'})
]
for label,params in params_tests:
    try:
        r=requests.get(base,params=params,timeout=20,headers={'Accept':'application/json'})
        print('variant:',label,'status:',r.status_code,'bytes:',len(r.content),flush=True)
        if r.status_code!=200: continue
        js=r.json()
        print('variant META:',label,repr(js.get('meta'))[:750],flush=True)
        print('variant STATS:',label,'last_hour',repr(js.get('stats',{}).get('date_range',{}).get('last_hour'))[:900],
            'last_day',repr(js.get('stats',{}).get('date_range',{}).get('last_day'))[:450],
            'platform',repr(js.get('stats',{}).get('platform'))[:450],flush=True)
        items=js.get('data',[])
        print('variant ITEM:',label,'num',len(items),'head',repr([
            {'date':x.get('date'),'platform':x.get('platform'),'id':x.get('id'),'type':x.get('type')}
            for x in items[:4]])[:950],flush=True)
    except Exception as exc:
        print('variant ERROR:',label,repr(exc)[:240],flush=True)
