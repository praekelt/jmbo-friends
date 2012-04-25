from django.contrib import admin

from friends.models import MemberFriend, BadgeGroup, Badge, MemberBadge

admin.site.register(MemberFriend)
admin.site.register(BadgeGroup)
admin.site.register(Badge)
admin.site.register(MemberBadge)