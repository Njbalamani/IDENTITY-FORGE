from django.contrib import admin

from identities.models import IdentityProfile, Team

admin.site.register(Team)
admin.site.register(IdentityProfile)
