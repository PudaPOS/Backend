import uuid

from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect

# Create your views here.
from posapp.forms import CreateUserForm
from posapp.models import Tab, ProductInTab, Product, User, Currency, Till, TillPaymentOptions
from posapp.security import waiter_login_required, manager_login_required, admin_login_required


def prepare_context(request):
    return {
        'page': request.get_full_path()[1:],
        'waiter_role': request.user.is_waiter,
        'manager_role': request.user.is_manager,
        'admin_role': request.user.is_admin,
    }


def add_pagination_context(context, manager, page, page_length, key):
    count = manager.count()
    last_page = count // page_length
    context[key] = {}

    context[key]['data'] = manager[page * page_length:(page + 1) * page_length]

    context[key]['showing'] = {}
    context[key]['showing']['from'] = page * page_length
    context[key]['showing']['to'] = min((page + 1) * page_length - 1, count - 1)
    context[key]['showing']['of'] = count

    context[key]['pages'] = {}
    context[key]['pages']['previous'] = page - 1
    context[key]['pages']['showPrevious'] = context[key]['pages']['previous'] >= 0
    context[key]['pages']['next'] = page + 1
    context[key]['pages']['showNext'] = context[key]['pages']['next'] <= last_page
    context[key]['pages']['last'] = last_page

    links = []
    if page < (last_page / 2):
        first_link = max(0, page - 2)
        start = first_link
        end = min(last_page + 1, first_link + 5)
    else:
        last_link = min(last_page, page + 2) + 1
        start = max(0, last_link - 5)
        end = last_link

    for i in range(start, end):
        links.append({'page': i, 'active': i == page})

    context[key]['pages']['links'] = links


def generate_page_length_options(page_length):
    options = {
        "len5": False,
        "len10": False,
        "len20": False,
        "len50": False,
        "len100": False,
        "len200": False,
        "len500": False,
        "other": False,
        "value": page_length,
    }
    if "len" + str(page_length) in options:
        options["len" + str(page_length)] = True
    else:
        options["other"] = True
    return options


@login_required
def index(request):
    return redirect("waiter/tabs")


@waiter_login_required
def waiter_tabs(request):
    context = prepare_context(request)
    tabs = []
    tabs_list = Tab.objects.filter(state=Tab.OPEN)
    for tab in tabs_list:
        out = {
            'name': tab.name,
            'id': tab.id,
            'total': tab.total,
            'products': []
        }

        products_list = ProductInTab.objects.filter(tab=tab)
        products = {}
        for product in products_list:
            if product.product.id not in products:
                products[product.product.id] = {
                    'id': product.product.id,
                    'name': product.product.name,
                    'variants': {},
                }

            if product.note not in products[product.product.id]['variants']:
                products[product.product.id]['variants'][product.note] = {
                    'note': product.note,
                    'orderedCount': 0,
                    'preparingCount': 0,
                    'toServeCount': 0,
                    'servedCount': 0,
                    'showOrdered': False,
                    'showPreparing': False,
                    'showToServe': False,
                    'showServed': False,
                }

            if product.state == ProductInTab.ORDERED:
                products[product.product.id]['variants'][product.note]['orderedCount'] += 1
                products[product.product.id]['variants'][product.note]['showOrdered'] = True
            elif product.state == ProductInTab.PREPARING:
                products[product.product.id]['variants'][product.note]['preparingCount'] += 1
                products[product.product.id]['variants'][product.note]['showPreparing'] = True
            elif product.state == ProductInTab.TO_SERVE:
                products[product.product.id]['variants'][product.note]['toServeCount'] += 1
                products[product.product.id]['variants'][product.note]['showToServe'] = True
            elif product.state == ProductInTab.SERVED:
                products[product.product.id]['variants'][product.note]['servedCount'] += 1
                products[product.product.id]['variants'][product.note]['showServed'] = True

        for product in products:
            variants = []
            for variant in products[product]['variants']:
                variants.append(products[product]['variants'][variant])

            out['products'].append({
                'id': products[product]['id'],
                'name': products[product]['name'],
                'variants': variants,
            })

        tabs.append(out)

    context['tabs'] = tabs
    context['products'] = []
    for product in Product.objects.all():
        context['products'].append({
            'id': product.id,
            'name': product.name,
        })
    return render(request, template_name="waiter/tabs.html", context=context)


@waiter_login_required
def waiter_orders(request):
    context = prepare_context(request)
    return render(request, template_name="waiter/orders.html", context=context)


@manager_login_required
def manager_users_overview(request):
    context = prepare_context(request)
    page_length = int(request.GET.get('page_length', 20))
    page = int(request.GET.get('page', 0))

    users = User.objects.filter(is_active=True).order_by("last_name", "first_name")
    context['me'] = request.user.username
    add_pagination_context(context, users, page, page_length, 'users')

    return render(request, template_name="manager/users/overview.html", context=context)


def check_dict(dict, keys):
    for key in keys:
        if key not in dict:
            return False
    return True


@manager_login_required
def manager_users_create(request):
    context = prepare_context(request)
    if request.method == 'GET':
        form = CreateUserForm()
    elif request.method == 'POST':
        print(request.POST)
        user = User()
        form = CreateUserForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(f'/manager/users/overview?created={form.cleaned_data["username"]}',
                                        permanent=False)
        else:
            print("form is not valid")

    else:
        # TODO Replace with proper handler
        assert False
    context['form'] = form
    return render(request, template_name="manager/users/create.html", context=context)


@manager_login_required
def manager_tills_overview(request, result=None):
    context = prepare_context(request)
    page_length = int(request.GET.get('page_length', 20))
    page_open = int(request.GET.get('page_open', 0))
    page_stopped = int(request.GET.get('page_closed', 0))
    page_counted = int(request.GET.get('page_counted', 0))

    open_tills = Till.objects.filter(state=Till.OPEN)
    stopped_tills = Till.objects.filter(state=Till.STOPPED)
    counted_tills = Till.objects.filter(state=Till.COUNTED)
    add_pagination_context(context, open_tills, page_open, page_length, 'open')
    add_pagination_context(context, stopped_tills, page_stopped, page_length, 'stopped')
    add_pagination_context(context, counted_tills, page_counted, page_length, 'counted')

    context["page_open"] = page_open
    context["page_stopped"] = page_stopped
    context["page_counted"] = page_counted
    context["page_length"] = generate_page_length_options(page_length)

    if result:
        context["message"] = result

    return render(request, template_name="manager/tills/overview.html", context=context)


@manager_login_required
def manager_tills_assign(request):
    context = prepare_context(request)

    if request.method == 'POST':
        if all(k in request.POST for k in ["users", "options"]):
            usernames = request.POST.getlist("users")
            options_id = request.POST["options"]

            try:
                options = TillPaymentOptions.objects.get(id=uuid.UUID(options_id))
                till = options.create_till()
                for username in usernames:
                    user = User.objects.get(username=username)
                    till.cashiers.add(user)
            except User.DoesNotExist:
                context["error"] = "One of the selected users does not exist"
            except TillPaymentOptions.DoesNotExist:
                context["error"] = "The selected payment options config does not exist. " \
                                   "It may have also been disabled by an administrator."
        else:
            context["error"] = "Some required fields are missing"

    context["users"] = User.objects.filter(is_waiter=True)
    context["options"] = TillPaymentOptions.objects.filter(enabled=True)

    return render(request, template_name="manager/tills/assign.html", context=context)


@manager_login_required
def manager_tills_id(request, id):
    context = prepare_context(request)


@manager_login_required
def manager_tills_id_stop(request):
    if request.method == "GET":
        return redirect('manager/tills/overview')
    elif request.method == "POST":
        try:
            till = Till.objects.get(id=uuid.UUID(request.POST["id"]))
            if till.state == Till.OPEN:
                if till.stop():
                    color = 'success'
                    message = 'The till was stopped successfully. It is now available for counting.'
                    icon = 'check'
                else:
                    color = 'danger'
                    message = 'An error occured during stopping. Please try again.'
                    icon = 'times'
            else:
                color = 'warning'
                message = f'The till is in a state from which it cannot be closed: {till.state}'
                icon = 'exclamation-triangle'
        except Till.DoesNotExist:
            color = 'danger'
            message = 'The specified till does not exist.'
            icon = 'times'
        return manager_tills_overview(request, {"color": color, "message": message, "icon": icon})


@manager_login_required
def manager_tills_id_count(request, id):
    context = prepare_context(request)
    context["id"] = id

    return render(request, template_name="manager/tills/id/count.html", context=context)


@admin_login_required
def admin_finance_currencies(request):
    context = prepare_context(request)
    page_length = int(request.GET.get('page_length', 20))
    search = request.GET.get('search', '')
    page = int(request.GET.get('page', 0))

    currencies = Currency.objects.filter(
        Q(name__contains=search) | Q(code__contains=search) | Q(symbol__contains=search)).order_by('code')
    add_pagination_context(context, currencies, page, page_length, 'currencies')

    context["page_number"] = page
    context["page_length"] = generate_page_length_options(page_length)
    context["search"] = search

    return render(request, template_name="admin/finance/currencies.html", context=context)


@admin_login_required
def admin_finance_methods(request):
    context = prepare_context(request)
