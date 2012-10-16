# xxx: massive security holes due to use of hidden form variables. You can 
# inject messages into any thread. Need to refactor.

from django import forms
from django.contrib.sites.models import get_current_site
from django.template.loader import render_to_string
from django.utils.translation import ugettext, ugettext_lazy as _
from django.conf import settings
from django.core.urlresolvers import reverse
from foundry.forms import as_div

from friends import models


class FriendRequestForm(forms.ModelForm):
    """This form does not follow the usual style since we do not want any 
    fields to render."""

    class Meta:
        model = models.MemberFriend
        fields = []

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request')
        super(FriendRequestForm, self).__init__(*args, **kwargs)
        self._meta.fields = ('member', 'friend', 'state')

    def clean(self):
        cleaned_data = super(FriendRequestForm, self).clean()
        member = self.initial['member']
        friend = self.initial['friend']
        if member == friend:
            raise forms.ValidationError(
                _("You may not be friends with yourself.")
            )

        q = models.MemberFriend.objects.filter(member=member, friend=friend)
        if q.filter(state='invited').exists():
            raise forms.ValidationError(
                _("You have already sent a friend request to %s." % friend.username)
            )
        if q.filter(state='accepted').exists():
            raise forms.ValidationError(
                _("You are already friends with %s." % friend.username)
            )
        if q.filter(state='declined').exists():
            raise forms.ValidationError(
                _("You may not be friends with %s." % friend.username)
            )
        cleaned_data['member'] = member
        cleaned_data['friend'] = friend
        cleaned_data['state'] = 'invited'
        return cleaned_data

    def save(self, commit=True):
        instance = super(FriendRequestForm, self).save(commit=commit)

        # Send mail
        current_site = get_current_site(self.request)
        extra = dict(
            memberfriend_id=instance.id,
            username=instance.member.username,
            site_name=current_site.name, 
            domain=current_site.domain,
        )
        content = render_to_string('friends/friend_request_email.html', extra)
        try:
            send_mail(
                _("You have a new friend request from %(username)s on %(site_name)s") % extra, 
                content, settings.DEFAULT_FROM_EMAIL, [instance.friend.email]
            )
        except:
            pass

        return instance

    as_div = as_div
    
class SearchFriendsForm(forms.Form):
    username = forms.CharField(required=False)
    first_name = forms.CharField(required=False)
    last_name = forms.CharField(required=False)
    mobile_number = forms.CharField(required=False)
    email = forms.CharField(required=False)
    
    def search(self, queryset):
        has_search_criteria = False
        
        if self.cleaned_data.has_key('username') and self.cleaned_data['username'].strip():
            has_search_criteria = True
            queryset = queryset.filter(username__icontains=self.cleaned_data['username'])
            
        if self.cleaned_data.has_key('first_name') and self.cleaned_data['first_name'].strip():
            has_search_criteria = True
            queryset = queryset.filter(first_name__icontains=self.cleaned_data['first_name'])
            
        if self.cleaned_data.has_key('last_name') and self.cleaned_data['last_name'].strip():
            has_search_criteria = True
            queryset = queryset.filter(last_name__icontains=self.cleaned_data['last_name'])
            
        if self.cleaned_data.has_key('mobile_number') and self.cleaned_data['mobile_number'].strip():
            has_search_criteria = True
            queryset = queryset.filter(mobile_number__icontains=self.cleaned_data['mobile_number'])
            
        if self.cleaned_data.has_key('email') and self.cleaned_data['email'].strip():
            has_search_criteria = True
            queryset = queryset.filter(email__icontains=self.cleaned_data['email'])
        
        if has_search_criteria:
            return queryset
        else:
            return queryset.empty()
        
    as_div = as_div


class SendDirectMessageForm(forms.ModelForm):
    
    class Meta:
        model = models.DirectMessage
        fields = ('from_member', 'to_member', 'message', )
        
    def __init__(self, from_member, *args, **kwargs):
        self.base_fields['from_member'].initial = from_member
        self.base_fields['from_member'].widget = forms.HiddenInput()       
        self.base_fields['to_member'].queryset = from_member.get_friends()  
        self.base_fields['message'].label = ugettext('Message')
        #self.base_fields['message'].widget.attrs.update({'class':'commentbox'})
        super(SendDirectMessageForm, self).__init__(*args, **kwargs)
         
    as_div = as_div


class SendDirectMessageInlineForm(forms.ModelForm):
    
    class Meta:
        model = models.DirectMessage
        fields = ('from_member', 'to_member', 'message', )
        
    def __init__(self, from_member, to_member, *args, **kwargs):
        self.base_fields['from_member'].initial = from_member
        self.base_fields['from_member'].widget = forms.HiddenInput()
        self.base_fields['to_member'].initial = to_member
        self.base_fields['to_member'].widget = forms.HiddenInput()
        self.base_fields['message'].label = ugettext('Message')
        #self.base_fields['message'].widget.attrs.update({'class':'commentbox'})        
        super(SendDirectMessageInlineForm, self).__init__(*args, **kwargs)
        
    as_div = as_div

    def save(self, *args, **kwargs):
        object = super(SendDirectMessageInlineForm, self).save(*args, **kwargs)
        object.username = object.to_member.username
        return object


class ReplyToDirectMessageForm(SendDirectMessageInlineForm):
    
    class Meta:
        model = models.DirectMessage
        fields = ('from_member', 'to_member', 'message', 'reply_to',)
    
    def __init__(self, from_member, to_member, reply_to, *args, **kwargs):
        self.base_fields['reply_to'].initial = reply_to
        self.base_fields['reply_to'].widget = forms.HiddenInput()
        self.base_fields['message'].label = ugettext('Message')
        super(ReplyToDirectMessageForm, self).__init__(from_member, to_member, *args, **kwargs)
        
#    def save(self, *args, **kwargs):
#        obj = super(ReplyToDirectMessageForm, self).save(*args, **kwargs)
#        obj.reply_to.state = 'sent'
#        obj.reply_to.save()
#        return obj
