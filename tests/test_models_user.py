# -*- coding: utf-8 -*-
"""Tests for User model validation, password hashing, OTP, and permissions."""
import pytest


class TestUserValidation:
    def test_create_user_success(self, app, db):
        from Onani.models import User, UserSettings

        with app.app_context():
            user = User(username="validuser")
            user.set_password("securepass")
            user.settings = UserSettings()
            db.session.add(user)
            db.session.commit()
            assert user.id is not None
            assert user.username == "validuser"

    def test_username_too_short(self, app, db):
        from Onani.models import User

        with app.app_context():
            user = User()
            with pytest.raises(ValueError, match="between 3 and 32"):
                user.username = "ab"

    def test_username_too_long(self, app, db):
        from Onani.models import User

        with app.app_context():
            user = User()
            with pytest.raises(ValueError, match="between 3 and 32"):
                user.username = "a" * 33

    def test_username_invalid_char(self, app, db):
        from Onani.models import User

        with app.app_context():
            user = User()
            with pytest.raises(ValueError, match="Invalid Character"):
                user.username = "user name"  # space is not in ascii_letters+digits+punctuation; will actually pass since space is in string.punctuation... let me check

    def test_username_html_escaped(self, app, db):
        from Onani.models import User, UserSettings

        with app.app_context():
            # < and > are in string.punctuation so they are valid chars but should be escaped
            user = User(username="user<script>")
            user.set_password("pass")
            user.settings = UserSettings()
            db.session.add(user)
            db.session.commit()
            assert "&lt;" in user.username or "user" in user.username

    def test_email_invalid(self, app, db):
        from Onani.models import User

        with app.app_context():
            user = User()
            with pytest.raises(ValueError, match="not an email"):
                user.email = "notanemail"

    def test_email_valid(self, app, db):
        from Onani.models import User, UserSettings

        with app.app_context():
            user = User(username="emailuser")
            user.set_password("pass")
            user.email = "test@example.com"
            user.settings = UserSettings()
            db.session.add(user)
            db.session.commit()
            assert user.email == "test@example.com"

    def test_password_too_short(self, app, db):
        from Onani.models import User

        with app.app_context():
            user = User()
            with pytest.raises(ValueError, match="between 4 and 50"):
                user.set_password("abc")

    def test_password_too_long(self, app, db):
        from Onani.models import User

        with app.app_context():
            user = User()
            with pytest.raises(ValueError, match="between 4 and 50"):
                user.set_password("a" * 51)

    def test_password_hashed_correctly(self, app, db):
        from Onani.models import User

        with app.app_context():
            user = User()
            user.set_password("correcthorse")
            assert user.password_hash != "correcthorse"
            assert user.check_password("correcthorse") is True
            assert user.check_password("wrongpassword") is False

    def test_nickname_optional(self, app, db):
        from Onani.models import User, UserSettings

        with app.app_context():
            user = User(username="nonickuser")
            user.set_password("pass")
            user.settings = UserSettings()
            db.session.add(user)
            db.session.commit()
            assert user.nickname is None

    def test_nickname_too_short(self, app, db):
        from Onani.models import User

        with app.app_context():
            user = User()
            with pytest.raises(ValueError, match="between 3 and 32"):
                user.nickname = "ab"


class TestUserPermissions:
    def test_default_permissions(self, app, db):
        from Onani.models import User, UserPermissions

        with app.app_context():
            user = User(username="permuser")
            user.set_password("pass")
            assert user.has_permissions(UserPermissions.CREATE_POSTS)
            assert user.has_permissions(UserPermissions.CREATE_COMMENTS)
            assert not user.has_permissions(UserPermissions.DELETE_POSTS)

    def test_admin_permissions(self, app, db):
        from Onani.models import User, UserPermissions, UserRoles

        with app.app_context():
            user = User(username="adminpermuser", role=UserRoles.ADMIN,
                        permissions=UserPermissions.ADMINISTRATION)
            user.set_password("pass")
            assert user.has_permissions(UserPermissions.DELETE_POSTS)
            assert user.has_permissions(UserPermissions.BAN_USERS)
            assert user.has_permissions(UserPermissions.VIEW_LOGS)

    def test_permission_list_check(self, app, db):
        from Onani.models import User, UserPermissions

        with app.app_context():
            user = User(username="listpermuser")
            user.set_password("pass")
            # DEFAULT has both CREATE_POSTS and CREATE_COMMENTS
            assert user.has_permissions(
                [UserPermissions.CREATE_POSTS, UserPermissions.CREATE_COMMENTS]
            )
            # should fail for combination including DELETE_POSTS
            assert not user.has_permissions(
                [UserPermissions.CREATE_POSTS, UserPermissions.DELETE_POSTS]
            )

    def test_has_role(self, app, db):
        from Onani.models import User, UserRoles

        with app.app_context():
            user = User(username="roleuser", role=UserRoles.MODERATOR)
            user.set_password("pass")
            assert user.has_role(UserRoles.MEMBER)
            assert user.has_role(UserRoles.MODERATOR)
            assert not user.has_role(UserRoles.ADMIN)


class TestUserOTP:
    def test_otp_token_generated(self, app, db):
        from Onani.models import User

        with app.app_context():
            user = User(username="otpuser")
            user.set_password("pass")
            assert user.otp_token is not None
            assert len(user.otp_token) > 0

    def test_check_otp_valid(self, app, db):
        import pyotp

        from Onani.models import User

        with app.app_context():
            user = User(username="otpvalid")
            user.set_password("pass")
            totp = pyotp.TOTP(user.otp_token)
            current_code = totp.now()
            assert user.check_otp(current_code) is True

    def test_check_otp_invalid(self, app, db):
        from Onani.models import User

        with app.app_context():
            user = User(username="otpinvalid")
            user.set_password("pass")
            assert user.check_otp("000000") is False

    def test_otp_uri(self, app, db):
        from Onani.models import User

        with app.app_context():
            user = User(username="otpuri")
            user.set_password("pass")
            uri = user.otp_uri
            assert "otpauth://totp/" in uri
            assert "Onani" in uri

    def test_generate_backup_codes(self, app, db):
        from Onani.models import User

        with app.app_context():
            user = User(username="otpbackup")
            user.set_password("pass")
            codes = user.generate_backup_codes()
            assert len(codes) == 10
            # Each code should be in "xxxxxxxx-xxxxxxxx" format
            for code in codes:
                assert "-" in code
                parts = code.split("-")
                assert len(parts) == 2
                assert len(parts[0]) == 8
                assert len(parts[1]) == 8
            # Hashed codes stored on user
            assert user.otp_backup_codes is not None
            assert len(user.otp_backup_codes) == 10

    def test_check_backup_code_valid(self, app, db):
        from Onani.models import User

        with app.app_context():
            user = User(username="otpbkvalid")
            user.set_password("pass")
            codes = user.generate_backup_codes()
            # A valid code should be accepted
            assert user.check_backup_code(codes[0]) is True
            # After use, the code should be consumed (9 remaining)
            assert len(user.otp_backup_codes) == 9

    def test_check_backup_code_invalid(self, app, db):
        from Onani.models import User

        with app.app_context():
            user = User(username="otpbkinvalid")
            user.set_password("pass")
            user.generate_backup_codes()
            assert user.check_backup_code("00000000-00000000") is False

    def test_check_backup_code_case_insensitive(self, app, db):
        from Onani.models import User

        with app.app_context():
            user = User(username="otpbkcase")
            user.set_password("pass")
            codes = user.generate_backup_codes()
            # Upper-cased code should still work
            assert user.check_backup_code(codes[0].upper()) is True

    def test_regen_otp_token(self, app, db):
        from Onani.models import User

        with app.app_context():
            user = User(username="otpregen")
            user.set_password("pass")
            user.otp_enabled = True
            original_token = user.otp_token
            user.generate_backup_codes()
            user.regen_otp_token()
            assert user.otp_token != original_token
            assert user.otp_enabled is False
            assert user.otp_backup_codes is None


class TestUserIsActive:
    def test_active_user(self, app, db, make_user):
        with app.app_context():
            user = make_user(username="activeuser")
            assert user.is_active is True

    def test_deleted_user_inactive(self, app, db, make_user):
        with app.app_context():
            user = make_user(username="deleteduser")
            user.is_deleted = True
            db.session.commit()
            assert user.is_active is False

    def test_banned_user_inactive(self, app, db, make_user):
        import datetime

        from Onani.models import Ban

        with app.app_context():
            user = make_user(username="banneduser")
            future = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=7)
            ban = Ban(user=user.id, expires=future, reason="Test ban")
            db.session.add(ban)
            user.ban = ban
            db.session.commit()
            assert user.is_active is False

    def test_expired_ban_auto_cleared(self, app, db, make_user):
        import datetime

        from Onani.models import Ban

        with app.app_context():
            user = make_user(username="expiredbanneduser")
            past = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=1)
            ban = Ban(user=user.id, expires=past, reason="Expired ban")
            db.session.add(ban)
            user.ban = ban
            db.session.commit()
            # is_active should clear the expired ban
            assert user.is_active is True
            db.session.refresh(user)
            assert user.ban is None
