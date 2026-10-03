from datetime import timedelta, date

from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.db import transaction
from django.contrib import messages
from django.contrib.auth.models import User
from django.core.files.storage import default_storage
from django.contrib.auth.decorators import login_required

from django.db.models import Q, Count, Sum

from .forms import (
    RegistrationForm,
    LoginForm,
    RoomForm,
    AssetForm,
    WarrantyForm,
    MaintenanceForm,
    DocumentForm,
    ExpenseForm,
    ProfileForm,
    HomeProfileForm,
)

from .models import (
    Home,
    Room,
    Asset,
    Warranty,
    Maintenance,
    Expense,
    Document,
    Notification,
)


# ============================================================
# PUBLIC PAGES
# ============================================================

def home(request):
    return render(request, 'home.html')


@transaction.atomic
def register(request):

    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':

        form = RegistrationForm(request.POST)

        if form.is_valid():

            user = form.save()

            Home.objects.create(
                owner=user,
                name="My Home"
            )

            return redirect('login')

    else:
        form = RegistrationForm()

    return render(
        request,
        'register.html',
        {'form': form}
    )


def login_view(request):

    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':

        form = LoginForm(request.POST)

        if form.is_valid():

            email = form.cleaned_data['email'].lower()
            password = form.cleaned_data['password']

            user = User.objects.filter(
                email__iexact=email
            ).first()

            if user is not None:

                authenticated_user = authenticate(
                    request,
                    username=user.username,
                    password=password
                )

                if authenticated_user is not None:

                    login(request, authenticated_user)

                    remember = request.POST.get('remember')

                    if remember:
                        request.session.set_expiry(1209600)
                    else:
                        request.session.set_expiry(0)

                    return redirect('dashboard')

            messages.error(
                request,
                'Invalid email or password.'
            )

    else:
        form = LoginForm()

    return render(
        request,
        'login.html',
        {'form': form}
    )


def logout_view(request):
    logout(request)
    return redirect('home')


# ============================================================
# DASHBOARD
# ============================================================

def dashboard(request):

    if not request.user.is_authenticated:
        return redirect('login')

    home = request.user.home

    assets = Asset.objects.filter(
        room__home=home
    )

    total_assets = assets.count()

    home_value = sum(
        asset.purchase_price or 0
        for asset in assets
    )

    today = timezone.now().date()

    active_warranties = Warranty.objects.filter(
        asset__room__home=home,
        end_date__gte=today
    ).count()

    upcoming_maintenance = Maintenance.objects.filter(
        asset__room__home=home,
        next_service_date__isnull=False
    ).order_by('next_service_date')[:5]

    monthly_expenses = Expense.objects.filter(
        home=home
    )

    total_expenses = sum(
        expense.amount
        for expense in monthly_expenses
    )

    rooms_count = Room.objects.filter(
        home=home
    ).count()

    context = {
        'home': home,
        'total_assets': total_assets,
        'home_value': home_value,
        'active_warranties': active_warranties,
        'upcoming_maintenance': upcoming_maintenance,
        'total_expenses': total_expenses,
        'rooms_count': rooms_count,
    }

    return render(
        request,
        'dashboard.html',
        context
    )


# ============================================================
# MY HOME
# ============================================================

def my_home(request):

    if not request.user.is_authenticated:
        return redirect('login')

    home = request.user.home

    rooms = Room.objects.filter(
        home=home
    ).order_by('name')

    context = {
        'home': home,
        'rooms': rooms,
    }

    return render(
        request,
        'my_home.html',
        context
    )


# ============================================================
# ROOMS
# ============================================================

def rooms(request):

    if not request.user.is_authenticated:
        return redirect('login')

    home = request.user.home

    rooms_list = Room.objects.filter(
        home=home
    ).prefetch_related(
        'assets'
    ).order_by('name')

    return render(
        request,
        'rooms.html',
        {
            'home': home,
            'rooms': rooms_list,
        }
    )


def add_room(request):

    if not request.user.is_authenticated:
        return redirect('login')

    home = request.user.home

    if request.method == 'POST':

        form = RoomForm(request.POST)

        if form.is_valid():

            room = form.save(commit=False)
            room.home = home
            room.save()

            Notification.objects.create(
                home=home,
                title='New room added',
                message=(
                    f"{room.name} has been added to "
                    f"{home.name}."
                ),
                notification_type='home',
                reference_key=f"home-room-{room.id}"
            )

            return redirect('my_home')

    else:
        form = RoomForm()

    return render(
        request,
        'add_room.html',
        {
            'form': form,
            'home': home,
        }
    )


def room_detail(request, room_id):

    if not request.user.is_authenticated:
        return redirect('login')

    home = request.user.home

    room = Room.objects.filter(
        id=room_id,
        home=home
    ).first()

    if room is None:
        return redirect('my_home')

    assets = Asset.objects.filter(
        room=room
    ).order_by('name')

    context = {
        'home': home,
        'room': room,
        'assets': assets,
    }

    return render(
        request,
        'room_detail.html',
        context
    )


def edit_room(request, room_id):

    if not request.user.is_authenticated:
        return redirect('login')

    home = request.user.home

    room = get_object_or_404(
        Room,
        id=room_id,
        home=home
    )

    if request.method == 'POST':

        form = RoomForm(
            request.POST,
            instance=room
        )

        if form.is_valid():

            form.save()

            return redirect(
                'room_detail',
                room_id=room.id
            )

    else:

        form = RoomForm(
            instance=room
        )

    return render(
        request,
        'edit_room.html',
        {
            'form': form,
            'home': home,
            'room': room,
        }
    )


@transaction.atomic
def delete_room(request, room_id):

    if not request.user.is_authenticated:
        return redirect('login')

    home = request.user.home

    room = get_object_or_404(
        Room,
        id=room_id,
        home=home
    )

    if request.method != 'POST':
        return redirect(
            'room_detail',
            room_id=room.id
        )

    # Delete uploaded document files before
    # the related database records are removed.
    assets = Asset.objects.filter(
        room=room
    )

    for asset in assets:

        documents = Document.objects.filter(
            asset=asset
        )

        for document in documents:

            if document.file:
                document.file.delete(
                    save=False
                )

    room_name = room.name

    room.delete()

    messages.success(
        request,
        f'{room_name} was deleted successfully.'
    )

    return redirect('rooms')


# ============================================================
# ASSETS
# ============================================================

def assets(request):

    if not request.user.is_authenticated:
        return redirect('login')

    home = request.user.home

    assets_list = Asset.objects.filter(
        room__home=home
    ).select_related(
        'room'
    ).order_by(
        'room__name',
        'name'
    )

    return render(
        request,
        'assets.html',
        {
            'home': home,
            'assets': assets_list,
        }
    )


def add_asset(request, room_id):
    if not request.user.is_authenticated:
        return redirect('login')

    home = request.user.home

    current_room = Room.objects.filter(
        id=room_id,
        home=home
    ).first()

    if current_room is None:
        return redirect('my_home')

    # Only show rooms belonging to this home
    if request.method == 'POST':
        form = AssetForm(request.POST)
        form.fields['room'].queryset = Room.objects.filter(
            home=home
        )

        if form.is_valid():
            asset = form.save()

            Notification.objects.create(
                home=home,
                title='New asset added',
                message=(
                    f"{asset.name} has been added to "
                    f"{asset.room.name}."
                ),
                notification_type='home',
                reference_key=f"home-asset-{asset.id}"
            )

            return redirect(
                'room_detail',
                room_id=asset.room.id
            )
    else:
        form = AssetForm()
        form.fields['room'].queryset = Room.objects.filter(
            home=home
        )
        form.fields['room'].initial = current_room

    return render(
        request,
        'add_asset.html',
        {
            'form': form,
            'home': home,
            'room': current_room,
        }
    )


def asset_detail(request, asset_id):

    if not request.user.is_authenticated:
        return redirect('login')

    home = request.user.home

    asset = Asset.objects.filter(
        id=asset_id,
        room__home=home
    ).select_related(
        'room'
    ).first()

    if asset is None:
        return redirect('my_home')

    context = {
        'home': home,
        'asset': asset,
    }

    return render(
        request,
        'asset_detail.html',
        context
    )


def edit_asset(request, asset_id):

    if not request.user.is_authenticated:
        return redirect('login')

    home = request.user.home

    asset = Asset.objects.filter(
        id=asset_id,
        room__home=home
    ).select_related(
        'room'
    ).first()

    if asset is None:
        return redirect('my_home')

    if request.method == 'POST':

        form = AssetForm(
            request.POST,
            instance=asset
        )

        if form.is_valid():

            form.save()

            return redirect(
                'asset_detail',
                asset_id=asset.id
            )

    else:

        form = AssetForm(
            instance=asset
        )

    return render(
        request,
        'edit_asset.html',
        {
            'form': form,
            'home': home,
            'asset': asset,
        }
    )


@transaction.atomic
def delete_asset(request, asset_id):

    if not request.user.is_authenticated:
        return redirect('login')

    home = request.user.home

    asset = get_object_or_404(
        Asset,
        id=asset_id,
        room__home=home
    )

    if request.method != 'POST':
        return redirect(
            'asset_detail',
            asset_id=asset.id
        )

    # Documents use CASCADE at database level,
    # so remove their physical files first.
    documents = Document.objects.filter(
        asset=asset
    )

    for document in documents:

        if document.file:
            document.file.delete(
                save=False
            )

    asset_name = asset.name

    asset.delete()

    messages.success(
        request,
        f'{asset_name} was deleted successfully.'
    )

    return redirect('assets')


# ============================================================
# WARRANTIES
# ============================================================

def get_warranty_status(end_date):

    today = timezone.now().date()

    if end_date < today:
        return 'expired'

    if end_date <= today + timedelta(days=30):
        return 'expiring'

    return 'active'


@login_required
def warranties(request):
    home = get_object_or_404(Home, owner=request.user)

    warranties = (
        Warranty.objects
        .filter(asset__room__home=home)
        .select_related('asset', 'asset__room')
        .order_by('end_date')
    )

    today = date.today()
    expiring_limit = today + timedelta(days=30)

    total_warranties = warranties.count()

    active_warranties = warranties.filter(
        end_date__gte=today
    ).count()

    expiring_warranties = warranties.filter(
        end_date__gte=today,
        end_date__lte=expiring_limit
    ).count()

    assets_without_warranty = (
        Asset.objects
        .filter(room__home=home)
        .exclude(warranty__isnull=False)
        .select_related('room')
        .order_by('name')
    )

    return render(
        request,
        'warranties.html',
        {
            'warranties': warranties,
            'total_warranties': total_warranties,
            'active_warranties': active_warranties,
            'expiring_warranties': expiring_warranties,
            'assets_without_warranty': assets_without_warranty,
            'today': today,
        }
    )


@login_required
def add_warranty_for_asset(request, asset_id):

    home = get_object_or_404(
        Home,
        owner=request.user
    )

    asset = get_object_or_404(
        Asset,
        id=asset_id,
        room__home=home
    )

    if hasattr(asset, 'warranty'):
        messages.info(
            request,
            'This asset already has a warranty.'
        )
        return redirect(
            'edit_warranty',
            warranty_id=asset.warranty.id
        )

    if request.method == 'POST':

        form = WarrantyForm(
            request.POST
        )

        if form.is_valid():

            warranty = form.save(
                commit=False
            )

            warranty.asset = asset

            warranty.status = get_warranty_status(
                warranty.end_date
            )

            warranty.save()

            messages.success(
                request,
                'Warranty added successfully.'
            )

            return redirect('warranties')

    else:

        form = WarrantyForm(
            initial={
                'asset': asset
            }
        )

        form.fields['asset'].queryset = Asset.objects.filter(
            id=asset.id
        )

    return render(
        request,
        'add_warranty.html',
        {
            'form': form,
            'asset': asset,
        }
    )


@login_required
def add_warranty(request):
    home = get_object_or_404(Home, owner=request.user)

    assets = Asset.objects.filter(
        room__home=home
    ).order_by('name')

    if request.method == 'POST':

        form = WarrantyForm(request.POST)

        # Only show assets belonging to this user's home
        if 'asset' in form.fields:
            form.fields['asset'].queryset = assets

        if form.is_valid():

            asset = form.cleaned_data['asset']

            # Safety check
            if asset.room.home_id != home.id:
                form.add_error(
                    'asset',
                    'You can only add warranties to your own assets.'
                )

            elif Warranty.objects.filter(asset=asset).exists():
                form.add_error(
                    'asset',
                    'This asset already has a warranty.'
                )

            else:
                warranty = form.save(commit=False)

                warranty.status = get_warranty_status(
                    warranty.end_date
                )

                warranty.save()

                return redirect('warranties')

    else:

        form = WarrantyForm()

        # Only show assets from this user's home
        if 'asset' in form.fields:
            form.fields['asset'].queryset = assets

    return render(
        request,
        'add_warranty.html',
        {
            'form': form,
            'assets': assets,
        }
    )


def edit_warranty(request, warranty_id):

    if not request.user.is_authenticated:
        return redirect('login')

    home = request.user.home

    warranty = get_object_or_404(
        Warranty.objects.select_related(
            'asset',
            'asset__room'
        ),
        id=warranty_id,
        asset__room__home=home
    )

    if request.method == 'POST':

        form = WarrantyForm(
            request.POST,
            instance=warranty
        )

        if form.is_valid():

            warranty = form.save(commit=False)

            warranty.status = get_warranty_status(
                warranty.end_date
            )

            warranty.save()

            return redirect(
                'asset_detail',
                asset_id=warranty.asset.id
            )

    else:

        form = WarrantyForm(
            instance=warranty
        )

    return render(
        request,
        'edit_warranty.html',
        {
            'form': form,
            'home': home,
            'asset': warranty.asset,
            'warranty': warranty,
        }
    )


def delete_warranty(request, warranty_id):

    if not request.user.is_authenticated:
        return redirect('login')

    home = request.user.home

    warranty = get_object_or_404(
        Warranty.objects.select_related(
            'asset'
        ),
        id=warranty_id,
        asset__room__home=home
    )

    asset_id = warranty.asset.id

    if request.method != 'POST':
        return redirect(
            'asset_detail',
            asset_id=asset_id
        )

    warranty.delete()

    messages.success(
        request,
        'Warranty deleted successfully.'
    )

    return redirect(
        'asset_detail',
        asset_id=asset_id
    )


# ============================================================
# MAINTENANCE
# ============================================================


@login_required
def maintenance(request):
    home = get_object_or_404(Home, owner=request.user)

    maintenance_list = (
        Maintenance.objects
        .filter(asset__room__home=home)
        .select_related('asset', 'asset__room')
        .order_by('-service_date')
    )

    today = date.today()

    total_maintenance = maintenance_list.count()

    upcoming_maintenance = maintenance_list.filter(
        next_service_date__gte=today
    ).count()

    overdue_maintenance = maintenance_list.filter(
        next_service_date__lt=today
    ).count()

    return render(
        request,
        'maintenance.html',
        {
            'maintenance_list': maintenance_list,
            'total_maintenance': total_maintenance,
            'upcoming_maintenance': upcoming_maintenance,
            'overdue_maintenance': overdue_maintenance,
            'today': today,
        }
    )


@login_required
def add_maintenance(request, asset_id):

    home = get_object_or_404(
        Home,
        owner=request.user
    )

    asset = get_object_or_404(
        Asset,
        id=asset_id,
        room__home=home
    )

    user_assets = (
        Asset.objects
        .filter(room__home=home)
        .select_related('room')
        .order_by('name')
    )

    if request.method == 'POST':

        form = MaintenanceForm(request.POST)

        form.fields['asset'].queryset = user_assets

        if form.is_valid():

            maintenance_record = form.save(commit=False)

            if maintenance_record.asset.room.home_id != home.id:

                messages.error(
                    request,
                    'You cannot add maintenance to this asset.'
                )

                return redirect('maintenance')

            maintenance_record.save()

            messages.success(
                request,
                'Maintenance added successfully.'
            )

            return redirect('maintenance')

    else:

        form = MaintenanceForm(
            initial={
                'asset': asset
            }
        )

        form.fields['asset'].queryset = user_assets

    return render(
        request,
        'add_maintenance.html',
        {
            'form': form,
            'selected_asset': asset,
        }
    )


@login_required
def add_maintenance_select(request):

    home = get_object_or_404(
        Home,
        owner=request.user
    )

    user_assets = (
        Asset.objects
        .filter(room__home=home)
        .select_related('room')
        .order_by('name')
    )

    if not user_assets.exists():

        messages.info(
            request,
            'Add an asset before creating a maintenance record.'
        )

        return redirect('assets')

    if request.method == 'POST':

        form = MaintenanceForm(request.POST)

        form.fields['asset'].queryset = user_assets

        if form.is_valid():

            maintenance_record = form.save(commit=False)

            if maintenance_record.asset.room.home_id != home.id:

                messages.error(
                    request,
                    'You cannot add maintenance to this asset.'
                )

                return redirect('maintenance')

            maintenance_record.save()

            messages.success(
                request,
                'Maintenance added successfully.'
            )

            return redirect('maintenance')

    else:

        form = MaintenanceForm()

        form.fields['asset'].queryset = user_assets

    return render(
        request,
        'add_maintenance.html',
        {
            'form': form,
            'selected_asset': None,
        }
    )


@login_required
def edit_maintenance(request, maintenance_id):
    home = get_object_or_404(
        Home,
        owner=request.user
    )

    maintenance_record = get_object_or_404(
        Maintenance.objects.select_related(
            'asset',
            'asset__room'
        ),
        id=maintenance_id,
        asset__room__home=home
    )

    if request.method == 'POST':
        form = MaintenanceForm(
            request.POST,
            instance=maintenance_record
        )

        # Asset is not editable because the template
        # does not contain an asset field.
        form.fields.pop('asset', None)

        if form.is_valid():
            updated_record = form.save(commit=False)

            # Preserve the existing asset association.
            updated_record.asset = maintenance_record.asset

            updated_record.save()

            messages.success(
                request,
                'Maintenance updated successfully.'
            )

            return redirect('maintenance')

        else:
            print(
                "MAINTENANCE FORM ERRORS:",
                form.errors.as_json()
            )

            messages.error(
                request,
                'Please correct the errors in the form '
                'and try again.'
            )

    else:
        form = MaintenanceForm(
            instance=maintenance_record
        )

        # The asset field is not shown on the edit page.
        form.fields.pop('asset', None)

    return render(
        request,
        'edit_maintenance.html',
        {
            'form': form,
            'maintenance': maintenance_record,
        }
    )


@login_required
def maintenance_detail(request, maintenance_id):

    home = get_object_or_404(
        Home,
        owner=request.user
    )

    maintenance_record = get_object_or_404(
        Maintenance.objects.select_related(
            'asset',
            'asset__room'
        ),
        id=maintenance_id,
        asset__room__home=home
    )

    return render(
        request,
        'maintenance_detail.html',
        {
            'maintenance': maintenance_record,
        }
    )


@login_required
def delete_maintenance(request, maintenance_id):

    if request.method != 'POST':
        return redirect('maintenance')

    home = get_object_or_404(
        Home,
        owner=request.user
    )

    maintenance_record = get_object_or_404(
        Maintenance,
        id=maintenance_id,
        asset__room__home=home
    )

    maintenance_record.delete()

    messages.success(
        request,
        'Maintenance deleted successfully.'
    )

    return redirect('maintenance')


# ============================================================
# DOCUMENTS
# ============================================================

def documents(request):

    if not request.user.is_authenticated:
        return redirect('login')

    home = request.user.home

    document_list = (
        Document.objects
        .filter(home=home)
        .select_related(
            'asset',
            'asset__room'
        )
        .order_by('-uploaded_at')
    )

    total_documents = document_list.count()

    linked_document_count = document_list.filter(
        asset__isnull=False
    ).count()

    home_document_count = document_list.filter(
        asset__isnull=True
    ).count()

    context = {
        'home': home,
        'documents': document_list,
        'total_documents': total_documents,
        'linked_document_count': linked_document_count,
        'home_document_count': home_document_count,
    }

    return render(
        request,
        'documents.html',
        context
    )


def add_document(request):

    if not request.user.is_authenticated:
        return redirect('login')

    home = request.user.home

    if request.method == 'POST':

        form = DocumentForm(
            request.POST,
            request.FILES,
            home=home
        )

        if form.is_valid():

            document = form.save(commit=False)

            document.home = home
            document.save()

            Notification.objects.create(
                home=home,
                title='New document added',
                message=(
                    f"{document.name} has been added "
                    f"to your home records."
                ),
                notification_type='home',
                reference_key=f"home-document-{document.id}"
            )

            return redirect('documents')

    else:

        form = DocumentForm(
            home=home
        )

    return render(
        request,
        'add_document.html',
        {
            'form': form,
            'home': home,
        }
    )


def edit_document(request, document_id):

    if not request.user.is_authenticated:
        return redirect('login')

    home = request.user.home

    document = get_object_or_404(
        Document.objects.select_related(
            'asset',
            'asset__room'
        ),
        id=document_id,
        home=home
    )

    old_file_name = document.file.name if document.file else None

    if request.method == 'POST':

        form = DocumentForm(
            request.POST,
            request.FILES,
            instance=document,
            home=home
        )

        # Existing file can remain when editing.
        form.fields['file'].required = False

        if form.is_valid():

            document = form.save(commit=False)

            new_file_uploaded = bool(
                request.FILES.get('file')
            )

            document.save()

            if (
                new_file_uploaded
                and old_file_name
                and old_file_name != document.file.name
            ):
                if default_storage.exists(old_file_name):
                    default_storage.delete(old_file_name)

            return redirect('documents')

    else:

        form = DocumentForm(
            instance=document,
            home=home
        )

        form.fields['file'].required = False

    return render(
        request,
        'edit_document.html',
        {
            'form': form,
            'home': home,
            'document': document,
        }
    )


def delete_document(request, document_id):

    if not request.user.is_authenticated:
        return redirect('login')

    home = request.user.home

    document = get_object_or_404(
        Document,
        id=document_id,
        home=home
    )

    if request.method != 'POST':
        return redirect('documents')

    if document.file:
        document.file.delete(
            save=False
        )

    document.delete()

    messages.success(
        request,
        'Document deleted successfully.'
    )

    return redirect('documents')


# ============================================================
# EXPENSES
# ============================================================

def expenses(request):

    if not request.user.is_authenticated:
        return redirect('login')

    home = request.user.home

    expense_list = (
        Expense.objects
        .filter(home=home)
        .select_related(
            'asset',
            'maintenance'
        )
        .order_by(
            '-expense_date',
            '-created_at'
        )
    )

    total_expenses = expense_list.count()

    total_amount = sum(
        expense.amount
        for expense in expense_list
    )

    linked_expenses = expense_list.filter(
        asset__isnull=False
    ).count()

    context = {
        'home': home,
        'expenses': expense_list,
        'total_expenses': total_expenses,
        'total_amount': total_amount,
        'linked_expenses': linked_expenses,
    }

    return render(
        request,
        'expenses.html',
        context
    )


def add_expense(request):

    if not request.user.is_authenticated:
        return redirect('login')

    home = request.user.home

    if request.method == 'POST':

        form = ExpenseForm(
            request.POST,
            home=home
        )

        if form.is_valid():

            expense = form.save(commit=False)

            expense.home = home
            expense.save()

            create_expense_notification(
                home,
                expense
            )

            return redirect('expenses')

    else:

        form = ExpenseForm(
            home=home
        )

    return render(
        request,
        'add_expense.html',
        {
            'form': form,
            'home': home,
        }
    )


def edit_expense(request, expense_id):

    if not request.user.is_authenticated:
        return redirect('login')

    home = request.user.home

    expense = get_object_or_404(
        Expense.objects.select_related(
            'asset',
            'maintenance'
        ),
        id=expense_id,
        home=home
    )

    if request.method == 'POST':

        form = ExpenseForm(
            request.POST,
            instance=expense,
            home=home
        )

        if form.is_valid():

            form.save()

            return redirect('expenses')

    else:

        form = ExpenseForm(
            instance=expense,
            home=home
        )

    return render(
        request,
        'edit_expense.html',
        {
            'form': form,
            'home': home,
            'expense': expense,
        }
    )


def delete_expense(request, expense_id):

    if not request.user.is_authenticated:
        return redirect('login')

    home = request.user.home

    expense = get_object_or_404(
        Expense,
        id=expense_id,
        home=home
    )

    if request.method != 'POST':
        return redirect('expenses')

    expense.delete()

    messages.success(
        request,
        'Expense deleted successfully.'
    )

    return redirect('expenses')


def create_expense_notification(home, expense):

    if expense.expense_type == 'purchase':

        title = 'New purchase recorded'

        message = (
            f"{expense.title} was added as a "
            f"purchase expense of ₹{expense.amount}."
        )

    elif expense.expense_type == 'maintenance':

        title = 'Maintenance expense recorded'

        message = (
            f"{expense.title} has a maintenance "
            f"expense of ₹{expense.amount}."
        )

    elif expense.expense_type == 'repair':

        title = 'Repair expense recorded'

        message = (
            f"{expense.title} has a repair "
            f"expense of ₹{expense.amount}."
        )

    elif expense.expense_type == 'service':

        title = 'Service expense recorded'

        message = (
            f"{expense.title} has a service "
            f"expense of ₹{expense.amount}."
        )

    else:

        title = 'New home expense'

        message = (
            f"{expense.title} was recorded as a "
            f"home expense of ₹{expense.amount}."
        )

    Notification.objects.create(
        home=home,
        title=title,
        message=message,
        notification_type='expense',
        reference_key=f"expense-{expense.id}"
    )


# ============================================================
# ANALYTICS
# ============================================================

def analytics(request):

    if not request.user.is_authenticated:
        return redirect('login')

    home = request.user.home
    today = timezone.now().date()

    assets = Asset.objects.filter(
        room__home=home
    )

    total_assets = assets.count()

    expenses = Expense.objects.filter(
        home=home
    )

    total_spending = sum(
        expense.amount
        for expense in expenses
    )

    active_warranties = Warranty.objects.filter(
        asset__room__home=home,
        end_date__gte=today
    ).count()

    upcoming_maintenance = Maintenance.objects.filter(
        asset__room__home=home,
        next_service_date__gte=today
    ).count()

    spending_values = {
        'Purchase': sum(
            expense.amount
            for expense in expenses
            if expense.expense_type == 'purchase'
        ),

        'Maintenance': sum(
            expense.amount
            for expense in expenses
            if expense.expense_type == 'maintenance'
        ),

        'Repair': sum(
            expense.amount
            for expense in expenses
            if expense.expense_type == 'repair'
        ),

        'Service': sum(
            expense.amount
            for expense in expenses
            if expense.expense_type == 'service'
        ),

        'Other': sum(
            expense.amount
            for expense in expenses
            if expense.expense_type == 'other'
        ),
    }

    spending_by_type = {}

    for name, amount in spending_values.items():

        if total_spending:

            percentage = float(
                (amount / total_spending) * 100
            )

        else:
            percentage = 0

        spending_by_type[name] = {
            'amount': amount,
            'percentage': percentage,
        }

    rooms = Room.objects.filter(
        home=home
    ).prefetch_related(
        'assets'
    ).order_by('name')

    room_distribution = []

    for room in rooms:

        room_count = room.assets.count()

        room_distribution.append({
            'name': room.name,
            'count': room_count,
        })

    max_room_assets = max(
        [
            room['count']
            for room in room_distribution
        ],
        default=0
    )

    for room in room_distribution:

        if max_room_assets:

            room['percentage'] = (
                room['count'] / max_room_assets
            ) * 100

        else:

            room['percentage'] = 0

    maintenance_records = Maintenance.objects.filter(
        asset__room__home=home
    )

    upcoming_maintenance_count = maintenance_records.filter(
        next_service_date__gte=today
    ).count()

    overdue_maintenance_count = maintenance_records.filter(
        next_service_date__lt=today
    ).count()

    warranties_list = Warranty.objects.filter(
        asset__room__home=home
    )

    active_warranty_count = warranties_list.filter(
        end_date__gte=today
    ).count()

    expiring_warranty_count = warranties_list.filter(
        end_date__gte=today,
        end_date__lte=today + timedelta(days=30)
    ).count()

    expired_warranty_count = warranties_list.filter(
        end_date__lt=today
    ).count()

    recent_expenses = Expense.objects.filter(
        home=home
    ).select_related(
        'asset',
        'maintenance'
    ).order_by(
        '-expense_date',
        '-created_at'
    )[:5]

    recent_maintenance = Maintenance.objects.filter(
        asset__room__home=home
    ).select_related(
        'asset',
        'asset__room'
    ).order_by(
        '-service_date',
        '-created_at'
    )[:5]

    context = {
        'home': home,

        'total_assets': total_assets,
        'total_spending': total_spending,
        'active_warranties': active_warranties,
        'upcoming_maintenance': upcoming_maintenance,

        'spending_by_type': spending_by_type,

        'room_distribution': room_distribution,

        'upcoming_maintenance_count':
            upcoming_maintenance_count,

        'overdue_maintenance_count':
            overdue_maintenance_count,

        'active_warranty_count':
            active_warranty_count,

        'expiring_warranty_count':
            expiring_warranty_count,

        'expired_warranty_count':
            expired_warranty_count,

        'recent_expenses': recent_expenses,
        'recent_maintenance': recent_maintenance,
    }

    return render(
        request,
        'analytics.html',
        context
    )


# ============================================================
# PROFILE
# ============================================================

@login_required
def profile(request):
    user = request.user
    home = get_object_or_404(Home, owner=user)

    if request.method == 'POST':
        if 'save_profile' in request.POST:
            profile_form = ProfileForm(
                request.POST,
                instance=user
            )
            home_form = HomeProfileForm(instance=home)

            if profile_form.is_valid():
                profile_form.save()
                messages.success(
                    request,
                    'Profile information saved successfully.'
                )
                return redirect('profile')

        elif 'save_home' in request.POST:
            home_form = HomeProfileForm(
                request.POST,
                instance=home
            )
            profile_form = ProfileForm(instance=user)

            if home_form.is_valid():
                home_form.save()
                messages.success(
                    request,
                    'Home details saved successfully.'
                )
                return redirect('profile')

        else:
            profile_form = ProfileForm(instance=user)
            home_form = HomeProfileForm(instance=home)

    else:
        profile_form = ProfileForm(instance=user)
        home_form = HomeProfileForm(instance=home)

    context = {
        'home': home,
        'user': user,
        'profile_form': profile_form,
        'home_form': home_form,
    }

    return render(request, 'profile.html', context)


# ============================================================
# SETTINGS
# ============================================================

def settings(request):

    if not request.user.is_authenticated:
        return redirect('login')

    home = request.user.home

    if request.method == 'POST':

        home.name = (
            request.POST.get(
                'home_name',
                ''
            ).strip()
            or 'My Home'
        )

        home.address = (
            request.POST.get(
                'address',
                ''
            ).strip()
        )

        home.warranty_reminders_enabled = (
            request.POST.get(
                'warranty_reminders'
            ) == 'on'
        )

        home.maintenance_reminders_enabled = (
            request.POST.get(
                'maintenance_reminders'
            ) == 'on'
        )

        home.save()

        return redirect('settings')

    create_automatic_notifications(home)

    notifications_list = Notification.objects.filter(
        home=home
    )

    unread_count = notifications_list.filter(
        is_read=False
    ).count()

    return render(
        request,
        'settings.html',
        {
            'home': home,
            'unread_count': unread_count,
        }
    )


# ============================================================
# NOTIFICATIONS
# ============================================================

def mark_notification_read(
    request,
    notification_id
):

    if not request.user.is_authenticated:
        return redirect('login')

    home = request.user.home

    notification = get_object_or_404(
        Notification,
        id=notification_id,
        home=home
    )

    notification.is_read = True

    notification.save(
        update_fields=['is_read']
    )

    return redirect('notifications')


def create_automatic_notifications(home):

    today = timezone.now().date()

    # --------------------------------------------------------
    # WARRANTY NOTIFICATIONS
    # --------------------------------------------------------

    if home.warranty_reminders_enabled:

        warranties = Warranty.objects.filter(
            asset__room__home=home
        ).select_related(
            'asset',
            'asset__room'
        )

        for warranty in warranties:

            days_remaining = (
                warranty.end_date - today
            ).days

            if days_remaining < 0:

                reference_key = (
                    f"warranty-expired-{warranty.id}-"
                    f"{warranty.end_date}"
                )

                Notification.objects.get_or_create(
                    reference_key=reference_key,
                    defaults={
                        'home': home,
                        'title': 'Warranty expired',
                        'message': (
                            f"The warranty for "
                            f"{warranty.asset.name} expired on "
                            f"{warranty.end_date.strftime('%d %b %Y')}."
                        ),
                        'notification_type': 'warranty',
                    }
                )

            elif days_remaining <= 30:

                reference_key = (
                    f"warranty-expiring-{warranty.id}-"
                    f"{warranty.end_date}"
                )

                Notification.objects.get_or_create(
                    reference_key=reference_key,
                    defaults={
                        'home': home,
                        'title': 'Warranty expiring soon',
                        'message': (
                            f"The warranty for "
                            f"{warranty.asset.name} expires in "
                            f"{days_remaining} day"
                            f"{'' if days_remaining == 1 else 's'}."
                        ),
                        'notification_type': 'warranty',
                    }
                )

    # --------------------------------------------------------
    # MAINTENANCE NOTIFICATIONS
    # --------------------------------------------------------

    if home.maintenance_reminders_enabled:

        maintenance_records = Maintenance.objects.filter(
            asset__room__home=home,
            next_service_date__isnull=False
        ).select_related(
            'asset',
            'asset__room'
        )

        for maintenance_record in maintenance_records:

            service_date = (
                maintenance_record.next_service_date
            )

            days_remaining = (
                service_date - today
            ).days

            if days_remaining < 0:

                reference_key = (
                    f"maintenance-overdue-"
                    f"{maintenance_record.id}-"
                    f"{service_date}"
                )

                Notification.objects.get_or_create(
                    reference_key=reference_key,
                    defaults={
                        'home': home,
                        'title': 'Maintenance overdue',
                        'message': (
                            f"Maintenance for "
                            f"{maintenance_record.asset.name} "
                            f"was due on "
                            f"{service_date.strftime('%d %b %Y')}."
                        ),
                        'notification_type': 'maintenance',
                    }
                )

            elif days_remaining <= 7:

                reference_key = (
                    f"maintenance-upcoming-"
                    f"{maintenance_record.id}-"
                    f"{service_date}"
                )

                Notification.objects.get_or_create(
                    reference_key=reference_key,
                    defaults={
                        'home': home,
                        'title': 'Maintenance due soon',
                        'message': (
                            f"Maintenance for "
                            f"{maintenance_record.asset.name} "
                            f"is due in "
                            f"{days_remaining} day"
                            f"{'' if days_remaining == 1 else 's'}."
                        ),
                        'notification_type': 'maintenance',
                    }
                )


def notifications(request):

    if not request.user.is_authenticated:
        return redirect('login')

    home = request.user.home

    create_automatic_notifications(home)

    notifications_list = Notification.objects.filter(
        home=home
    ).order_by(
        '-created_at'
    )

    unread_count = notifications_list.filter(
        is_read=False
    ).count()

    return render(
        request,
        'notifications.html',
        {
            'home': home,
            'notifications': notifications_list,
            'unread_count': unread_count,
        }
    )


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


# ============================================================
# GLOBAL SEARCH
# ============================================================
@login_required
def global_search(request):
    query = request.GET.get('q', '').strip()
    home = Home.objects.filter(owner=request.user).first()

    results = []

    if query and home:
        assets = Asset.objects.filter(
            room__home=home
        ).filter(
            Q(name__icontains=query)
            | Q(category__icontains=query)
            | Q(brand__icontains=query)
            | Q(model_number__icontains=query)
            | Q(serial_number__icontains=query)
            | Q(notes__icontains=query)
        ).distinct()

        for item in assets:
            results.append({
                'type': 'Asset',
                'title': item.name,
                'description': f'{item.get_category_display()} • {item.room.name}',
                'url': 'assets',
            })

        rooms = Room.objects.filter(home=home).filter(
            Q(name__icontains=query)
            | Q(room_type__icontains=query)
            | Q(description__icontains=query)
        )

        for item in rooms:
            results.append({
                'type': 'Room',
                'title': item.name,
                'description': item.get_room_type_display(),
                'url': 'rooms',
            })

        warranties = Warranty.objects.filter(
            asset__room__home=home
        ).filter(
            Q(provider__icontains=query)
            | Q(warranty_number__icontains=query)
            | Q(coverage__icontains=query)
            | Q(status__icontains=query)
            | Q(asset__name__icontains=query)
        )

        for item in warranties:
            results.append({
                'type': 'Warranty',
                'title': f'{item.asset.name} Warranty',
                'description': f'{item.provider} • {item.get_status_display()}',
                'url': 'warranties',
            })

        maintenance_records = Maintenance.objects.filter(
            asset__room__home=home
        ).filter(
            Q(maintenance_type__icontains=query)
            | Q(service_provider__icontains=query)
            | Q(description__icontains=query)
            | Q(asset__name__icontains=query)
        )

        for item in maintenance_records:
            results.append({
                'type': 'Maintenance',
                'title': f'{item.asset.name} - {item.get_maintenance_type_display()}',
                'description': item.description or item.service_provider,
                'url': 'maintenance',
            })

        documents = Document.objects.filter(home=home).filter(
            Q(name__icontains=query)
            | Q(document_type__icontains=query)
            | Q(description__icontains=query)
            | Q(asset__name__icontains=query)
        )

        for item in documents:
            results.append({
                'type': 'Document',
                'title': item.name,
                'description': item.description or item.get_document_type_display(),
                'url': 'documents',
            })

        expenses = Expense.objects.filter(home=home).filter(
            Q(title__icontains=query)
            | Q(expense_type__icontains=query)
            | Q(description__icontains=query)
        )

        for item in expenses:
            results.append({
                'type': 'Expense',
                'title': item.title,
                'description': f'₹{item.amount} • {item.get_expense_type_display()}',
                'url': 'expenses',
            })

    return render(request, 'global_search.html', {
        'query': query,
        'results': results,
        'home': home,
    })