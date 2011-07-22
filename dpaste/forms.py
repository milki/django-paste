from django import forms
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from dpaste.models import Snippet
from dpaste.highlight import LEXER_LIST_ALL, LEXER_LIST, LEXER_DEFAULT
import datetime

import logging

#===============================================================================
# Snippet Form and Handling
#===============================================================================

class SnippetForm(forms.ModelForm):

    content = forms.CharField(label='Log',widget=forms.Textarea(attrs={'cols': 80, 'rows': 38}))
    
    def __init__(self, request, *args, **kwargs):
        super(SnippetForm, self).__init__(*args, **kwargs)
        self.request = request
        
        if kwargs.has_key('initial'):
            initial = kwargs['initial']
            self.fields['content'].initial = initial['content']

        if kwargs.has_key('data'):
            data = kwargs['data']
            self.instance.content = data['content']
            

    def save(self, parent=None, *args, **kwargs):
        # Set parent snippet
        if parent:
            self.instance.parent = parent

        # Save snippet in the db
        super(SnippetForm, self).save(*args, **kwargs)

        # Add the snippet to the user session list
        if self.request.session.get('snippet_list', False):
            self.request.session['snippet_list'] += [self.instance.pk]
        else:
            self.request.session['snippet_list'] = [self.instance.pk]

        return self.request, self.instance

    class Meta:
        model = Snippet
        fields = (
            'branch',
            'content',
        )


#===============================================================================
# User Settings
#===============================================================================

USERPREFS_FONT_CHOICES = [(None, _(u'Default'))] + [
    (i, i) for i in sorted((
        'Monaco',
        'Bitstream Vera Sans Mono',
        'Courier New',
        'Consolas',
    ))
]

USERPREFS_SIZES = [(None, _(u'Default'))] + [(i, '%dpx' % i) for i in range(5, 25)]

class UserSettingsForm(forms.Form):

    default_name = forms.CharField(label=_(u'Default Name'), required=False)
    display_all_lexer = forms.BooleanField(
        label=_(u'Display all lexer'), 
        required=False,
        widget=forms.CheckboxInput,
        help_text=_(u'This also enables the super secret \'guess lexer\' function.'),
    )
    font_family = forms.ChoiceField(label=_(u'Font Family'), required=False, choices=USERPREFS_FONT_CHOICES)
    font_size = forms.ChoiceField(label=_(u'Font Size'), required=False, choices=USERPREFS_SIZES)
    line_height = forms.ChoiceField(label=_(u'Line Height'), required=False, choices=USERPREFS_SIZES)
