import datetime
import sys
import re
from optparse import make_option
from django.core.management.base import CommandError, LabelCommand
from dpaste.models import Snippet
from dpaste.settings import *

from dulwich.repo import Repo
from dulwich.object_store import tree_lookup_path
from dulwich.objects import Blob

class Command(LabelCommand):
    option_list = LabelCommand.option_list + (
        make_option('--commit', '-c', action='store_true', dest='commit', 
            help='Commit to db.'),
    )
    help = "Import snippets"

    def extract_log(x): return re.sub(r".*/","#",x)

    def handle(self, *args, **options):
        repo = Repo(GITREPO)
        sys.stdout.write(u"Reading snippets from %s...\n" % (repo.path))

        allbranches = list(repo.refs.keys())
        allbranches.sort()

        if repo.has_index():
            branches = [ branch for branch in allbranches if not re.search('master|HEAD',branch) ]
        else:
            branches = [ branch for branch in allbranches if not re.search('remotes|master|HEAD',branch) ]

        new_snippets = []
        for branch_ref in branches:
            try:
                if not Snippet.objects.filter(branch="%s" % (branch_ref)):
                    new_snippets.append( Snippet(branch="%s" % (branch_ref)) )
            except UnicodeError:
                sys.stdout.write(u"Failed to create - %s\n" % (branch_ref))
                next
        sys.stdout.write(u"%s snippets found\n" % len(new_snippets))
        for c in new_snippets:
            sys.stdout.write(u"%s - %s\n" % (c.branch,c.title))
        if options.get('commit'):
            [ snippet.save() for snippet in new_snippets ]
            sys.stdout.write(u"%s snippets created\n" % len(new_snippets))
        else:
            sys.stdout.write(u'Dry run - Doing nothing! *crossingfingers*\n')
