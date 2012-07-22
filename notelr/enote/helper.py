from django.http import HttpResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

def make_page(request, qs, pagesize=10, pagefield='page'):
    paginator = Paginator(qs, pagesize)
    pagenum = request.GET.get(pagefield)
    try:
        objs = paginator.page(pagenum)
    except (PageNotAnInteger, TypeError):
        objs = paginator.page(1)
    except EmptyPage:
        objs = paginator.page(paginator.num_pages)    
    return objs

def http_error(code, msg):
    resp = HttpResponse(msg)
    resp.status_code = code
    return resp
