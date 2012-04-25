'''
Created on 08 Apr 2012

@author: euan
'''
from django.core.management.base import BaseCommand
from django.db.models import Q

from foundry import models

class Command(BaseCommand):
    """
    Calculates and awards badges to members
    """
    def handle(self, *args, **options):
        # Get the latest activities - we assume the site is busy, so we'll only look at the new ones.
        latest_activities = models.UserActivity.objects.filter(checked_for_badges=False)

        # Get a list of active members and work only with them.
        active_members = models.Member.objects.filter(pk__in=[activity.user.id for activity in latest_activities])
        
        # Only need to check active members - ignore the inactive ones for now. 
        for member in active_members:
            
            FRIENDS = Q(group__type=models.BadgeGroup.TYPE_FRIENDS, 
                        threshold__lte=member.get_friends().count())
            
            COMMENTS = Q(group__type=models.BadgeGroup.TYPE_COMMENTS, 
                         threshold__lte=member.number_of_comments)
            
            # Get all the badges a member is entitled to.
            for badge in models.Badge.objects.filter(FRIENDS | COMMENTS):
                # Award member new badge, if not already in possession of it. 
                _, created = models.MemberBadge.objects.get_or_create(member=member, badge=badge)
            
                if created:
                    # Notify the user of the new badge.
                    # Notification gets deleted when they view their badges.
                    link, _ = models.Link.objects.get_or_create(title='You have been awarded a new badge.', 
                                                                view_name='my-badges')
                    models.Notification.objects.get_or_create(member=member, link=link)
        
        # Mark them, so we don't have to check them again.
        latest_activities.update(checked_for_badges=True)