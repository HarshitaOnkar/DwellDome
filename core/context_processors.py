from .models import Home, Notification


def unread_notifications(request):
    if request.user.is_authenticated:
        try:
            home = request.user.home

            count = Notification.objects.filter(
                home=home,
                is_read=False
            ).count()

        except Home.DoesNotExist:
            count = 0

        return {
            'unread_notifications_count': count
        }

    return {
        'unread_notifications_count': 0
    }