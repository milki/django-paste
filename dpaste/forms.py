from django import forms
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from dpaste.models import Snippet
from dpaste.highlight import LEXER_LIST_ALL, LEXER_LIST, LEXER_DEFAULT
import datetime

#==============================================================================
# Snippet Form and Handling
#==============================================================================

EXPIRE_DEFAULT = 3600 * 24 * 30 * 12 * 100  # 100 years


class SnippetForm(forms.ModelForm):
    if not hasattr(Snippet, 'content'):
        content = forms.CharField(
            label='Content',
            widget=forms.Textarea(attrs={'cols': 80, 'rows': 38}))

    def __init__(self, request, *args, **kwargs):
        super(SnippetForm, self).__init__(*args, **kwargs)
        self.request = request

        if not hasattr(Snippet, 'content'):
            if 'initial' in kwargs:
                initial = kwargs['initial']
                self.fields['content'].initial = initial['content']

            if 'data' in kwargs:
                data = kwargs['data']
                content = data['content']
                self.instance.content = data['content'].replace('\r\n', '\n')

    def save(self, parent=None, *args, **kwargs):

        # Set parent snippet
        if parent:
            self.instance.parent = parent

        # Add expire datestamp
        self.instance.expires = datetime.datetime.now() + \
            datetime.timedelta(
                seconds=int(EXPIRE_DEFAULT))

        # Save snippet in the db
        super(SnippetForm, self).save(*args, **kwargs)

        # Add the snippet to the user session list
        if self.request.session.get('snippet_list', False):
            if len(self.request.session['snippet_list']) >= \
                    getattr(settings, 'MAX_SNIPPETS_PER_USER', 10):
                self.request.session['snippet_list'].pop(0)
            self.request.session['snippet_list'] += [self.instance.pk]
        else:
            self.request.session['snippet_list'] = [self.instance.pk]

        return self.request, self.instance

    class Meta:
        model = Snippet
        fields = (
            'title',
            'content',
        )
