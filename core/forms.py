from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

from .models import Room, Asset, Warranty, Maintenance, Expense, Document, Home


class RegistrationForm(UserCreationForm):

    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(
            attrs={
                'placeholder': 'Username'
            }
        )
    )

    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(
            attrs={
                'placeholder': 'Email address'
            }
        )
    )

    password1 = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                'placeholder': 'Password'
            }
        )
    )

    password2 = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                'placeholder': 'Confirm password'
            }
        )
    )

    class Meta:
        model = User
        fields = (
            'username',
            'email',
            'password1',
            'password2',
        )

    def clean_email(self):
        email = self.cleaned_data['email'].lower()

        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                'An account with this email already exists.'
            )

        return email

    def save(self, commit=True):
        user = super().save(commit=False)

        user.email = self.cleaned_data['email'].lower()

        if commit:
            user.save()

        return user


class LoginForm(forms.Form):

    email = forms.EmailField(
        widget=forms.EmailInput(
            attrs={
                'placeholder': 'Email address'
            }
        )
    )

    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                'placeholder': 'Password'
            }
        )
    )


class RoomForm(forms.ModelForm):

    class Meta:
        model = Room
        fields = (
            'name',
            'room_type',
            'description',
        )

        widgets = {
            'name': forms.TextInput(
                attrs={
                    'placeholder': 'e.g. Living Room'
                }
            ),

            'room_type': forms.Select(),

            'description': forms.Textarea(
                attrs={
                    'placeholder': 'Add a short description of this room...',
                    'rows': 3
                }
            ),
        }


class AssetForm(forms.ModelForm):

    class Meta:
        model = Asset

        fields = (
            'room',
            'name',
            'category',
            'brand',
            'model_number',
            'serial_number',
            'purchase_date',
            'purchase_price',
            'condition',
            'notes',
        )

        widgets = {
            
            'room': forms.Select(),

            'name': forms.TextInput(
                attrs={
                    'placeholder': 'e.g. Samsung Refrigerator'
                }
            ),

            'category': forms.Select(),

            'brand': forms.TextInput(
                attrs={
                    'placeholder': 'e.g. Samsung'
                }
            ),

            'model_number': forms.TextInput(
                attrs={
                    'placeholder': 'Model number'
                }
            ),

            'serial_number': forms.TextInput(
                attrs={
                    'placeholder': 'Serial number'
                }
            ),

            'purchase_date': forms.DateInput(
                attrs={
                    'type': 'date'
                }
            ),

            'purchase_price': forms.NumberInput(
                attrs={
                    'placeholder': 'e.g. 45000',
                    'step': '0.01'
                }
            ),

            'condition': forms.Select(),

            'notes': forms.Textarea(
                attrs={
                    'placeholder': 'Add any notes about this asset...',
                    'rows': 3
                }
            ),
        }

class WarrantyForm(forms.ModelForm):

    class Meta:
        model = Warranty

        fields = (
            'asset',
            'provider',
            'warranty_number',
            'start_date',
            'end_date',
            'coverage',
        )

        widgets = {
            'asset': forms.Select(),

            'provider': forms.TextInput(
                attrs={
                    'placeholder': 'e.g. Samsung'
                }
            ),

            'warranty_number': forms.TextInput(
                attrs={
                    'placeholder': 'Warranty number'
                }
            ),

            'start_date': forms.DateInput(
                attrs={
                    'type': 'date'
                }
            ),

            'end_date': forms.DateInput(
                attrs={
                    'type': 'date'
                }
            ),

            'coverage': forms.Textarea(
                attrs={
                    'placeholder': 'What does this warranty cover?',
                    'rows': 4
                }
            ),
        }

    def clean(self):
        cleaned_data = super().clean()

        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')

        if start_date and end_date and end_date < start_date:
            self.add_error(
                'end_date',
                'End date cannot be before the start date.'
            )

        return cleaned_data

class MaintenanceForm(forms.ModelForm):

    asset = forms.ModelChoiceField(
        queryset=Asset.objects.none(),
        empty_label="Select an asset"
    )

    class Meta:
        model = Maintenance
        fields = [
            'asset',
            'maintenance_type',
            'service_date',
            'cost',
            'service_provider',
            'description',
            'next_service_date',
        ]

        widgets = {
            'service_date': forms.DateInput(
                attrs={'type': 'date'}
            ),
            'next_service_date': forms.DateInput(
                attrs={'type': 'date'}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['asset'].queryset = Asset.objects.all()

    def clean(self):
        cleaned_data = super().clean()

        service_date = cleaned_data.get('service_date')
        next_service_date = cleaned_data.get('next_service_date')

        if (
            service_date
            and next_service_date
            and next_service_date < service_date
        ):
            self.add_error(
                'next_service_date',
                'Next service date cannot be before the service date.'
            )

        return cleaned_data


class DocumentForm(forms.ModelForm):

    asset = forms.ModelChoiceField(
        queryset=Asset.objects.none(),
        required=False,
        empty_label='Home document — not linked to an asset',
        widget=forms.Select()
    )

    document_type = forms.ChoiceField(
        choices=Document.DOCUMENT_TYPES,
        widget=forms.Select()
    )

    class Meta:
        model = Document
        fields = (
            'name',
            'document_type',
            'asset',
            'file',
            'description',
        )

        widgets = {
            'name': forms.TextInput(
                attrs={
                    'placeholder': 'e.g. Samsung Refrigerator Invoice'
                }
            ),

            'file': forms.ClearableFileInput(),

            'description': forms.Textarea(
                attrs={
                    'placeholder': 'Add a short description of this document...',
                    'rows': 4
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        home = kwargs.pop('home', None)

        super().__init__(*args, **kwargs)

        if home is not None:
            self.fields['asset'].queryset = (
                Asset.objects
                .filter(room__home=home)
                .select_related('room')
                .order_by(
                    'room__name',
                    'name'
                )
            )

            self.fields['asset'].label_from_instance = (
                lambda asset:
                    f"{asset.room.name} — {asset.name}"
            )

    def clean_file(self):
        uploaded_file = self.cleaned_data.get('file')
        
        if not uploaded_file:
            return uploaded_file

        # Limit uploads to 10 MB.
        if uploaded_file.size > 10 * 1024 * 1024:
            raise forms.ValidationError(
                "File size must not exceed 10 MB."
            )

        # Allow only common document formats.
        allowed_extensions = {
            '.pdf', '.jpg', '.jpeg', '.png',
            '.doc', '.docx', '.xls', '.xlsx'
        }

        import os
        extension = os.path.splitext(uploaded_file.name)[1].lower()

        if extension not in allowed_extensions:
            raise forms.ValidationError(
                "Upload a PDF, image, Word document, or Excel file."
            )

        return uploaded_file

class ExpenseForm(forms.ModelForm):

    asset = forms.ModelChoiceField(
        queryset=Asset.objects.none(),
        required=False,
        empty_label='Not linked to an asset',
        widget=forms.Select()
    )

    maintenance = forms.ModelChoiceField(
        queryset=Maintenance.objects.none(),
        required=False,
        empty_label='Not linked to maintenance',
        widget=forms.Select()
    )

    class Meta:
        model = Expense

        fields = (
            'title',
            'expense_type',
            'amount',
            'expense_date',
            'asset',
            'maintenance',
            'description',
        )

        widgets = {

            'title': forms.TextInput(
                attrs={
                    'placeholder': 'e.g. AC Service'
                }
            ),

            'expense_type': forms.Select(),

            'amount': forms.NumberInput(
                attrs={
                    'placeholder': 'e.g. 2500',
                    'step': '0.01'
                }
            ),

            'expense_date': forms.DateInput(
                attrs={
                    'type': 'date'
                }
            ),

            'description': forms.Textarea(
                attrs={
                    'placeholder': 'Add a short description of this expense...',
                    'rows': 4
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        home = kwargs.pop('home', None)

        super().__init__(*args, **kwargs)

        if home is not None:

            self.fields['asset'].queryset = (
                Asset.objects
                .filter(room__home=home)
                .select_related('room')
                .order_by(
                    'room__name',
                    'name'
                )
            )

            self.fields['asset'].label_from_instance = (
                lambda asset:
                    f"{asset.room.name} — {asset.name}"
            )

            self.fields['maintenance'].queryset = (
                Maintenance.objects
                .filter(asset__room__home=home)
                .select_related(
                    'asset',
                    'asset__room'
                )
                .order_by(
                    'asset__room__name',
                    'asset__name',
                    '-service_date'
                )
            )

            self.fields['maintenance'].label_from_instance = (
                lambda maintenance:
                    f"{maintenance.asset.room.name} — "
                    f"{maintenance.asset.name} — "
                    f"{maintenance.maintenance_type}"
            )

    def clean(self):
        cleaned_data = super().clean()

        asset = cleaned_data.get('asset')
        maintenance = cleaned_data.get('maintenance')

        if maintenance and asset:
            if maintenance.asset_id != asset.id:
                self.add_error(
                    'maintenance',
                    'The selected maintenance record does not belong to the selected asset.'
                )

        return cleaned_data


class ProfileForm(forms.ModelForm):

    class Meta:
        model = User
        fields = (
            'first_name',
            'last_name',
            'username',
            'email',
        )

        widgets = {
            'first_name': forms.TextInput(
                attrs={
                    'placeholder': 'First name'
                }
            ),

            'last_name': forms.TextInput(
                attrs={
                    'placeholder': 'Last name'
                }
            ),

            'username': forms.TextInput(
                attrs={
                    'placeholder': 'Username'
                }
            ),

            'email': forms.EmailInput(
                attrs={
                    'placeholder': 'Email address'
                }
            ),
        }

    def clean_email(self):
        email = self.cleaned_data['email'].lower()

        if User.objects.filter(
            email__iexact=email
        ).exclude(
            pk=self.instance.pk
        ).exists():
            raise forms.ValidationError(
                'An account with this email already exists.'
            )

        return email

    def clean_username(self):
        username = self.cleaned_data['username']

        if User.objects.filter(
            username__iexact=username
        ).exclude(
            pk=self.instance.pk
        ).exists():
            raise forms.ValidationError(
                'This username is already taken.'
            )

        return username


class HomeProfileForm(forms.ModelForm):

    class Meta:
        model = Home
        fields = (
            'name',
            'address',
        )

        widgets = {
            'name': forms.TextInput(
                attrs={
                    'placeholder': 'My Home'
                }
            ),

            'address': forms.Textarea(
                attrs={
                    'placeholder': 'Enter your home address',
                    'rows': 3
                }
            ),
        }