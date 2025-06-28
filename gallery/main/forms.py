from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.utils.translation import gettext_lazy as _
from .models import User
from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.utils.translation import gettext_lazy as _
from .models import User
from django.core.exceptions import ValidationError
import re

class UserLoginForm(AuthenticationForm):
    username = forms.CharField(
        label=_("Email или логин"),
        widget=forms.TextInput(attrs={'autofocus': True, 'class': 'form-control'})
    )
    password = forms.CharField(
        label=_("Пароль"),
        strip=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )

class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(
        label=_("Email"),
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'example@domain.com'})
    )
    username = forms.CharField(
        label=_("Логин"),
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    first_name = forms.CharField(
        label=_("Имя"),
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        required=False
    )
    last_name = forms.CharField(
        label=_("Фамилия"),
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        required=False
    )
    role = forms.ChoiceField(
        label=_("Роль"),
        choices=User.ROLE_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        initial='buyer'
    )
    
    class Meta:
        model = User
        fields = ('email', 'username', 'first_name', 'last_name', 'role', 'password1', 'password2')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})
        self.fields['role'].choices = [
            ('buyer', _('Покупатель')),
            ('seller', _('Продавец'))
        ]

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'avatar')
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'avatar': forms.FileInput(attrs={'class': 'form-control'}),
        }
    
    def clean_email(self):
        email = self.cleaned_data['email']
        
        # Проверка уникальности email
        if User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise ValidationError(_("Этот email уже используется другим пользователем."))
        
        # Простая проверка формата email
        if not re.match(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$', email):
            raise ValidationError(_("Введите корректный email адрес."))
        
        return email
    
    def clean_first_name(self):
        first_name = self.cleaned_data['first_name']
        
        # Проверка на разрешенные символы
        if not re.match(r'^[a-zA-Zа-яА-ЯёЁ\s\-]+$', first_name):
            raise ValidationError(_("Имя может содержать только буквы, пробелы и дефисы."))
        
        return first_name
    
    def clean_last_name(self):
        last_name = self.cleaned_data['last_name']
        
        # Проверка на разрешенные символы
        if not re.match(r'^[a-zA-Zа-яА-ЯёЁ\s\-]+$', last_name):
            raise ValidationError(_("Фамилия может содержать только буквы, пробелы и дефисы."))
        
        return last_name
    
from django import forms
from .models import User, Artwork, Artist, Category

class AdminUserEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = [
            'email', 
            'username', 
            'first_name', 
            'last_name', 
            'role', 
            'balance',
            'rating',
            'is_active',
            'is_staff',
            'avatar'
        ]
        widgets = {
            'role': forms.Select(choices=User.ROLE_CHOICES),
        }

class AdminArtworkForm(forms.ModelForm):
    class Meta:
        model = Artwork
        fields = '__all__'
        exclude = ['seller']  # Продавца устанавливаем в представлении
        widgets = {
            'style': forms.Select(choices=Artwork.STYLE_CHOICES),
            'medium': forms.Select(choices=Artwork.MEDIUM_CHOICES),
            'status': forms.Select(choices=Artwork.STATUS_CHOICES),
            'description': forms.Textarea(attrs={'rows': 4}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['artist'].queryset = Artist.objects.all()
        self.fields['category'].queryset = Category.objects.all()