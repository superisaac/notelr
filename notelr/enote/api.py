import thrift.protocol.TBinaryProtocol as TBinaryProtocol
import thrift.transport.THttpClient as THttpClient
import evernote.edam.userstore.UserStore as UserStore
import evernote.edam.userstore.constants as UserStoreConstants
import evernote.edam.notestore.NoteStore as NoteStore
from django.conf import settings

EVERNOTE_HOST = getattr(settings, 'EVERNOTE_HOST', 'sandbox.evernote.com')
USER_STORE_URI = "https://" + EVERNOTE_HOST + "/edam/user"

class ENoteClient(object):
    user_store = None
    note_store = None

    def __init__(self, token):
        self.auth_token = token
    
    def get_user_store(self):
        if self.user_store is None:
            client = THttpClient.THttpClient(USER_STORE_URI)
            protocol = TBinaryProtocol.TBinaryProtocol(client)
            self.user_store = UserStore.Client(protocol)
        return self.user_store

    def get_note_store(self):
        if self.note_store is None:
            user_store = self.get_user_store()
            note_store_url = user_store.getNoteStoreUrl(self.auth_token)
            client = THttpClient.THttpClient(note_store_url)
            protocol = TBinaryProtocol.TBinaryProtocol(client)
            self.note_store = NoteStore.Client(protocol)
        return self.note_store



        
