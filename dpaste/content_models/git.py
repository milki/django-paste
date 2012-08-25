import datetime
import time
import stat
from mptt.models import MPTTModel, TreeForeignKey

from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.db.models.signals import post_init, pre_save, post_delete
from django.dispatch import receiver

from dpaste.highlight import pygmentize

from dulwich.repo import Repo
from dulwich.object_store import tree_lookup_path
from dulwich.objects import Blob, Commit, Tree


class GitSnippet(MPTTModel):
    parent = TreeForeignKey('self', null=True, blank=True,
                            related_name='children')
    title = models.CharField(_(u'Title'), max_length=120, blank=True)
    author = models.CharField(_(u'Author'), max_length=30, blank=True)
    published = models.DateTimeField(_(u'Published'), blank=True)
    sha1 = models.CharField(_(u'sha1'), max_length=40, null=True,
                            blank=False, unique=True)
    filename = models.CharField(_(u'sha1'), max_length=40,
                                null=True, blank=False)
    repo = Repo(getattr(settings, 'DPASTE_GITREPO', None))

    if repo is None:
        from django.core.exceptions import ImproperlyConfigured
        raise ImproperlyConfigured("Missing DPASTE_GITREPO")

    class Meta:
        ordering = ('-filename',)
        abstract = True

    class MPTTMeta:
        level_attr = 'mptt_level'
        order_insertion_by = ['filename']

    def __init__(self, *args, **kwargs):
        super(GitSnippet, self).__init__(*args, **kwargs)
        self.content = self.get_content()

    def save(self, *args, **kwargs):
        if not self.pk:
            self.published = datetime.datetime.now()

        blob = Blob.from_string(self.content.encode('UTF-8'))
        if self.parent:  # existing branch
            bcommit = self.repo.get_object(self.parent.sha1)
            tree = self.repo.get_object(bcommit.tree)
            self.filename = tree.entries()[0][1]
        else:  # new orphan branch
            tree = Tree()
            self.filename = blob.id

        tree[self.filename] = (stat.S_IFREG | 0644, blob.id)

        author = getattr(settings, 'DPASTE_COMMITTER', 'django-paste')
        message = getattr(settings, 'DPASTE_EDIT_MESSAGE', 'editted')

        commit = Commit()
        commit.tree = tree.id
        if self.parent:
            commit.parents = [bcommit.id]
        commit.author = commit.committer = author
        commit.commit_time = commit.author_time = int(time.time())
        commit.commit_timezone = commit.author_timezone = time.timezone
        commit.encoding = 'UTF-8'
        commit.message = message

        self.repo.object_store.add_object(blob)
        self.repo.object_store.add_object(tree)
        self.repo.object_store.add_object(commit)

        self.repo["refs/heads/%s" % self.filename] = commit.id

        self.sha1 = commit.id

        super(GitSnippet, self).save(*args, **kwargs)

    def get_content(self):
        if self.sha1:
            bcommit = self.repo.get_object(self.sha1)
            tree = self.repo.get_object(bcommit.tree)
            return self.repo.get_object(
                tree.entries()[0][2]).data.decode('UTF-8')
        else:
            return ''

    def remove_content(self):
        try:
            del self.repo["refs/heads/%s" % self.filename]
        except:
            pass
