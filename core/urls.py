from django.urls import path
from . import views

urlpatterns = [
    # Public
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),

    # Main
    path('dashboard/', views.dashboard, name='dashboard'),
    path('search/', views.global_search, name='global_search'),
    path('notifications/', views.notifications, name='notifications'),
    path(
        'notifications/<int:notification_id>/read/',
        views.mark_notification_read,
        name='mark_notification_read'
    ),
    path('profile/', views.profile, name='profile'),
    path('settings/', views.settings, name='settings'),
    path('analytics/', views.analytics, name='analytics'),

    # Warranties
    path('warranties/', views.warranties, name='warranties'),
    path(
        'warranties/add/',
        views.add_warranty,
        name='add_warranty'
    ),
    path(
        'my-home/asset/<int:asset_id>/add-warranty/',
        views.add_warranty_for_asset,
        name='add_warranty_for_asset'
    ),
    path(
        'my-home/warranty/<int:warranty_id>/edit/',
        views.edit_warranty,
        name='edit_warranty'
    ),
    path(
        'my-home/warranty/<int:warranty_id>/delete/',
        views.delete_warranty,
        name='delete_warranty'
    ),

    # Maintenance
    path('maintenance/', views.maintenance, name='maintenance'),
    path(
        'my-home/asset/<int:asset_id>/add-maintenance/',
        views.add_maintenance,
        name='add_maintenance'
    ),
    path('maintenance/add/', views.add_maintenance_select,
         name='add_maintenance_select'),

    path('my-home/maintenance/<int:maintenance_id>/',
         views.maintenance_detail, name='maintenance_detail'),

    path(
        'my-home/maintenance/<int:maintenance_id>/edit/',
        views.edit_maintenance,
        name='edit_maintenance'
    ),
    path(
        'my-home/maintenance/<int:maintenance_id>/delete/',
        views.delete_maintenance,
        name='delete_maintenance'
    ),

    # Documents
    path('documents/', views.documents, name='documents'),
    path('documents/add/', views.add_document, name='add_document'),
    path(
        'documents/<int:document_id>/edit/',
        views.edit_document,
        name='edit_document'
    ),
    path(
        'documents/<int:document_id>/delete/',
        views.delete_document,
        name='delete_document'
    ),
    path('documents/<int:document_id>/view/',
         views.view_document, name='view_document'),
    
    # Expenses
    path('expenses/', views.expenses, name='expenses'),
    path('expenses/add/', views.add_expense, name='add_expense'),
    path(
        'expenses/<int:expense_id>/edit/',
        views.edit_expense,
        name='edit_expense'
    ),
    path(
        'expenses/<int:expense_id>/delete/',
        views.delete_expense,
        name='delete_expense'
    ),

    # My Home
    path('my-home/', views.my_home, name='my_home'),

    # Rooms
    path('rooms/', views.rooms, name='rooms'),
    path('my-home/add-room/', views.add_room, name='add_room'),
    path(
        'my-home/room/<int:room_id>/',
        views.room_detail,
        name='room_detail'
    ),
    path(
        'my-home/room/<int:room_id>/edit/',
        views.edit_room,
        name='edit_room'
    ),
    path(
        'my-home/room/<int:room_id>/delete/',
        views.delete_room,
        name='delete_room'
    ),

    # Assets
    path('assets/', views.assets, name='assets'),
    path(
        'my-home/room/<int:room_id>/add-asset/',
        views.add_asset,
        name='add_asset'
    ),
    path(
        'my-home/asset/<int:asset_id>/',
        views.asset_detail,
        name='asset_detail'
    ),
    path(
        'my-home/asset/<int:asset_id>/edit/',
        views.edit_asset,
        name='edit_asset'
    ),
    path(
        'my-home/asset/<int:asset_id>/delete/',
        views.delete_asset,
        name='delete_asset'
    ),

    # Logout
    path('logout/', views.logout_view, name='logout'),
]
