from django import forms


class AddTagForm(forms.Form):
    account_id = forms.IntegerField(required=True)
    title = forms.CharField(required=True)
    next = forms.CharField(required=False)


class EditTagForm(forms.Form):
    tag_id = forms.IntegerField(required=True)
    title = forms.CharField(required=True)
    next = forms.CharField(required=False)


class AddTransactionForm(forms.Form):
    account_id = forms.IntegerField(required=True)
    title = forms.CharField(required=True)
    date = forms.DateTimeField(required=True)
    value = forms.IntegerField(required=True)
    discount = forms.IntegerField(required=False)
    description = forms.CharField(required=False)


class EditTransactionForm(forms.Form):
    transaction_id = forms.IntegerField(required=True)
    title = forms.CharField(required=True)
    date = forms.DateTimeField(required=True)
    value_raw = forms.IntegerField(required=True)
    discount = forms.IntegerField(required=False)
    description = forms.CharField(required=False)
