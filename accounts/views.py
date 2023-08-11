from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from django.core.exceptions import BadRequest
from django.shortcuts import render, redirect, reverse
from django.views import View

from .forms import *
from .models import User, MemberAccount, Invitation


class LoginView(View):
    def get(self, request):
        next_url = '/'
        if request.GET.get('next') is not None:
            next_url = request.GET.get('next')

        context = {'next': next_url}
        return render(request, "login.html", context=context)

    def post(self, request):
        next_url = '/'
        if request.GET.get('next') is not None:
            next_url = request.GET.get('next')

        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.info(request, f"You are now logged in as {username}")

                # get member accounts
                if request.user.user_accounts.filter(id=user.default_account_id).count() != 0:
                    account = request.user.user_accounts.filter(id=user.default_account_id).first()
                else:
                    account = request.user.user_accounts.first()
                request.session['account_id'] = account.id

                return redirect(next_url)

        # invalid anything
        messages.error(request, "Invalid username or password.")
        context = {'next': next_url}
        return render(request, "login.html", context=context)


class RegisterView(View):

    def get(self, request):
        if request.user.is_authenticated:
            return redirect(reverse('logout') + "?next={}".format(reverse("register")))
        return render(request, 'register.html')

    def post(self, request):
        form = RegisterForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('email')
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            confirm_password = form.cleaned_data.get('confirm_password')
            if password != confirm_password:
                # messages.ERROR(request, "Not Valid Password! Use More Complex One!")
                messages.error(request, "Password and its confirmation should be the same!")
                return redirect('register')

            if User.objects.filter(username=username).count() != 0:
                messages.error(request, "Username Already Taken! Pick Another one!")
                return redirect('register')

            user = User.objects.create_user(
                username=username,
                email=email,
                password=password
            )
            user.save()

            # create default account
            account = MemberAccount.objects.create(title="Personal")
            account.save()

            user.user_accounts.add(account)

            user.default_account_id = account.id
            user.save()

            return redirect('login')
        else:
            messages.error(request, form.errors)
            return redirect('register')


class ProfileView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return_url = reverse("profile")
            return redirect(reverse('login') + "?next={}".format(return_url))

        # user accounts
        accounts = request.user.user_accounts.all()

        # invitations
        invitations = Invitation.objects.filter(user_id=request.user.id).filter(status='p').all()

        context = {
            "accounts": accounts,
            "invitations": invitations,
            "related_url": "profile",
        }
        return render(request, 'profile.html', context=context)


def update_personal_details(request):
    if not request.user.is_authenticated:
        return_url = reverse("profile")
        return redirect(reverse('login') + "?next={}".format(return_url))

    if request.method != "POST":
        return BadRequest("Invalid Request Method!")

    form = UpdatePersonalDetailsForm(request.POST)
    if form.is_valid():
        email = form.cleaned_data.get('email')
        username = form.cleaned_data.get('username')
        mobile_number = form.cleaned_data.get('mobile_number')
        profile_avatar_url = form.cleaned_data.get('profile_avatar_url')

        # if no field is changed
        # skip the post
        if ((email == request.user.email) and
                (username == request.user.username) and
                (mobile_number == request.user.mobile_number) and
                (profile_avatar_url == request.user.profile_avatar_url)):
            return redirect('profile')

        # if username already exists
        if username != request.user.username:
            if not len(username.strip()):
                messages.error(request, "Username Cannot be empty!")
                return redirect('profile')

            if User.objects.filter(username=username).count() != 0:
                messages.error(request, "Username Already Taken! Pick Another one!")
                return redirect('profile')

        if not len(email.strip()):
            messages.error(request, "Email Cannot be empty!")
            return redirect('profile')

        if not len(profile_avatar_url.strip()):
            messages.error(request, "Avatar Cannot be empty!")
            return redirect('profile')

        user = User.objects.filter(id=request.user.id).first()
        user.username = username
        user.email = email
        user.mobile_number = mobile_number
        user.profile_avatar_url = profile_avatar_url.replace('/static/', '')
        user.save()
        messages.info(request, "Personal Data Updated!")
        return redirect('profile')

    for f, e in list(form.errors.items()):
        messages.error(request, "[{}]: {}".format(f, e[0]))
    return redirect('profile')


def set_default_account(request):
    if not request.user.is_authenticated:
        return_url = reverse("profile")
        return redirect(reverse('login') + "?next={}".format(return_url))

    if request.method != "GET":
        return BadRequest("Invalid Request Method!")

    # get data
    account_id = request.GET.get('account_id')

    # check validation
    if request.user.user_accounts.filter(id=account_id).count() == 0:
        return BadRequest("Invalid Data!")

    user = User.objects.filter(id=request.user.id).first()
    user.default_account_id = account_id
    user.save()

    return redirect('profile')


def create_account(request):
    if not request.user.is_authenticated:
        return_url = reverse("profile")
        return redirect(reverse('login') + "?next={}".format(return_url))

    if request.method != "POST":
        return BadRequest("Invalid Request Method!")

    form = CreateAccountForm(request.POST)
    if form.is_valid():
        title = form.cleaned_data.get('title')

        if not len(title.strip()):
            messages.error(request, "Title Cannot be empty!")
            return redirect('profile')

        # check the account belongs to this user or not
        if request.user.user_accounts.filter(title=title).count() != 0:
            messages.error(request, "You cannot have 2 accounts with the same name! Please Choose Another One")
            return redirect('profile')

        account = MemberAccount(title=title, owner_id=request.user.id)
        account.save()

        request.user.user_accounts.add(account)

        return redirect('profile')

    for f, e in list(form.errors.items()):
        messages.error(request, "[{}]: {}".format(f, e[0]))
    return redirect('profile')


def update_account(request):
    if not request.user.is_authenticated:
        return_url = reverse("profile")
        return redirect(reverse('login') + "?next={}".format(return_url))

    if request.method != "POST":
        return BadRequest("Invalid Request Method!")

    form = UpdateAccountForm(request.POST)
    if form.is_valid():
        account_id = form.cleaned_data.get('id')
        title = form.cleaned_data.get('title')

        if account_id is None:
            return BadRequest("Invalid Form Data!")

        if not len(title.strip()):
            messages.error(request, "Title Cannot be empty!")
            return redirect('profile')

        # check the account belongs to this user or not
        if request.user.user_accounts.filter(id=account_id).count() == 0:
            return BadRequest("Invalid Form Data!")

        account = MemberAccount.objects.filter(id=account_id).first()

        # if no field is changed
        # skip the post
        if account.title == title:
            return redirect('profile')

        account.title = title
        account.save()
        return redirect('profile')

    for f, e in list(form.errors.items()):
        messages.error(request, "[{}]: {}".format(f, e[0]))
    return redirect('profile')


def delete_account(request):
    if not request.user.is_authenticated:
        return_url = reverse("profile")
        return redirect(reverse('login') + "?next={}".format(return_url))

    if request.method != "GET":
        return BadRequest("Invalid Request Method!")

    # get data
    account_id = request.GET.get('account_id')

    # check validation
    if request.user.user_accounts.filter(id=account_id).count() == 0:
        return BadRequest("Invalid Data!")

    # remove from user accounts
    account = request.user.user_accounts.filter(id=account_id).first()

    if account.id == request.user.default_account_id:
        messages.error(request, "Cannot Delete Default Account!")
        return redirect('profile')

    request.user.user_accounts.remove(account)

    # delete account if no more user account is available
    if account.user_accounts.count() == 0:
        account.delete()

    return redirect('profile')


def invite_user(request):
    if not request.user.is_authenticated:
        return_url = reverse("profile")
        return redirect(reverse('login') + "?next={}".format(return_url))

    if request.method != "POST":
        return BadRequest("Invalid Request Method!")

    form = InviteForm(request.POST)
    if form.is_valid():
        account_id = form.cleaned_data.get('id')
        username = form.cleaned_data.get('username')

        if account_id is None:
            return BadRequest("Invalid Form Data!")

        if not len(username.strip()):
            messages.error(request, "Username Cannot be empty!")
            return redirect('profile')

        # check the account belongs to this user or not
        if request.user.user_accounts.filter(id=account_id).count() == 0:
            return BadRequest("Invalid Form Data!")

        # check user is owner of account
        if request.user.user_accounts.filter(id=account_id).first().owner != request.user:
            messages.error(request, "Only Account Owners can Add Users!")
            return redirect('profile')

        # check user exists
        if User.objects.filter(username=username).count() == 0:
            messages.error(request, "Username not found!")
            return redirect('profile')

        # check not inviting yourself :D
        if User.objects.filter(username=username).first() == request.user:
            messages.error(request, "You Cannot Invite Yourself!")
            return redirect('profile')

        invitation = Invitation.objects.create(
            account_id=account_id,
            user_id=User.objects.filter(username=username).first().id
        )
        invitation.save()
        return redirect('profile')

    for f, e in list(form.errors.items()):
        messages.error(request, "[{}]: {}".format(f, e[0]))
    return redirect('profile')


def accept_invitation(request):
    if not request.user.is_authenticated:
        return_url = reverse("profile")
        return redirect(reverse('login') + "?next={}".format(return_url))

    if request.method != "GET":
        return BadRequest("Invalid Request Method!")

    # get data
    invitation_id = request.GET.get('invitation_id')

    if Invitation.objects.filter(id=invitation_id).count() == 0:
        return BadRequest("Invalid Form Data!")

    invitation = Invitation.objects.filter(id=invitation_id).first()
    account = invitation.account
    request.user.user_accounts.add(account)

    invitation.status = "a"
    invitation.save()

    return redirect('profile')


def decline_invitation(request):
    if not request.user.is_authenticated:
        return_url = reverse("profile")
        return redirect(reverse('login') + "?next={}".format(return_url))

    if request.method != "GET":
        return BadRequest("Invalid Request Method!")

    # get data
    invitation_id = request.GET.get('invitation_id')

    if Invitation.objects.filter(id=invitation_id).count() == 0:
        return BadRequest("Invalid Form Data!")

    invitation = Invitation.objects.filter(id=invitation_id).first()
    invitation.status = "d"
    invitation.save()

    return redirect('profile')


def deactivate_user_account(request):
    pass


def logout_page(request):
    logout(request)
    return redirect("login")


def change_account(request):
    if request.method != "GET":
        return BadRequest("Invalid Request Method!")
    if not request.user.is_authenticated:
        return redirect(reverse('login') + "?next={}".format(reverse("change_account")))

    next_url = "/"
    if request.GET.get('next') is not None:
        next_url = request.GET.get('next')

    if request.GET.get('account_id') is not None:
        account_id = request.GET.get('account_id')
        if account_id.isdigit():
            account_id = int(account_id)
            account = request.user.user_accounts.filter(id=account_id)
            if account.count() != 0:
                request.session['account_id'] = account.first().id
                return redirect(next_url)

    messages.error(request, "not valid account_id")
    return redirect(next_url)


def change_password(request):
    return_url = reverse("profile")
    if not request.user.is_authenticated:
        return redirect(reverse('login') + "?next={}".format(return_url))

    if request.method != "POST":
        return BadRequest("Invalid Request Method!")

    # Get the posted form
    form = ChangePasswordForm(request.POST)
    if form.is_valid():
        password = form.cleaned_data.get('password')
        confirm_password = form.cleaned_data.get('confirm_password')

        if not (password == confirm_password):
            for f, e in list(form.errors.items()):
                messages.error(request, "[{}]: {}".format(f, e[0]))
            return redirect('profile')

        request.user.set_password(password)
        messages.info(request, "Password Changed!")
        return redirect("profile")

    for f, e in list(form.errors.items()):
        messages.error(request, "[{}]: {}".format(f, e[0]))
    return redirect('profile')
