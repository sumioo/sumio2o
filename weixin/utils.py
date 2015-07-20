#coding:utf-8

from hashlib import sha1
import xml.etree.ElementTree as ET
import urllib2,urllib
from HTMLParser import HTMLParser
import re

from sae.taskqueue import Task, TaskQueue


TOKEN='sumioo'

def echo_str(query_dict):
    signature=query_dict.get('signature','')
    timestamp=query_dict.get('timestamp','')
    nonce=query_dict.get('nonce','')
    echostr=query_dict.get('echostr','')
    l=[TOKEN,timestamp,nonce]
    l.sort()
    st=''.join(l)
    st=sha1(st).hexdigest()
    if st == signature:
        return echostr
    else:
        return False

def verify_source(query_dict):
    '''
    verify the request's source.argument query_dict is 'GET' method argument
    '''
    signature=query_dict.get('signature','')
    timestamp=query_dict.get('timestamp','')
    nonce=query_dict.get('nonce','')
    l=[TOKEN,timestamp,nonce]
    l.sort()
    st=''.join(l)
    st=sha1(st).hexdigest()
    if st == signature:
        return True
    else:
        return False

def convert_xml_to_dict(request):
    '''
    process the post xml data,return all tags and its text as a dict .
    '''
    xml_dict={}
    xml_tree=ET.parse(request)
    root=xml_tree.getroot()
    for child in root:
        xml_dict[child.tag]=child.text
    return xml_dict


def fetch_url(key_word,method,page):
    k = urllib.urlencode({method:key_word.encode('gbk')})
    url ='http://210.38.245.168:81/searchresult.aspx'
    params='?%s&dt=ALL&cl=ALL&dept=ALL&sf=M_PUB_YEAR&ob=DESC&page=%s&dp=45&sm=table' %(k,page)
    url=url+params
    print url
    headers={'User-Agent':'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/38.0.2125.122 UBrowser/4.0.3647.11 Safari/537.36'}
    req=urllib2.Request(url=url,headers=headers)
    return urllib2.urlopen(req) #file-like object


class Myhtmlparser(HTMLParser):
    d=['searchresult_cb','title','author','press','year','ac_num','quantity','lendable']
    pattern1=('id','ctl00_ContentPlaceHolder1_countlbl') # total numbers pattern
    pattern2=('id','ctl00_ContentPlaceHolder1_dplblfl1') #current page pattern
    pattern3=('id','ctl00_ContentPlaceHolder1_gplblfl1') #total page pattren
    def __init__(self):
        HTMLParser.__init__(self)
        self.flag,self.flag2=False,False
        self.nums=[]
        self.temp=[]
        self.rt=[]
        self.data=[]
    def handle_starttag(self,tag,attrs):
        if tag=='tbody':
            self.flag=True
        elif tag == 'span' and (Myhtmlparser.pattern1 in attrs or Myhtmlparser.pattern2 in attrs or Myhtmlparser.pattern3 in attrs):
            self.flag2=True
    def handle_data(self,data):
            if self.flag and (not data.isspace()):
                self.data.append(data)
            elif self.flag2:
                self.nums.append(int(data))
    def handle_endtag(self,tag):
            if self.flag and tag=='td':
                self.temp.append(''.join(self.data))
                self.data=[]
            if self.flag and tag=='tr':
                #print self.temp
                self.rt.append(dict(zip(Myhtmlparser.d,self.temp)))
                self.temp=[]
            if tag=='tbody':
                    self.flag=False
            elif tag=='span':
                self.flag2=False


def query_library(key_word,title,page):
    '''
    open the school library search page

    '''
    html=fetch_url(key_word,title,page).read()
    parser=Myhtmlparser()
    parser.feed(html)
    if parser.rt:
        return parser.rt,parser.nums[0],parser.nums[1],parser.nums[2] #parser[0,1,2]:total nums,current page,total page;
    else:
        return [],0,0,0
"""
def set_kvdb(x_dict):
    '''
    set sae kvdb
    '''
    user_dict={'rt':rt,'next':9,'current_page':current_page,'total_page':total_page,'total_nums':total_nums,'key_word':content}
    kv.set(from_username,user_dict)
"""

def add_task(user_dict,url,user):
    '''
    add sae queue task ,fetch next page
    '''
    url=url+'?&from=%s' %user
    queue = TaskQueue('fetch_next')
    queue.add(Task(url))
    return None

