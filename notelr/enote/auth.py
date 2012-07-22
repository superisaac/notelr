import oauth2 as oauth
import urllib
import urlparse
from django.conf import settings


class OAuthAgent(object):
    can_auth = True
    api_host = settings.EVERNOTE_HOST
    service_host = settings.EVERNOTE_HOST

    def get_auth_url(self):
        return '/auth'

    def request_token_url(self, **kw):
        params = urllib.urlencode(kw)
        a = 'https://%s/oauth' % self.service_host
        if params:
            a += '?' + params
        return a

    def access_token_url(self):
        return 'https://%s/oauth' % self.service_host

    def authorize_url(self):
        return 'https://%s/OAuth.action' % self.service_host

    def get_consumer(self):
        consumer = oauth.Consumer(key=settings.EVERNOTE_KEY,
                                  secret=settings.EVERNOTE_SECRET)
        return consumer

    def get_client(self):
        consumer = self.get_consumer()
        client = oauth.Client(consumer, self.agent_token)
        return client

    def request(self, url, *args, **kw):
        from models import AuthInfo
        if self.agent_token is None:
            self.agent_token = self.get_oauth_token_from_pool(self.service_id)

        if url.startswith('/'):
            url = 'http://%s%s' % (self.api_host, url)
        client = self.get_client()
        res, content = client.request(url, *args, **kw)
        if str(res['status']) != '200':
            raise AgentException(res, content)
        return content
    
    def request_json(self, url, *args, **kw):
        try:
            content = self.request(url, *args, **kw)
        except AgentException:
            import traceback
            traceback.print_exc()
            return []
        return json.loads(content)

    def get_request_token(self, callback_url):
        consumer = self.get_consumer()
        client = oauth.Client(consumer)
        resp, content = client.request(self.request_token_url(oauth_callback=callback_url),
                                       'GET')
        print 'request content', content
        req_token = dict(urlparse.parse_qsl(content))
        return req_token
