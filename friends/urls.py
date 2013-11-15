from django.conf.urls.defaults import patterns, url, include
from django.utils.translation import ugettext_lazy as _
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.conf import settings
from django.contrib.auth.decorators import login_required


from friends import views, forms

urlpatterns = patterns('',

    # Member detail page
    url(r'^members/(?P<username>[=@\.\w+-]+)/$',
        views.MemberDetail.as_view(
            form_class=forms.SendDirectMessageInlineForm,
            template_name='friends/member_detail.html'
        ),
        name='member-detail'
    ),

    # Friend request
    url(
        r'^friend-request/(?P<member_id>\d+)/$',
        login_required(views.friend_request),
        {},
        name='friend-request'
    ),

    # My friends
    url(
        r'^my-friends/$',
        login_required(views.my_friends),
        {'template_name':'friends/my_friends.html'},
        name='my-friends'
    ),

    # My friend requests
    url(
        r'^my-friend-requests/$',
        login_required(views.my_friend_requests),
        {'template_name':'friends/my_friend_requests.html'},
        name='my-friend-requests'
    ),

    # Accept friend request
    url(
        r'^accept-friend-request/(?P<memberfriend_id>\d+)/$',
        login_required(views.accept_friend_request),
        {},
        name='accept-friend-request'
    ),

    # De-friend a member
    url(
        r'^de-friend/(?P<member_id>\d+)/$',
        login_required(views.de_friend),
        {},
        name='de-friend'
    ),

    # Messaging
    url(r'^inbox/$',
        login_required(views.Inbox.as_view(template_name='friends/inbox.html')),
        name='inbox'
    ),
    url(r'^message/send/$',
        login_required(
            views.SendDirectMessage.as_view(
                form_class=forms.SendDirectMessageForm,
                template_name='friends/send_direct_message.html'
            )
        ),
        name='send-direct-message'
    ),
    url(r'^message/(?P<pk>\d+)/view/$',
        login_required(
            views.ViewMessage.as_view(
                template_name='friends/message_view.html'
            )
        ),
        name='message-view'
    ),
    url(r'^message/(?P<pk>\d+)/reply/$',
        login_required(
            views.ReplyToDirectMessage.as_view(
                form_class=forms.ReplyToDirectMessageForm,
                template_name='friends/reply_to_direct_message.html'
            )
        ),
        name='reply-to-direct-message'
    ),

)
