from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User

from .models import Destination, Lead, Tour


class EmailLoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].label = "Email"
        self.fields["username"].widget.attrs.update(
            {"class": "form-control", "autocomplete": "username"}
        )
        self.fields["password"].widget.attrs.update(
            {"class": "form-control", "autocomplete": "current-password"}
        )


class LeadForm(forms.ModelForm):
    next = forms.CharField(required=False, widget=forms.HiddenInput())

    class Meta:
        model = Lead
        fields = (
            "name",
            "email",
            "phone",
            "message",
            "destination_interest",
            "related_tour",
            "source_page",
        )
        widgets = {
            "message": forms.Textarea(attrs={"rows": 4}),
            "phone": forms.TextInput(attrs={"autocomplete": "tel"}),
            "source_page": forms.HiddenInput(),
            "related_tour": forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["destination_interest"].required = False
        self.fields["destination_interest"].queryset = Destination.objects.all()
        self.fields["related_tour"].required = False
        self.fields["related_tour"].queryset = Tour.objects.select_related(
            "destination"
        ).order_by("destination__name", "name")
        self.fields["source_page"].required = False
        self.fields["name"].widget.attrs.setdefault("autocomplete", "name")
        self.fields["email"].widget.attrs.setdefault("autocomplete", "email")
        for name, field in self.fields.items():
            if name in ("next", "source_page"):
                continue
            w = field.widget
            if isinstance(w, (forms.TextInput, forms.EmailInput, forms.Textarea)):
                w.attrs.setdefault("class", "form-control")
            elif isinstance(w, forms.Select):
                w.attrs.setdefault("class", "form-select")


class TravelerSignUpForm(forms.ModelForm):
    password1 = forms.CharField(
        label="Password",
        strip=False,
        widget=forms.PasswordInput(
            attrs={"autocomplete": "new-password", "class": "form-control"}
        ),
    )
    password2 = forms.CharField(
        label="Confirm password",
        strip=False,
        widget=forms.PasswordInput(
            attrs={"autocomplete": "new-password", "class": "form-control"}
        ),
    )

    class Meta:
        model = User
        fields = ("email", "first_name", "last_name")
        widgets = {
            "email": forms.EmailInput(
                attrs={"autocomplete": "email", "class": "form-control"}
            ),
            "first_name": forms.TextInput(
                attrs={"autocomplete": "given-name", "class": "form-control"}
            ),
            "last_name": forms.TextInput(
                attrs={"autocomplete": "family-name", "class": "form-control"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in ("password1", "password2"):
            self.fields[name].widget.attrs.setdefault("class", "form-control")

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(username=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def clean(self):
        data = super().clean()
        p1 = data.get("password1")
        p2 = data.get("password2")
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("The two password fields didn’t match.")
        return data

    def save(self, commit=True):
        user = super().save(commit=False)
        email = self.cleaned_data["email"].strip().lower()
        user.username = email
        user.email = email
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class UserProfileDetailsForm(forms.ModelForm):
    phone = forms.CharField(
        max_length=40,
        required=False,
        widget=forms.TextInput(
            attrs={"autocomplete": "tel", "class": "form-control"}
        ),
    )
    country = forms.CharField(
        max_length=80,
        required=False,
        widget=forms.TextInput(
            attrs={"autocomplete": "country", "class": "form-control"}
        ),
    )

    class Meta:
        model = User
        fields = ("first_name", "last_name", "email")
        widgets = {
            "first_name": forms.TextInput(
                attrs={"autocomplete": "given-name", "class": "form-control"}
            ),
            "last_name": forms.TextInput(
                attrs={"autocomplete": "family-name", "class": "form-control"}
            ),
            "email": forms.EmailInput(
                attrs={"autocomplete": "email", "class": "form-control"}
            ),
        }

    def __init__(self, *args, profile_instance=None, **kwargs):
        self.profile_instance = profile_instance
        super().__init__(*args, **kwargs)
        if profile_instance is not None:
            self.fields["phone"].initial = profile_instance.phone
            self.fields["country"].initial = profile_instance.country

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if (
            User.objects.filter(username=email)
            .exclude(pk=self.instance.pk)
            .exists()
        ):
            raise forms.ValidationError("That email is already in use.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data["email"].strip().lower()
        user.email = user.username
        if commit:
            user.save()
            if self.profile_instance is not None:
                self.profile_instance.phone = self.cleaned_data.get("phone", "")
                self.profile_instance.country = self.cleaned_data.get("country", "")
                self.profile_instance.save()
        return user
