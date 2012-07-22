from django.db import models
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from enote.enml import enml2html

class ENoteProfile(models.Model):
    euserid = models.IntegerField(unique=True)
    user = models.ForeignKey(User, db_index=True, null=True)
    edam_data = models.TextField()
    auth_token = models.CharField(max_length=512)
    note_store_url = models.CharField(max_length=200)
    shard_id = models.CharField(max_length=21)
    last_synced = models.DateTimeField(db_index=True, blank=True, null=True)
    update_count = models.IntegerField(default=0)
    
    class Meta:
        verbose_name = 'Profile'

    def get_absolute_url(self):
        return '/%s' % self.user.username

class Notebook(models.Model):
    guid = models.CharField(max_length=40, primary_key=True)
    name = models.CharField(max_length=200, blank=True, null=True, db_index=True)
    user = models.ForeignKey(User, related_name='notebooks', db_index=True, null=True, blank=True)
    cnt_note = models.IntegerField(db_index=True, default=0)
    update_seq = models.IntegerField(db_index=True, default=0)

    def update_cnt(self, save=False):
        self.cnt_note = Note.objects.filter(notebook=self).count()
        if save:
            self.save()
    
    def get_absolute_url(self):
        return reverse('notebook_page',
                       kwargs={'notebook_id': self.guid})
    
class Note(models.Model):
    guid = models.CharField(max_length=40, primary_key=True)
    notebook = models.ForeignKey(Notebook, related_name='notes', db_index=True, null=True, blank=True)
    user = models.ForeignKey(User, related_name='notes', db_index=True, null=True, blank=True)
    title = models.CharField(max_length=200, db_index=True)
    content = models.TextField()
    html_content = models.TextField(blank=True, null=True)
    date_created = models.DateTimeField(db_index=True, blank=True, null=True)
    date_updated = models.DateTimeField(db_index=True, blank=True, null=True)
    date_deleted = models.DateTimeField(db_index=True, blank=True, null=True)
    update_seq = models.IntegerField(db_index=True, default=0)

    class Meta:
        pass
    
    def __unicode__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('blog_item', kwargs={'note_id': self.guid})

    def get_html_content(self):
        if self.html_content is None:
            self.html_content = enml2html(self)
            self.save()
        return self.html_content

class Resource(models.Model):
    guid = models.CharField(max_length=40, primary_key=True)
    note = models.ForeignKey(Note, related_name='resources', db_index=True, blank=True, null=True)
    file = models.FileField(upload_to="%Y%m%d", blank=True, null=True)
    hash = models.CharField(max_length=40, db_index=True, blank=True, null=True)
    mime = models.CharField(max_length=40, default='image/jpeg')
