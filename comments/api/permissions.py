from rest_framework.permissions import BasePermission


class IsObjectOwner(BasePermission):
    # this checks if the user is the owner of the object
    # if detail=False, only check has_permission() method
    # if detail=True, check both has_permission() and has_object_permission()
    message = "You don't have permission to access this object"

    def has_permission(self, request, view):
        return True

    def has_object_permission(self, request, view, obj):
        return request.user == obj.user
