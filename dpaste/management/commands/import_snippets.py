import datetime
import sys
import re
from optparse import make_option
from django.core.management.base import CommandError, LabelCommand
from dpaste.models import Snippet
from django.conf import settings

from dulwich.repo import Repo
from dulwich.object_store import tree_lookup_path
from dulwich.objects import Blob

# 100 years 
EXPIRE = datetime.datetime.now() + \
          datetime.timedelta(seconds=int(3600 * 24 * 30 * 12 * 100))

class Command(LabelCommand):
    option_list = LabelCommand.option_list + (
        make_option('--commit', '-c', action='store_true', dest='commit', 
            help='Commit to db.'),
    )
    help = "Import snippets"

    def handle(self, *args, **options):
        repo = Repo(getattr(settings, 'DPASTE_GITREPO', None))
        sys.stdout.write(u"Reading snippets from %s...\n" % (repo.path))

        allbranches = list(repo.refs.keys())
        allbranches.sort()

        if repo.has_index():
            branches = [ branch for branch in allbranches if not re.search('master|HEAD|scripts',branch) ]
        else:
            branches = [ branch for branch in allbranches if not re.search('remotes|master|HEAD|scripts',branch) ]

        new_snippets = []
        for branch_ref in branches:
            sha = repo[branch_ref].id
            logtitle = re.sub(r".*/","",branch_ref)
            try:
                if not Snippet.objects.filter(title=logtitle,sha1=sha):
                    new_snippets.append(Snippet(title=logtitle,
                                                sha1=sha,
                                                expires=EXPIRE))
            except UnicodeError:
                sys.stdout.write(u"Failed to create - {0}\n".format(logtitle))
                next
        sys.stdout.write(u"%s snippets found\n" % len(new_snippets))
        for c in new_snippets:
            sys.stdout.write(u"{0} - {1} : {2}\n".format(c.title, c.sha1,
                                                         c.filename))
        if options.get('commit'):
            [ snippet.save(nocommit=True) for snippet in new_snippets ]
            sys.stdout.write(u"%s snippets created\n" % len(new_snippets))
        else:
            sys.stdout.write(u'Dry run - Doing nothing! *crossingfingers* (-c to commit changes)\n')
