from django import forms


class LoginForm(forms.Form):
    username = forms.CharField(max_length=100)
    password = forms.CharField(widget=forms.PasswordInput())


class RegisterForm(forms.Form):
    email = forms.CharField(max_length=100)
    username = forms.CharField(max_length=100)
    password = forms.CharField(widget=forms.PasswordInput())
    confirm_password = forms.CharField(widget=forms.PasswordInput())


class ChangePasswordForm(forms.Form):
    password = forms.CharField(widget=forms.PasswordInput(), required=True)
    confirm_password = forms.CharField(widget=forms.PasswordInput(), required=True)


class UpdatePersonalDetailsForm(forms.Form):
    username = forms.CharField(max_length=100)
    email = forms.CharField(max_length=100)
    mobile_number = forms.CharField(max_length=11)
    profile_avatar_url = forms.CharField(max_length=2000)


class CreateAccountForm(forms.Form):
    title = forms.CharField(max_length=100, required=True)


class UpdateAccountForm(forms.Form):
    id = forms.IntegerField(required=True)
    title = forms.CharField(max_length=100, required=True)


class InviteForm(forms.Form):
    id = forms.IntegerField(required=True)
    username = forms.CharField(max_length=100, required=True)
