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

