def user_accounts_context(request):
    if not request.user.is_authenticated:
        return {}

    user_accounts = request.user.user_accounts.all()
    return {
        'selected_account_id': int(request.session["account_id"]) if "account_id" in request.session else 0,
        'user_accounts': user_accounts,
    }
