import pytest
from django.contrib.auth.models import AnonymousUser, User
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.test import RequestFactory

from accounts import permissions as perm
from accounts.models import Profile

rf = RequestFactory()


def make_user(username, role="OP", status="A", is_active=True):
    u = User.objects.create_user(username, password="x", is_active=is_active)
    Profile.objects.filter(user=u).update(role=role, status=status)
    return User.objects.get(pk=u.pk)          # reload so the cached profile is fresh


def request_for(user):
    r = rf.get("/x")
    r.user = user
    return r


# ---------- who counts as an active member ----------
def test_anonymous_has_no_access():
    anon = AnonymousUser()
    assert perm.is_active_member(anon) is False
    assert perm.role_level(anon) == 0
    assert perm.has_role(anon, perm.OPERATIVE) is False
    assert perm.has_capability(anon, "sales.create") is False


@pytest.mark.django_db
@pytest.mark.parametrize("status", ["PEN", "INA", "OL"])
def test_non_active_status_blocked(status):
    u = make_user(f"u_{status}", status=status)
    assert perm.is_active_member(u) is False
    assert perm.role_level(u) == 0
    assert perm.has_capability(u, "sales.create") is False


@pytest.mark.django_db
def test_disabled_django_account_blocked():
    u = make_user("disabled", is_active=False)
    assert perm.is_active_member(u) is False


@pytest.mark.django_db
def test_user_without_profile_blocked():
    u = User.objects.create_user("noprofile", password="x")
    Profile.objects.filter(user=u).delete()
    u = User.objects.get(pk=u.pk)
    assert perm.get_profile(u) is None
    assert perm.is_active_member(u) is False
    assert perm.has_capability(u, "sales.create") is False


@pytest.mark.django_db
def test_superuser_is_always_admin():
    su = User.objects.create_superuser("root", password="x")
    su = User.objects.get(pk=su.pk)
    assert perm.is_active_member(su) is True
    assert perm.role_level(su) == 3
    assert perm.is_admin(su) and perm.is_manager(su)
    assert perm.has_capability(su, "staff.delete") is True


# ---------- role levels and has_role ----------
@pytest.mark.django_db
@pytest.mark.parametrize("role,level", [("OP", 1), ("EX", 2), ("AD", 3)])
def test_role_levels(role, level):
    assert perm.role_level(make_user(f"r_{role}", role=role)) == level


@pytest.mark.django_db
@pytest.mark.parametrize("role,min_role,expected", [
    ("OP", "OP", True), ("OP", "EX", False), ("OP", "AD", False),
    ("EX", "OP", True), ("EX", "EX", True), ("EX", "AD", False),
    ("AD", "OP", True), ("AD", "EX", True), ("AD", "AD", True),
    ("AD", "XX", False),                      # unknown minimum role fails closed
])
def test_has_role_matrix(role, min_role, expected):
    assert perm.has_role(make_user(f"m_{role}_{min_role}", role=role), min_role) is expected


@pytest.mark.django_db
def test_is_manager_and_is_admin():
    op, ex, ad = make_user("o"), make_user("e", "EX"), make_user("a", "AD")
    assert (perm.is_manager(op), perm.is_manager(ex), perm.is_manager(ad)) == (False, True, True)
    assert (perm.is_admin(op), perm.is_admin(ex), perm.is_admin(ad)) == (False, False, True)


@pytest.mark.django_db
def test_blank_or_unknown_role_falls_back_to_operative():
    for i, role in enumerate(["", "ZZ"]):
        u = make_user(f"odd{i}", role=role)
        assert perm.role_level(u) == 1
        assert perm.has_capability(u, "sales.create") is True
        assert perm.has_capability(u, "sales.void") is False


# ---------- capabilities per role ----------
@pytest.mark.django_db
@pytest.mark.parametrize("role,capability,expected", [
    ("OP", "sales.create", True),
    ("OP", "sales.void", False),
    ("OP", "purchases.manage", False),
    ("OP", "staff.create", False),
    ("EX", "sales.create", True),
    ("EX", "sales.void", True),
    ("EX", "purchases.manage", True),
    ("EX", "staff.create", False),
    ("AD", "sales.void", True),
    ("AD", "staff.create", True),
    ("OP", "does.not.exist", False),         # unknown capability fails closed
    ("AD", "does.not.exist", False),
])
def test_capability_matrix(role, capability, expected):
    u = make_user(f"c_{role}_{capability}", role=role)
    assert perm.has_capability(u, capability) is expected


# ---------- function view guards ----------
@perm.role_required(perm.EXECUTIVE)
def exec_view(request):
    return HttpResponse("ok")


@perm.capability_required("sales.void")
def void_view(request):
    return HttpResponse("ok")


@pytest.mark.django_db
def test_role_required_decorator():
    anon = exec_view(request_for(AnonymousUser()))
    assert anon.status_code == 302 and "next=" in anon.url
    with pytest.raises(PermissionDenied):
        exec_view(request_for(make_user("d_op", "OP")))
    assert exec_view(request_for(make_user("d_ex", "EX"))).status_code == 200
    assert exec_view(request_for(make_user("d_ad", "AD"))).status_code == 200


@pytest.mark.django_db
def test_capability_required_decorator():
    anon = void_view(request_for(AnonymousUser()))
    assert anon.status_code == 302 and "next=" in anon.url
    with pytest.raises(PermissionDenied):
        void_view(request_for(make_user("v_op", "OP")))
    assert void_view(request_for(make_user("v_ex", "EX"))).status_code == 200


# ---------- class view guards ----------
def guard(mixin, user, **attrs):
    g = mixin()
    g.request = request_for(user)
    for k, v in attrs.items():
        setattr(g, k, v)
    return g.test_func()


@pytest.mark.django_db
def test_role_mixins():
    op, ex, ad = make_user("k_op"), make_user("k_ex", "EX"), make_user("k_ad", "AD")
    assert guard(perm.RoleRequiredMixin, op) is True
    assert guard(perm.ManagerRequiredMixin, op) is False
    assert guard(perm.ManagerRequiredMixin, ex) is True
    assert guard(perm.AdminRequiredMixin, ex) is False
    assert guard(perm.AdminRequiredMixin, ad) is True


@pytest.mark.django_db
def test_capability_mixins():
    ex, ad = make_user("q_ex", "EX"), make_user("q_ad", "AD")
    assert guard(perm.CapabilityRequiredMixin, ex, required_capability="sales.void") is True
    assert guard(perm.CapabilityRequiredMixin, ex, required_capability="") is False
    for mixin in (perm.StaffViewRequiredMixin, perm.StaffCreateRequiredMixin,
                  perm.StaffUpdateRequiredMixin, perm.StaffDeleteRequiredMixin):
        assert guard(mixin, ex) is False
        assert guard(mixin, ad) is True
