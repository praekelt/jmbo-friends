import random

from django import template
from django.core.cache import cache

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


@register.inclusion_tag('friends/inclusion_tags/suggested_friends.html')
def suggested_friends(member):
    """
    Displays a list of suggested friends.
    """
    try:
        CACHE_KEY = 'JMBO_SUGGESTED_FRIENDS_MEMBER_ID_%d' % member.id
        suggested_friend_ids = cache.get(CACHE_KEY)
        if suggested_friend_ids:
            suggested_friends = Member.objects.filter(pk__in=suggested_friend_ids)
        else:
            #friends, exclude_ids = Member.objects.get(id=user.member.id).get_friends_with_ids()
            friends, exclude_ids = member.get_friends_with_ids()
            exclude_ids.append(member.id)
            suggested_friends = []
            for friend in friends:
                friend.other_friends, friend_ids = friend.get_friends_with_ids(exclude_ids, 5)
                for suggested_friend in friend.other_friends:
                    suggested_friends.append(suggested_friend) 
                exclude_ids.extend(friend_ids)
                
            if len(suggested_friends) > 5:
                suggested_friends = random.sample(suggested_friends, 5)
                
            cache.set(CACHE_KEY, [fr.id for fr in suggested_friends], 60 * 5)
        
        return { 'suggested_friends' : suggested_friends }
    except:
        pass
    
    return {}


@register.inclusion_tag('friends/inclusion_tags/direct_message.html')
def direct_message(direct_message):
    """
    Iterates through all the message replies.
    """
    # xxx: what is the point? Looks redundant.
    return {'object' : direct_message}
