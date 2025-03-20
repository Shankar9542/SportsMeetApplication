from django.contrib.auth.models import Group

def user_group_context(request):
    """Returns whether the user belongs to the 'owner' or 'customer' group."""
    if request.user.is_authenticated:
        is_owner = request.user.groups.filter(name__iexact="owner").exists()  # Case-insensitive check
        is_customer = request.user.groups.filter(name__iexact="customer").exists()  # Case-insensitive check
        return {'is_owner': is_owner, 'is_customer': is_customer}
    
    return {'is_owner': False, 'is_customer': False}

