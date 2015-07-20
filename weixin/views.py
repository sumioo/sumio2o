#coding:utf-8
from hashlib import sha1
from time import time

from django import template
from django.http import HttpResponse,HttpResponseRedirect
import sae.kvdb
from utils import *

kv=sae.kvdb.Client()

def init_srever(request):
    if request.method=='GET':
        return HttpResponse(echo_str(request.GET))

def index(request):
    if request.method=='POST':
        if verify_source(request.GET):        #检查请求来源是否合法
            x_dict=convert_xml_to_dict(request)
            from_username=x_dict['FromUserName']
            content=x_dict['Content'].strip()
            if content != '1':                  #发送来的内容不是'1'（‘1’请求下一页），即为查询关键字
                kv.delete(from_username) #remove kv user_dict
                rt,total_nums,current_page,total_page=query_library(content,'title','1')
                sub_rt=rt[0:9]            #display 9 items on weixin
                len_sub_rt=len(sub_rt)
                if len_sub_rt == 9:         #图书子结果是否等于9
                    if len(rt) > 9:         #如果查询图书结果大于9条，则保存
                        user_dict={'rt':rt,
                                   'next':9,
                                   'current_page':current_page,
                                   'total_page':total_page,
                                   'total_nums':total_nums,
                                   'key_word':content
                                   }
                        kv.set(from_username,user_dict)   #save
                    article_count='10'
                    title=u'查询关键字:%s 结果数:%s' %(content,total_nums)
                elif 0<len_sub_rt<9:                                        #图书结果大于0，小于9
                    article_count=len_sub_rt+2
                    title=u'查询关键字:%s 结果数:%s' %(content,total_nums)
                else:                                                           #无图书查询结果
                    article_count='1'
                    title=u'查询关键字:%s 结果数:%s' %(content,total_nums)
                    description=u'没有您要检索的馆藏书目！'

            else:       #查询下一页
                user_dict=kv.get(from_username)
                if user_dict:
                    _next=user_dict['next']
                    sub_rt=user_dict['rt'][_next:_next+9]
                    user_dict['next']+=9
                    kv.replace(from_username,user_dict)
                    len_sub_rt=len(sub_rt)
                    if len_sub_rt == 9:             #the number of response items about books is 45
                        article_count='10'
                        title=u'查询关键字:%s 结果数:%s' %(user_dict['key_word'],user_dict['total_nums'])
                        if sub_rt[-1] == user_dict['rt'][-1]:    #when go to the end index
                            if user_dict['current_page'] != user_dict['total_page']:
                                add_task(user_dict,'/task/',from_username)    # add task to sae queue to fetch next page
                            else:
                                kv.delete(from_username)          #if go to the end page delete user_dict,
                    else:
                        article_count=len_sub_rt+2
                        title=u'查询关键字:%s 结果数:%s' %(user_dict['key_word'],user_dict['total_nums'])
                        sub_rt=user_dict['rt'][_next:]
                        kv.delete(from_username) #remove kv user_dict
                else:
                    article_count='1'
                    title=u'没有更多的数据或查询下一页已过期' #return 'no more data'or'query outdate'

            create_time=str(int(time()))
            t=template.loader.get_template('news_response.xml')
            c=template.Context(locals())
            xml=t.render(c)
            return HttpResponse(xml,content_type='application/xml')
        else:
            return HttpResponse('False')
    else:
        return HttpResponse('False')


def fetch_next(request):
    if request.method=='GET':
        from_username=request.GET.get('from','0').encode('ascii')
        user_dict=kv.get(from_username)
        rt,total_nums,current_page,total_page=query_library(user_dict['key_word'],'title',user_dict['current_page']+1)
        user_dict.update({'rt':rt,'current_page':current_page,'next':0})
        kv.replace(from_username,user_dict)
        return HttpResponse('done')









