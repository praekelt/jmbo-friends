from optparse import make_option

from django.core.management.base import BaseCommand
from django.db import connection
from django.db.models import Q

from friends.models import MemberFriend


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--delete',
            action='store_true',
            dest='delete',
            help='Delete duplicate records'
        ),
    )
    help = "Finds duplicate friendships, optionally deletes them"

    def handle(self, *args, **options):
        cursor = connection.cursor()
        cursor.execute("""SELECT GREATEST(member_id, friend_id) AS member1,
            LEAST(member_id, friend_id) AS member2, min(id) FROM friends_memberfriend
            WHERE state = 'accepted' GROUP BY member1, member2 HAVING count(id) > 1""")
        duplicates = cursor.fetchall()
        print "There are %d duplicates" % len(duplicates)
        if options['delete']:
            print "Deleting duplicates..."
            for d in duplicates:
                MemberFriend.objects.filter(Q(member=d[0], friend=d[1]) |
                    Q(member=d[1], friend=d[0]), ~Q(pk=d[2]),
                    state='accepted').delete()
            print "Duplicates deleted"
