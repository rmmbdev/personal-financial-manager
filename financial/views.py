import copy
import json
import math
from datetime import datetime, timedelta

import pandas as pd
from django.contrib import messages
from django.core.exceptions import BadRequest
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views import View

from accounts.models import MemberAccount
from .forms import *
from .models import Tag, Transaction


# Create your views here.

class HomePageView(View):

    def get(self, request):
        template_name = "homepage.html"
        if not request.user.is_authenticated:
            return_url = request.get_full_path()
            return redirect(reverse('login') + "?next={}".format(return_url))

        # selected account
        # is session alright?
        account_id = int(request.GET.get("account_id", request.session["account_id"]))
        request.session["account_id"] = account_id
        selected_account = MemberAccount.objects.filter(id=account_id).first()
        if selected_account is None:
            raise BadRequest('Invalid request.')

        # the account belongs to user
        if selected_account.user_accounts.filter(id=request.user.id).first() is None:
            raise BadRequest('Invalid request.')

        # get transactions
        transactions = Transaction.objects.filter(account=selected_account).order_by('-date').all()

        # get data for charts

        # get data for tags
        account_tags = selected_account.tag_set.all()
        df = None
        for tag in account_tags:
            tmp_df = pd.DataFrame([{"tag": tag.title, **t} for t in tag.transaction_tags.all().values()])
            if df is None:
                df = tmp_df
            else:
                df = df.append(tmp_df, ignore_index=True)

        # balance per tag
        # balance_per_tag_df = df.groupby('tag').agg({'value_raw': 'sum'}).reset_index()

        # balance for month
        today = datetime.now()
        today = datetime(
            year=today.year,
            month=today.month,
            day=today.day
        )
        this_month_first_day = datetime(today.year, today.month, 1)
        transactions_df = pd.DataFrame(
            Transaction.objects
                .filter(date__gte=this_month_first_day)
                .filter(account_id=selected_account.id)
                .all()
                .values()
        )

        # total discounts
        total_discounts = 0
        if len(transactions_df) > 0:
            discount_df = transactions_df[transactions_df["discount"].notna()]
            if len(discount_df) > 0:
                total_discounts = discount_df["discount"].sum()
        this_month_discounts = int(total_discounts)

        # value = total value - total discount
        this_month_value = 0
        if len(transactions_df) > 0:
            this_month_value = transactions_df["value_raw"].sum() - total_discounts

        # last week
        last_week_start = today - timedelta(days=6)
        transactions_df = pd.DataFrame(
            Transaction.objects
                .filter(date__gte=last_week_start)
                .filter(account_id=selected_account.id)
                .all()
                .values()
        )

        # total discounts
        total_discounts = 0
        if len(transactions_df) > 0:
            discount_df = transactions_df[transactions_df["discount"].notna()]
            if len(discount_df) > 0:
                total_discounts = discount_df["discount"].sum()

        # value = total value - total discount
        last_week_value = 0
        if len(transactions_df) > 0:
            last_week_value = transactions_df["value_raw"].sum() - total_discounts
        last_week_value = int(last_week_value)

        # today
        tomorrow = today + timedelta(days=1)
        transactions_df = pd.DataFrame(
            Transaction.objects
                .filter(date__lt=tomorrow)
                .filter(date__gte=today)
                .filter(account_id=selected_account.id)
                .all()
                .values()
        )
        # total discounts
        total_discounts = 0
        if len(transactions_df) > 0:
            discount_df = transactions_df[transactions_df["discount"].notna()]
            if len(discount_df) > 0:
                total_discounts = discount_df["discount"].sum()

        # value = total value - total discount
        today_value = 0
        if len(transactions_df) > 0:
            today_value = transactions_df["value_raw"].sum() - total_discounts
        today_value = int(today_value)

        # last week by day
        last_week_start = today - timedelta(days=6)

        last_week_report_days = []
        day = copy.copy(last_week_start)
        while day <= today + timedelta(hours=23, minutes=59, seconds=56, milliseconds=1000):
            last_week_report_days.append(day.strftime("%A"))
            day += timedelta(days=1)

        transactions_df = pd.DataFrame(
            Transaction.objects
                .filter(date__gte=last_week_start)
                .filter(account_id=selected_account.id)
                .all()
                .values()
        )
        last_week_report_values = [0] * len(last_week_report_days)
        if len(transactions_df) > 0:
            transactions_df['date_name'] = transactions_df['date'].apply(
                lambda x: datetime(x.year, x.month, x.day).strftime("%A")
            )
            transactions_df.sort_values(by=['date'], inplace=True)

            for idx, d in enumerate(last_week_report_days):
                day_df = transactions_df[transactions_df["date_name"] == d]

                # discounts
                discounts = 0
                if len(day_df) > 0:
                    discount_df = day_df[day_df["discount"].notna()]
                    if len(discount_df) > 0:
                        discounts = discount_df["discount"].sum()
                if len(day_df) > 0:
                    last_week_report_values[idx] = day_df["value_raw"].sum() - discounts

        # last 10 transactions per user
        last_ten_users_transactions = []
        for user in selected_account.user_accounts.all():
            transactions_df = pd.DataFrame(
                Transaction.objects
                    .filter(account_id=selected_account.id)
                    .filter(user_id=user.id)
                    .all()
                    .order_by('-date')[:10]
                    .values()
            )

            if len(transactions_df) > 0:
                transactions_df["date"] = transactions_df["date"].apply(lambda x: x.strftime("%Y-%m-%dT%H:%M:%S.000Z"))
                dates = transactions_df["date"].values.tolist()
                # dates = [d[:19] for d in dates]

                transactions_df["discount"] = transactions_df["discount"].apply(lambda x: x if not math.isnan(x) else 0)
                transactions_df["values"] = transactions_df["value_raw"] - transactions_df["discount"]
                values = transactions_df["values"].values.tolist()
                last_ten_users_transactions.append(
                    {
                        "username": user.username,
                        "dates": dates,
                        "values": values,
                        "total": sum(values),
                        "avatar": user.profile_avatar_url
                    }
                )
            else:
                last_ten_users_transactions.append(
                    {
                        "username": user.username,
                        "dates": [],
                        "values": [],
                        "total": 0,
                    }
                )

        # tags
        this_month_first_day = datetime(today.year, today.month, 1)

        account_tags_table = []
        for ut in account_tags:
            transactions_df = pd.DataFrame(
                ut.transaction_tags
                    .filter(date__gte=last_week_start)
                    .filter(account_id=selected_account.id)
                    .all()
                    .values()
            )
            total_discounts = 0
            tag_value = 0
            if len(transactions_df) > 0:
                # total discounts
                discount_df = transactions_df[transactions_df["discount"].notna()]
                if len(discount_df) > 0:
                    total_discounts = discount_df["discount"].sum()

                # each tag
                tag_value = transactions_df["value_raw"].sum() - total_discounts

            account_tags_table.append(
                {
                    "tag": ut.title,
                    "discount": total_discounts,
                    "value": tag_value
                }
            )

        # tag values for chart
        transactions_month = Transaction.objects \
            .filter(date__gte=this_month_first_day) \
            .filter(account_id=selected_account.id) \
            .all()

        account_tags_chart = {"[{}]".format(item['tag']): 0 for item in account_tags_table}

        for transaction in transactions_month:
            value = transaction.value_raw
            if (transaction.discount is not None) and (not math.isnan(transaction.discount)):
                value = value - transaction.discount

            if transaction.tags.count() == 0:
                tags_label = "[untagged]"
                if tags_label not in account_tags_chart:
                    account_tags_chart[tags_label] = 0
                account_tags_chart[tags_label] += value

            elif transaction.tags.count() > 0:
                for tag in transaction.tags.all():
                    tags_label = "[{}]".format(tag.title)
                    account_tags_chart[tags_label] += value

            # elif transaction.tags.count() == 1:
            #     tags_label = "[{}]".format(transaction.tags.first().title)
            #     account_tags_chart[tags_label] += value
            #
            # else:
            #     tags = sorted(["[{}]".format(tag_obj.title) for tag_obj in transaction.tags.all()])
            #     tags_label = '-'.join(tags)
            #     if tags_label not in account_tags_chart:
            #         account_tags_chart[tags_label] = 0
            #     account_tags_chart[tags_label] += value

        account_tags_chart_titles = []
        account_tags_chart_values = []
        for k, v in account_tags_chart.items():
            account_tags_chart_titles.append(k)
            account_tags_chart_values.append(float("{:.2f}".format((v / (this_month_value + 1)) * 100)))
            # account_tags_chart_values.append(float("{:.2f}".format(v / this_month_value) * 100))

        context = {
            "tags": list(account_tags),
            "current_date": datetime.now(),
            "transactions": transactions,
            "this_month_value": this_month_value,
            "today_value": today_value,
            "last_week_value": last_week_value,
            "this_month_discounts": this_month_discounts,
            "last_week_report_days": last_week_report_days,
            "last_week_report_values": last_week_report_values,
            "last_ten_users_transactions": last_ten_users_transactions,
            "last_ten_users_transactions_json": json.dumps(last_ten_users_transactions, ensure_ascii=False),
            "account_tags_table": account_tags_table,
            "account_tags_chart_titles": account_tags_chart_titles,
            "account_tags_chart_values": account_tags_chart_values,
            "selected_account_id": account_id,
            "related_url": 'homepage',
        }

        return render(
            request,
            template_name=template_name,
            context=context
        )


class AddTagView(View):
    def post(self, request):
        if not request.user.is_authenticated:
            return_url = reverse("homepage")
            return redirect(reverse('login') + "?next={}".format(return_url))

        form = AddTagForm(request.POST)
        next_url = '/'
        if form.is_valid():
            account_id = form.cleaned_data.get('account_id')
            title = form.cleaned_data.get('title')
            next_url = form.cleaned_data.get('next', '/')

            # is account valid
            if request.user.user_accounts.filter(id=account_id).count() == 0:
                return BadRequest("Invalid Data!")
            account = request.user.user_accounts.filter(id=account_id).first()

            # empty title
            if not len(title.strip()):
                messages.error(request, "Title Cannot be empty!")
                return redirect(next_url)

            # not duplicated tag
            if account.tag_set.filter(title=title).count() != 0:
                messages.error(request, "You cannot have two tags with the same name!")
                return redirect(next_url)

            tag = Tag.objects.create(title=title, account_id=account_id)
            tag.save()
            return redirect(next_url)

        for f, e in list(form.errors.items()):
            messages.error(request, "[{}]: {}".format(f, e[0]))
        return redirect(next_url)


class EditsTagView(View):
    def post(self, request):
        if not request.user.is_authenticated:
            return_url = reverse("homepage")
            return redirect(reverse('login') + "?next={}".format(return_url))

        next_url = 'homepage'
        form = EditTagForm(request.POST)
        if form.is_valid():
            tag_id = form.cleaned_data.get('tag_id')
            title = form.cleaned_data.get('title')
            next_url = form.cleaned_data.get('next', '')

            # is account valid
            # check validation
            if Tag.objects.filter(id=tag_id).filter(account__in=request.user.user_accounts.all()).count() == 0:
                return BadRequest("Invalid Data!")

            tag = Tag.objects.filter(id=tag_id).first()

            # skip if new title is the same as old one
            if tag.title == title.strip():
                return redirect(next_url)

            # empty title
            if not len(title.strip()):
                messages.error(request, "Title Cannot be empty!")
                return redirect(next_url)

            tag.title = title
            tag.save()
            return redirect(next_url)

        for f, e in list(form.errors.items()):
            messages.error(request, "[{}]: {}".format(f, e[0]))
        return redirect(next_url)


class RemoveTagView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return_url = reverse("homepage")
            return redirect(reverse('login') + "?next={}".format(return_url))

        next_url = request.GET.get('next', '')
        tag_id = request.GET.get('tag_id')

        # check validation
        if Tag.objects.filter(id=tag_id).filter(account__in=request.user.user_accounts.all()).count() == 0:
            return BadRequest("Invalid Data!")

        tag = Tag.objects.filter(id=tag_id).first()
        tag.delete()

        return redirect(next_url)


class AddTransactionView(View):
    def post(self, request):
        if not request.user.is_authenticated:
            return_url = reverse("homepage")
            return redirect(reverse('login') + "?next={}".format(return_url))

        form = AddTransactionForm(request.POST)
        if form.is_valid():
            account_id = form.cleaned_data.get('account_id')
            title = form.cleaned_data.get('title')
            date = form.cleaned_data.get('date')
            value = form.cleaned_data.get('value')
            discount = form.cleaned_data.get('discount')
            description = form.cleaned_data.get('description')

            # is account valid
            if request.user.user_accounts.filter(id=account_id).count() == 0:
                return BadRequest("Invalid Data!")
            account = request.user.user_accounts.filter(id=account_id).first()

            # empty title
            if not len(title.strip()):
                messages.error(request, "Title Cannot be empty!")
                return redirect('homepage')

            # TODO check not empty fields in (value, date)

            transaction = Transaction.objects.create(
                title=title,
                date=date,
                value_raw=value,
                discount=discount,
                description=description,
                account=account,
                user=request.user
            )

            # get related tags
            tags = request.POST.getlist("tags")
            for t in tags:
                tag_object = Tag.objects.get(account=account, id=int(t))
                transaction.tags.add(tag_object)
            return redirect('homepage')

        for f, e in list(form.errors.items()):
            messages.error(request, "[{}]: {}".format(f, e[0]))
        return redirect('homepage')


class EditTransactionView(View):
    def get(self, request):
        return_url = reverse("homepage")
        if not request.user.is_authenticated:
            return redirect(reverse('login') + "?next={}".format(return_url))

        transaction_id = request.GET.get("id", "")
        transaction = Transaction.objects.filter(id=transaction_id).first()

        context = {
            "transaction_id": transaction.id,
            "title": transaction.title,
            "value_raw": transaction.value_raw,
            "discount": transaction.discount,
            "date": transaction.date,
            "description": transaction.description,
            "tags": Tag.objects.filter(account=transaction.account).all(),
            "selected_tags": [t.id for t in transaction.tags.all()],
            "related_url": "homepage"
        }
        return render(request, template_name='edit_transaction.html', context=context)

    def post(self, request):
        return_url = reverse("homepage")
        if not request.user.is_authenticated:
            return redirect(reverse('login') + "?next={}".format(return_url))

        form = EditTransactionForm(request.POST)
        if form.is_valid():
            transaction_id = form.cleaned_data.get('transaction_id')
            title = form.cleaned_data.get('title')
            date = form.cleaned_data.get('date')
            value = form.cleaned_data.get('value_raw')
            discount = form.cleaned_data.get('discount')
            description = form.cleaned_data.get('description')

            # is transaction valid
            if Transaction.objects.filter(id=transaction_id) \
                    .filter(account__in=request.user.user_accounts.all()) \
                    .count() == 0:
                return BadRequest("Invalid Data!")

            transaction = Transaction.objects.filter(id=transaction_id).first()

            # empty title
            if not len(title.strip()):
                messages.error(request, "Title Cannot be empty!")
                return redirect('homepage')

            # get related tags
            tags = request.POST.getlist("tags")
            tags = [int(t) for t in tags]
            transaction_tags = [t["id"] for t in transaction.tags.all().values()]

            diff_tags = set(tags).union(set(transaction_tags)) - set(tags).intersection(set(transaction_tags))
            is_tags_changed = len(diff_tags) != 0

            # if no field is changed
            # skip update
            if transaction.title == title and \
                    transaction.date == date and \
                    transaction.value_raw == value and \
                    transaction.discount == discount and \
                    transaction.description == description and \
                    not is_tags_changed:
                return redirect('homepage')

            # TODO check not empty fields in (value, date)

            transaction.title = title
            transaction.date = date
            transaction.value_raw = value
            transaction.discount = discount
            transaction.description = description
            transaction.save()

            if not is_tags_changed:
                return redirect('homepage')

            # remove existing tags
            transaction_tags = transaction.tags.all()
            for tt in transaction_tags:
                transaction.tags.remove(tt)

            # add new ones
            for t in tags:
                tag_object = Tag.objects.get(account=transaction.account, id=t)
                transaction.tags.add(tag_object)

            return redirect('homepage')

        for f, e in list(form.errors.items()):
            messages.error(request, "[{}]: {}".format(f, e[0]))
        return redirect('homepage')


def remove_transaction(request):
    if not request.user.is_authenticated:
        return_url = reverse("homepage")
        return redirect(reverse('login') + "?next={}".format(return_url))

    if request.method != "GET":
        return BadRequest("Invalid Request Method!")

    transaction_id = request.GET.get('id', '')
    if not len(transaction_id):
        messages.error(request, "Not valid transaction id!")
        return redirect('homepage')

    # is transaction valid
    if Transaction.objects.filter(id=transaction_id) \
            .filter(account__in=request.user.user_accounts.all()) \
            .count() == 0:
        return BadRequest("Invalid Data!")

    transaction = Transaction.objects.filter(id=transaction_id).first()
    transaction.delete()

    return redirect('homepage')
