import logging
import sys
import hashlib
import binascii
import time
from datetime import datetime
from django.core.files.base import ContentFile

import evernote.edam.notestore.NoteStore as NoteStore
import evernote.edam.type.ttypes as Types
import evernote.edam.error.ttypes as Errors
from enote.api import ENoteClient

from enote.models import *
from enml import enml2html

extmap = {
    'image/jpeg': '.jpg',
    'image/png': '.png',
    'image/gif': '.gif',
    }

class SyncNoteProcessor(object):
    def __init__(self, client, user):
        self.user_store = client.get_user_store()
        self.note_store = client.get_note_store()
        self.user = user
        self.token = user.get_profile().auth_token
        self.notebooks = {}

    def to_date(self, t):
        if t is None:
            return None
        tt = time.localtime(t/1000)
        return datetime(*tt[:6])

    def sync_notebook(self, nb_guid):
        nbobj = self.note_store.getNotebook(self.token, nb_guid)
        notebook, c = Notebook.objects.get_or_create(pk=nbobj.guid)
        if c or nbobj.updateSequenceNum > notebook.update_seq:
            notebook.pk = nbobj.guid
            notebook.user = self.user
            notebook.name = nbobj.name
            notebook.update_seq = nbobj.updateSequenceNum
            notebook.save()
        return notebook

    def sync_note(self, noteobj):
        # to find out if there is OK tag
        if (noteobj.tagGuids is None or 
            self.hit_tag_guid not in noteobj.tagGuids or
            self.hide_tag_guid in noteobj.tagGuids):
            print 'delete note', noteobj.guid
            logging.info('delete note %s' % noteobj.guid)
            Note.objects.filter(guid=noteobj.guid).delete()
            return
            
        note, created = Note.objects.get_or_create(pk=noteobj.guid)
        print 'seq num', noteobj.updateSequenceNum, note.update_seq

        if (created or
            noteobj.updateSequenceNum > note.update_seq):
            #### note.date_updated < self.to_date(noteobj.updated)):
            note.user = self.user
            note.guid = noteobj.guid
            note.update_seq = noteobj.updateSequenceNum

            note.notebook = self.sync_notebook(noteobj.notebookGuid)
            note.notebook.save()            

            note.title = noteobj.title
            note.content = self.note_store.getNoteContent(self.token,
                                                    noteobj.guid)
            note.date_created = self.to_date(noteobj.created)
            note.date_updated = self.to_date(noteobj.updated)
            note.date_deleted = self.to_date(noteobj.deleted)
            note.save()
            if noteobj.resources:
                for res in noteobj.resources:
                    self.sync_resource(note, res)
            note.html_content = enml2html(note)
            note.save()

        return note
        
    def sync_resource(self, note, resobj):
        hash = ''.join('%02x' % ord(c) for c in resobj.data.bodyHash)
        res, c = Resource.objects.get_or_create(pk=resobj.guid)
        if c or res.hash <> hash:
            resobj = self.note_store.getResource(self.token,
                                                 resobj.guid,
                                                 True, True, True, True)
            res.guid = resobj.guid
            res.hash = hash
            res.mime = resobj.mime
            res.note = note
            content = ContentFile(resobj.data.body)
            fn = hash + extmap.get(resobj.mime, '')
            res.file.save(fn, content)
            res.save()
        return res

    def get_hit_tag_guid(self):
        self.hit_tag_guid = None
        self.hide_tag_guid = None
        for tag in self.note_store.listTags(self.token):
            if tag.name == 'note2share':
                self.hit_tag_guid = tag.guid
            elif tag.name == 'hide':
                self.hide_tag_guid = tag.guid
            
    def full_sync(self, state, use_tag=True):
        self.get_hit_tag_guid()
        if not self.hit_tag_guid:
            # No tag, so don't look at it.
            return

        profile = self.user.get_profile()
        filter = NoteStore.NoteFilter()
        filter.ascending = False
        filter.words = 'tag:note2share'
        
        for start in xrange(10):
            noteList = self.note_store.findNotes(self.token,
                                                 filter,
                                                 start * 100, 100)
            if noteList is None:
                break
        
            for noteobj in noteList.notes:
                print 'note update_count', noteobj.updateSequenceNum, noteobj.title
                if profile.update_count < noteobj.updateSequenceNum:
                    self.sync_note(noteobj)

            if noteList is None and len(noteList) < 99:
                break
            else:
                time.sleep(0.2)

        for nb in Notebook.objects.filter(user=self.user):
            nb.update_cnt(save=True)

        profile.update_count = state.updateCount
        profile.last_synced = datetime.now()
        profile.save()

def make_sync(user):
    profile = user.get_profile()
    auth_token = profile.auth_token
    client = ENoteClient(auth_token)
    note_store = client.get_note_store()
    processor = SyncNoteProcessor(client, user)

    state = note_store.getSyncState(auth_token)
    print 'profile update_count', profile.update_count, 'vs.', state.updateCount
    if state.updateCount > profile.update_count:
        processor.full_sync(state)

def sync_note(noteid, profile):
    client = ENoteClient(profile.auth_token)
    note_store = client.get_note_store()
    noteobj = note_store.getNote(profile.auth_token,
                                 noteid, False,
                                 False, False, False)
    processor = SyncNoteProcessor(client, profile.user)
    processor.get_hit_tag_guid()
    if processor.hit_tag_guid:
        processor.sync_note(noteobj)
        for nb in Notebook.objects.filter(user=profile.user):
            nb.update_cnt(save=True)
    else:
        logging.warn('No tag notelr')

    
if __name__ == '__main__':
    #auth_token = 'S=s1:U=276b7:E=13f8a96a364:C=13832e57764:P=1cd:A=en-devtoken:H=db9b23a7bc6d99da8531371fd0b36923'
    user = User.objects.get(username='superisaac')
    make_sync(user)
