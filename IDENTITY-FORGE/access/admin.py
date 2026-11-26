from django.contrib import admin

from access.models import (
    AccessEvent,
    AccessResource,
    AccessReview,
    Permission,
    Role,
    RoleAssignment,
)

for model in (Permission, Role, RoleAssignment, AccessResource, AccessEvent, AccessReview):
    admin.site.register(model)
