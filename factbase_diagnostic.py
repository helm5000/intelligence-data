from urllib.parse import urlparse
import re
import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

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

try:
    observed=set()
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True,args=['--no-sandbox'])
        page=browser.new_page(viewport={'width':1280,'height':900})
        def on_response(resp):
            try:
                if resp.request.resource_type in ('xhr','fetch'):
                    u=urlparse(resp.url)
                    observed.add((resp.status,u.netloc,u.path[:180]))
            except Exception:
                pass
        page.on('response',on_response)
        resp=page.goto(URL,wait_until='domcontentloaded',timeout=45000)
        page.wait_for_timeout(10000)
        print('browser status:',resp.status if resp else None,'page title:',page.title(),flush=True)
        inspect(page.content(),'rendered HTML')
        print('network xhr/fetch (status,host,path only):',sorted(observed)[:40],flush=True)
        browser.close()
except Exception as exc:
    print('browser failed:',repr(exc),flush=True)
