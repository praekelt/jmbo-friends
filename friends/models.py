from django.db import models
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _, ugettext

from foundry.models import Member, Link, Notification

import friends.monkey


def can_friend(self, friend):
        # Can't friend yourself
        if self == friend:
            return False
        return not MemberFriend.objects.filter(
            Q(member=self, friend=friend) | Q(member=friend, friend=self)
        ).exists()
                    

def get_friends_with_ids(self, exlude_ids=[], limit=0):
        # todo: find a better way to query for friends
        values_list = MemberFriend.objects.filter(
            Q(member=self)|Q(friend=self), 
            state='accepted'
        ).values_list('member', 'friend')
        ids = []
        for member_id, friend_id in values_list:
            if self.id != member_id:
                if member_id not in exlude_ids:
                    ids.append(member_id)
            if self.id != friend_id:
                if friend_id not in exlude_ids:
                    ids.append(friend_id)
        if limit > 0:
            return Member.objects.filter(id__in=ids).order_by('?')[0:limit], ids
        else:
            return Member.objects.filter(id__in=ids).order_by('?'), ids


def get_friends(self):
        friends, _ = self.get_friends_with_ids()
        return friends 


def get_5_random_friends(self, exlude_ids=[]):
        friends, _ = self.get_friends_with_ids(exlude_ids, 5)
        return friends


five_random_friends = property(get_5_random_friends)


# Add to class
Member.can_friend = can_friend
Member.get_friends_with_ids = get_friends_with_ids
Member.get_friends = get_friends
Member.get_5_random_friends = get_5_random_friends
Member.five_random_friends = five_random_friends


class MemberFriend(models.Model):
    member = models.ForeignKey(Member, related_name='member_friend_member')
    friend = models.ForeignKey(Member, related_name='member_friend_friend')
    state = models.CharField(
        max_length=32,
        default='invited',
        db_index=True,
        choices=(
            ('invited', 'Invited'),
            ('accepted', 'Accepted'),
            ('declined', 'Declined')
        )
    )
    
    def save(self, *args, **kwargs):        
        is_new = not self.id

        super(MemberFriend, self).save(*args, **kwargs)        

        if is_new:
            link, dc = Link.objects.get_or_create(
                title=ugettext("You have pending friend requests"), view_name='my-friend-requests'
            )
            Notification.objects.get_or_create(member=self.friend, link=link)

    def accept(self):
        self.state = 'accepted'
        self.save()

        # Delete notifications if no more friend requests        
        if not MemberFriend.objects.filter(friend=self.friend, state='invited').exclude(id=self.id).exists():
            link, dc = Link.objects.get_or_create(
                title=ugettext("You have pending friend requests"), view_name='my-friend-requests'
            )
            for obj in Notification.objects.filter(member=self.friend, link=link):
                obj.delete()


    def defriend(self):
        # Setting state to declined means we can never be friends ever again
        self.state = 'declined'
        self.save()


class DirectMessage(models.Model):
    root_direct_message = models.ForeignKey('self', null=True, blank=True, editable=False)
    from_member = models.ForeignKey(Member, related_name='sent_items')
    to_member = models.ForeignKey(Member, related_name='inbox')
    message = models.TextField()
    reply_to = models.ForeignKey('DirectMessage', related_name='replies', null=True, blank=True)
    state = models.CharField(
        max_length=32,
        default='sent',
        db_index=True,
        choices=(
            ('sent', 'Sent'),
            ('read', 'Read'),
            ('archived', 'Archived')
        )
    )
    created = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs): 
        is_new = not self.id

        super(DirectMessage, self).save(*args, **kwargs)

        if is_new:
            if not self.reply_to:
                self.root_direct_message = self
            else:
                self.root_direct_message = self.reply_to.root_direct_message
            self.save()
