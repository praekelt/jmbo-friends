import random

from django.views.generic import DetailView, FormView, ListView, CreateView, UpdateView, TemplateView
from django.views.generic.list import BaseListView
from django.shortcuts import get_object_or_404, render_to_response
from django.db.models import Q
from django.template import RequestContext
from django.template.loader import render_to_string
from django.utils.translation import ugettext as _
from django.contrib import messages
from django.contrib.sites.models import Site
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.core.cache import cache
from django.core.mail import send_mail
from django.conf import settings


from jmbo.generic.views import GenericObjectDetail, GenericObjectList
from foundry.models import Member, Notification, Link

from friends.models import MemberFriend, DirectMessage
from friends.forms import FriendRequestForm

class MemberDetail(CreateView):
    
    def get_form_kwargs(self):
        kwargs = super(MemberDetail, self).get_form_kwargs()
        kwargs.update({'from_member': Member.objects.get(id=self.request.user.id),
                       'to_member': self.member,
                       })
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super(MemberDetail, self).get_context_data(**kwargs)
        
        context.update({'object' : self.member,
                        'is_self' : True if self.member.id == self.request.user.id else False,
                        'can_friend' : self.request.user.member.can_friend(self.member) if self.request.user.is_authenticated() and isinstance(self.request.user, Member) else False,
                        })
        return context
    
    def get(self, request, *args, **kwargs):
        username = kwargs.pop('username')
        self.member = get_object_or_404(Member, username=username)
        return super(MemberDetail, self).get(request, *args, **kwargs)
    
    def post(self, request, *args, **kwargs):
        username = kwargs.pop('username')
        self.member = get_object_or_404(Member, username=username)
        return super(MemberDetail, self).post(request, *args, **kwargs)

    def form_valid(self, form):
        msg = _("Your message has been sent.")
        messages.success(self.request, msg, fail_silently=True)
        return super(MemberDetail, self).form_valid(form)


class Inbox(ListView):
    
    def get_queryset(self):
        return DirectMessage.objects.filter(to_member=self.request.user).exclude(state='archived').order_by('-state', '-created')


class SendDirectMessage(CreateView):
   
    def get_form_kwargs(self):
        kwargs = super(SendDirectMessage, self).get_form_kwargs()
        kwargs.update({'from_member': self.request.user})
        return kwargs
 
    def get_success_url(self):
        return reverse('inbox')

    def form_valid(self, form):
        msg = _("Your message has been sent.")
        messages.success(self.request, msg, fail_silently=True)
        return super(SendDirectMessage, self).form_valid(form)


class ViewMessage(DetailView):
    
    def get_queryset(self):
        return DirectMessage.objects.filter(
            Q(to_member=self.request.user)|Q(from_member=self.request.user)
        )
    
    def get_object(self, *args, **kwargs):
        obj = super(ViewMessage, self).get_object(*args, **kwargs).root_direct_message
        # Mark all messages in thread sent to authenticated user as read
        DirectMessage.objects.filter(root_direct_message=obj, 
                                     to_member=self.request.user, 
                                     state='sent').update(state='read')
        return obj
    
    def get_context_data(self, **kwargs):
        context = super(ViewMessage, self).get_context_data(**kwargs)
        context.update({'unread_messages' : DirectMessage.objects.filter(to_member=self.request.user, state='sent').count()})
        return context
    

class ReplyToDirectMessage(CreateView):
    
    def get_queryset(self):
        return DirectMessage.objects.filter(Q(to_member__id=self.request.user.id) | Q(from_member__id=self.request.user.id))
    
    def get_object(self):
        try:
            return self.get_queryset().get(pk=self.kwargs['pk'])
        except DirectMessage.DoesNotExist:
            raise Http404(_(u"No DirectMessage found matching the query"))
    
    def get_form_kwargs(self):
        kwargs = super(ReplyToDirectMessage, self).get_form_kwargs()
        kwargs.update({'from_member': self.message.to_member if self.message.to_member.id == self.request.user.id else self.message.from_member,
                       'to_member': self.message.from_member if self.message.to_member.id == self.request.user.id else self.message.to_member,
                       'reply_to': self.message,
                       })
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super(ReplyToDirectMessage, self).get_context_data(**kwargs)
        context.update({'unread_messages' : DirectMessage.objects.filter(to_member__id=self.request.user.id, state='sent').count(),
                        'original_message' : self.message})
        return context
    
    def get(self, request, *args, **kwargs):
        self.message = self.get_object()
        return super(ReplyToDirectMessage, self).get(request, *args, **kwargs)
    
    def post(self, request, *args, **kwargs):
        self.message = self.get_object()
        return super(ReplyToDirectMessage, self).post(request, *args, **kwargs)
    
    def get_success_url(self):
        return reverse('inbox')

    def form_valid(self, form):
        msg = _("Your reply has been sent.")
        messages.success(self.request, msg, fail_silently=True)
        return super(ReplyToDirectMessage, self).form_valid(form)


def friend_request(request, member_id):
    member = get_object_or_404(Member, id=request.user.id)
    friend = get_object_or_404(Member, id=member_id)
    if request.method == 'POST':
        form = FriendRequestForm(
            request.POST, 
            initial=dict(member=member, friend=friend), 
            request=request
        )
        if form.is_valid():
            instance = form.save()
            msg = _("Your invitation has been sent to %s." % instance.friend.username)
            messages.success(request, msg, fail_silently=True)
            
            try:
                if friend.email:
                    subject = render_to_string('friends/email/friend_request_notification_subject.txt')
                    # Email subject *must not* contain newlines
                    subject = ''.join(subject.splitlines())
                    message = render_to_string('friends/email/friend_request_notification_message.txt', 
                                               {'member': member,
                                                'friend': friend,
                                                'current_site' : Site.objects.get_current()
                                                })
                    send_mail(subject, 
                              message, 
                              settings.DEFAULT_FROM_EMAIL, 
                              [friend.email])
            except:
                pass
                
            return HttpResponseRedirect(reverse('my-friends'))
    else:
        form = FriendRequestForm(
            initial=dict(member=request.user, friend=friend),
            request=request
        )

    extra = dict(form=form, friend=friend)
    return render_to_response('friends/friend_request_form.html', extra, context_instance=RequestContext(request))


class MyFriends(GenericObjectList):
    
    
    def get_queryset(self, *args, **kwargs):
        return self.request.user.get_friends()
    
    def get_paginate_by(self, *args, **kwargs):
        return 20

my_friends = MyFriends()


class MyFriendRequests(GenericObjectList):

    def get_queryset(self, *args, **kwargs):
        return MemberFriend.objects.filter(
            friend=self.request.user, state='invited'
        )

    def get_paginate_by(self, *args, **kwargs):
        return 20

my_friend_requests = MyFriendRequests()


def accept_friend_request(request, memberfriend_id):
    # This single check is sufficient to ensure a valid request
    # todo: friendlier page than a 404. Break it down do inform "you are 
    # already friends" etc.
    obj = get_object_or_404(
        MemberFriend, id=memberfriend_id, friend=request.user, state='invited'    
    )
    obj.accept()
    extra = {'username': obj.member.username}
    return render_to_response('friends/friend_request_accepted.html', extra, context_instance=RequestContext(request))


def de_friend(request, member_id):
    # todo: friendlier page than a 404.
    # todo: use Q
    try:
        obj = MemberFriend.objects.get(member=request.user, friend__id=member_id, state='accepted')
    except MemberFriend.DoesNotExist:
        try:
            obj = MemberFriend.objects.get(member__id=member_id, friend=request.user, state='accepted')
        except MemberFriend.DoesNotExist:
            return Http404('MemberFriend does not exist')
       
    obj.defriend()
    return HttpResponseRedirect(reverse('my-friends'))

class SearchView(FormView, ListView):
    """
    Get the fields that was completed in the form 
    Match the completed fields with the database
    """
    object_list = None

    def form_valid(self, form):
        self.object_list = form.search(self.get_queryset())
    
    def get(self, request, *args, **kwargs):
        return super(FormView, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        if form.is_valid():
            self.form_valid(form)
            context = super(BaseListView, 
                            self).get_context_data(object_list=self.object_list,
                                                   form=form)
            return self.render_to_response(context)
        else:
            return self.form_invalid(form)

class SuggestedFriends(TemplateView):
    
    def get_suggested_friends(self):
        suggested_friends = []
        member = self.request.user.member
        
        try:
            CACHE_KEY = 'JMBO_SUGGESTED_FRIENDS_MEMBER_ID_%d' % member.id
            suggested_friend_ids = cache.get(CACHE_KEY)
            if suggested_friend_ids:
                suggested_friends = Member.objects.filter(pk__in=suggested_friend_ids)
                return { 'suggested_friends' : suggested_friends }
            else:
                friends, exclude_ids = member.get_friends_with_ids()
                exclude_ids.append(member.id)
                
                for friend in friends:
                    friend.other_friends, friend_ids = friend.get_friends_with_ids(exclude_ids, 5)
                    for suggested_friend in friend.other_friends:
                        suggested_friends.append(suggested_friend) 
                    exclude_ids.extend(friend_ids)
                    
                if len(suggested_friends) > 5:
                    suggested_friends = random.sample(suggested_friends, 5)
        except:
            pass
        
        if not suggested_friends:
                
            suggestable_friends = Member.objects.exclude(pk=member.id).order_by('-last_login')[0:100]
            suggested_friends = random.sample(suggestable_friends, 5) if suggestable_friends.count() > 4 else suggestable_friends
        
        cache.set(CACHE_KEY, [fr.id for fr in suggested_friends], 60 * 5)
        
        return suggested_friends
    
    def get_context_data(self, **kwargs):
        return {
            'suggested_friends' : self.get_suggested_friends()
        }
        
        