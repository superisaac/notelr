import urllib
from datetime import datetime, timedelta
import urlparse
import oauth2 as oauth
import PyRSS2Gen
from django.contrib.auth.models import User
from django.shortcuts import render_to_response, redirect
from django.shortcuts import get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.template.context import RequestContext
from django.http import HttpResponse, Http404
from django.conf import settings

from enote.models import *
from enote.auth import OAuthAgent
from enote.sync import SyncNoteProcessor
from enote.api import ENoteClient
from enote.sync import sync_note
from enote.helper import make_page, http_error

def enote_logout(request):
    logout(request)
    return redirect('/')

def enote_oauth(request):
    agent = OAuthAgent()
    callback_url = request.build_absolute_uri('/auth/callback')
    req_token = agent.get_request_token(callback_url)
    request.session['request_token'] = req_token['oauth_token']
    request.session['request_token_secret'] = req_token['oauth_token_secret']

    params = urllib.urlencode({
            'oauth_token': req_token['oauth_token'],
            'oauth_callback': callback_url
            })
    aurl = '%s?%s' % (agent.authorize_url(), params)
    return redirect(aurl, code=302)

def enote_oauth_callback(request):
    agent = OAuthAgent()
    consumer = agent.get_consumer()
    request_token = request.GET.get('oauth_token')
    request_secret = request.session['request_token_secret']

    token = oauth.Token(request_token, request_secret)
    verifier = request.GET.get('oauth_verifier')
    if verifier:
        token.set_verifier(verifier)

    agent.agent_token = token
    client = agent.get_client()
    resp, content = client.request(agent.access_token_url(), 
                                   'GET')
    token_dict = dict(urlparse.parse_qsl(content))
    auth_token = token_dict['oauth_token']

    profile, c = ENoteProfile.objects.get_or_create(euserid=token_dict['edam_userId'])
    profile.auth_token = auth_token
    if c:
        client = ENoteClient(auth_token)
        user_store = client.get_user_store()
        userobj = user_store.getUser(client.auth_token)

        profile.shard_id = userobj.shardId

        user = User.objects.create_user(userobj.username,
                                        '%s@notlr.com' % userobj.username)
        user.set_password(userobj.username + '.asdf')
        user.save()
        profile.user = user
        profile.note_store_url = token_dict['edam_noteStoreUrl']
        profile.last_synced = datetime.now() - timedelta(seconds=settings.SYNC_INTERVAL)
        profile.save()

        # async 
        if 0:
            note_store = client.get_note_store()
            processor = SyncNoteProcessor(client,
                                          user)
            state = note_store.getSyncState(client.auth_token)
            if state.updateCount > profile.update_count:
                processor.full_sync(state, use_tag=True)

    else:
        profile.save()
        user = profile.user

    u = authenticate(username=user.username,
                     password=user.username + '.asdf')
    if u:
        login(request, u)
        return redirect(profile.get_absolute_url())
    else:
        return redirect('/')

def index(request):
    notes = Note.objects.all().order_by('-date_created')
    pagename = 'index'
    paged = make_page(request, notes)
    return render_to_response('index.html', 
                              RequestContext(request,
                                             locals()))

def notebook_page(request, notebook_id=None):
    notebook = get_object_or_404(Notebook,
                                 guid=notebook_id)
    return blog_notebook_page(request, notebook.user, notebook)

def blog_page(request, username=None):
    user = get_object_or_404(User,
                             username=username,
                             is_active=True)
    return blog_notebook_page(request, user, None)

def blog_notebook_page(request, puser, curr_nb):
    notebooks = Notebook.objects.filter(user=puser)
    if curr_nb:
        notes = Note.objects.filter(notebook=curr_nb).order_by('-date_created')
    else:
        notes = Note.objects.filter(user=puser).order_by('-date_created')
    pagename = puser.username
    paged = make_page(request, notes)
    return render_to_response('blog_page.html', 
                              RequestContext(request,
                                             locals()))

def blog_item(request, note_id=None):
    note = get_object_or_404(Note, guid=note_id)
    notebooks = Notebook.objects.filter(user=note.user_id)

    pagename = note.user.username
    return render_to_response('blog_item.html', 
                              RequestContext(request,
                                             locals()))

def change_callback(request):
    userId = request.GET.get('userId')
    if not userId:
        return http_error(400, "No userId")
    noteId = request.GET.get('guid')
    if not noteId:
        return http_error(400, "No noteId")

    reason = request.GET.get('reason', 'update')
    profile = get_object_or_404(ENoteProfile,
                                euserid=userId)
    if not profile.user.is_active:
        raise Http404

    sync_note(noteId, profile)
    return HttpResponse('ok')

def rss_page(request, username=None):
    puser = get_object_or_404(User,
                             username=username,
                             is_active=True)
    notes = puser.notes.order_by('-date_created')[:10]
    rssurl = request.build_absolute_uri(reverse('blog_page',
                                                kwargs={'username': username}))
    last_build = None
    items = []
    for note in notes:
        if (last_build is None or 
            last_build < note.date_created):
            last_build = note.date_created
        note_url = note.get_absolute_url()
        rssitem = PyRSS2Gen.RSSItem(
            title=note.title,
            link=note_url,
            description=note.get_html_content(),
            guid=PyRSS2Gen.Guid(note_url),
            pubDate=note.date_created
            )
        items.append(rssitem)

    if last_build is None:
        last_build = datetime.now()
    
    # render the rss
    rss = PyRSS2Gen.RSS2(
        title=u"%s's notes" % puser.username,
        link=rssurl,
        description='%s' % puser.username,
        lastBuildDate=last_build,
        items=items
        )

    resp = HttpResponse(rss.to_xml())
    resp.content_type = 'application/rss+xml'
    return resp

