import pytest
from services.users import UserService
from schemas.users import UpdateProfileRequest


def test_update_profile_first_name(session, verified_user):
    """Updating first_name returns the user with the new value; other fields unchanged."""
    original_last_name = verified_user.last_name
    data = UpdateProfileRequest(first_name="Updated")

    updated = UserService.update_profile(session, verified_user, data)

    assert updated.first_name == "Updated"
    assert updated.last_name == original_last_name


def test_update_profile_multiple_fields(session, verified_user):
    """All provided fields are applied at once."""
    data = UpdateProfileRequest(first_name="Jane", last_name="Doe", phone_number="+201234567890")

    updated = UserService.update_profile(session, verified_user, data)

    assert updated.first_name == "Jane"
    assert updated.last_name == "Doe"
    assert updated.phone_number == "+201234567890"


def test_update_profile_unset_fields_unchanged(session, verified_user):
    """Fields not included in the payload retain their original values."""
    original_first_name = verified_user.first_name
    original_email = verified_user.email
    data = UpdateProfileRequest(last_name="Smith")

    updated = UserService.update_profile(session, verified_user, data)

    assert updated.last_name == "Smith"
    assert updated.first_name == original_first_name
    assert updated.email == original_email
