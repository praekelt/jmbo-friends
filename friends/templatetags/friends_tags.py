from django import template

from foundry.models import Member, Notification

from friends.models import DirectMessage

register = template.Library()

@register.inclusion_tag('friends/inclusion_tags/my_friends.html')
def my_friends(member, my_friends):
    """
    Displays my friends and some of their's too.
    """
    # xxx: overkill. Should be a method on Member.
    friends, exclude_ids = Member.objects.get(id=member.id).get_friends_with_ids()
    exclude_ids.append(member.id)
    for friend in friends:
        friend.other_friends, friend_ids = friend.get_friends_with_ids(exclude_ids, 5)
        exclude_ids.extend(friend_ids)
    
    return { 'friends' : friends }

@register.inclusion_tag('friends/inclusion_tags/direct_message.html', takes_context=True)
def direct_message(context, direct_message):
    """
    Iterates through all the message replies.
    """
    return {'user': context['user'],
            'object' : direct_message
            }

@register.inclusion_tag('friends/inclusion_tags/message_count.html')
def message_count(user):
    """
    Displays the user's number of unread messages.
    """
    
    if hasattr(user,'member'):
        return { 'message_count' : DirectMessage.objects.filter(to_member__id=user.id, state='sent').count() }
    else:
        return { 'message_count' : 0 }
