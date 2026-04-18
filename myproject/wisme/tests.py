from django.test import TestCase, override_settings
from django.urls import reverse
from django.core import mail
from allauth.account.models import EmailAddress
from wisme.models import CustomUser, Page
import datetime


def make_verified_user(email, password):
    user = CustomUser.objects.create_user(username=email, email=email, password=password)
    EmailAddress.objects.create(user=user, email=email, primary=True, verified=True)
    return user


def make_page(owner, title="テストページ"):
    return Page.objects.create(
        owner=owner,
        title=title,
        thoughts="",
        page_date=datetime.date.today(),
    )


# DoD: メールアドレスとパスワードで新規登録できる
class SignupTest(TestCase):
    @override_settings(ACCOUNT_EMAIL_VERIFICATION='none')
    def test_signup_creates_user(self):
        self.client.post(reverse('account_signup'), {
            'email': 'new@example.com',
            'password1': 'Testpass123!',
            'password2': 'Testpass123!',
        })
        self.assertTrue(CustomUser.objects.filter(email='new@example.com').exists())


# DoD: 登録後、確認メールが送信される
class EmailVerificationTest(TestCase):
    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_signup_sends_verification_email(self):
        self.client.post(reverse('account_signup'), {
            'email': 'verify@example.com',
            'password1': 'Testpass123!',
            'password2': 'Testpass123!',
        })
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('verify@example.com', mail.outbox[0].to)


# DoD: メールアドレスとパスワードでログインできる
class LoginTest(TestCase):
    def setUp(self):
        self.user = make_verified_user('login@example.com', 'Testpass123!')

    def test_login_with_email_and_password(self):
        response = self.client.post(reverse('account_login'), {
            'login': 'login@example.com',
            'password': 'Testpass123!',
        })
        self.assertRedirects(response, '/wisme/', fetch_redirect_response=False)


# DoD: ログアウトできる
class LogoutTest(TestCase):
    def setUp(self):
        self.user = make_verified_user('logout@example.com', 'Testpass123!')
        self.client.force_login(self.user)

    def test_logout(self):
        response = self.client.post(reverse('account_logout'))
        self.assertRedirects(response, '/wisme/', fetch_redirect_response=False)


# DoD: 未ログイン状態でリダイレクトされる
class UnauthenticatedRedirectTest(TestCase):
    def test_index_redirects_to_login(self):
        response = self.client.get(reverse('wisme:index'))
        self.assertRedirects(response, '/accounts/login/?next=/wisme/', fetch_redirect_response=False)

    def test_page_list_redirects_to_login(self):
        response = self.client.get(reverse('wisme:page_list'))
        self.assertRedirects(response, '/accounts/login/?next=/wisme/page/list/', fetch_redirect_response=False)

    def test_page_create_redirects_to_login(self):
        response = self.client.get(reverse('wisme:page_create'))
        self.assertRedirects(response, '/accounts/login/?next=/wisme/page/create/', fetch_redirect_response=False)


# DoD: ログイン後は自分のメモのみ一覧に表示される
class OwnerFilterTest(TestCase):
    def setUp(self):
        self.user1 = make_verified_user('user1@example.com', 'Testpass123!')
        self.user2 = make_verified_user('user2@example.com', 'Testpass123!')
        make_page(self.user1, title='user1のページ')
        make_page(self.user2, title='user2のページ')

    def test_list_shows_only_own_pages(self):
        self.client.force_login(self.user1)
        response = self.client.get(reverse('wisme:page_list'))
        page_list = response.context['page_list']
        self.assertEqual(page_list.count(), 1)
        self.assertEqual(page_list.first().title, 'user1のページ')


# DoD: 他ユーザーのUUIDを直接指定してもアクセスできない（404）
class OtherUserPageAccessTest(TestCase):
    def setUp(self):
        self.user1 = make_verified_user('user1@example.com', 'Testpass123!')
        self.user2 = make_verified_user('user2@example.com', 'Testpass123!')
        self.user2_page = make_page(self.user2, title='user2のページ')

    def test_detail_returns_404_for_other_users_page(self):
        self.client.force_login(self.user1)
        response = self.client.get(reverse('wisme:page_detail', kwargs={'id': self.user2_page.id}))
        self.assertEqual(response.status_code, 404)

    def test_update_returns_404_for_other_users_page(self):
        self.client.force_login(self.user1)
        response = self.client.get(reverse('wisme:page_update', kwargs={'id': self.user2_page.id}))
        self.assertEqual(response.status_code, 404)

    def test_delete_returns_404_for_other_users_page(self):
        self.client.force_login(self.user1)
        response = self.client.get(reverse('wisme:page_delete', kwargs={'id': self.user2_page.id}))
        self.assertEqual(response.status_code, 404)


# DoD: CSRFトークンがログインフォームに含まれている
class CSRFTest(TestCase):
    def test_login_form_contains_csrf_token(self):
        response = self.client.get(reverse('account_login'))
        self.assertContains(response, 'csrfmiddlewaretoken')


# --- 003 ユーザープロフィール ---

# DoD: プロフィール画面にアクセスできる（ログイン必須）
class ProfileViewTest(TestCase):
    def setUp(self):
        self.user = make_verified_user('profile@example.com', 'Testpass123!')

    def test_profile_accessible_when_logged_in(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('wisme:profile'))
        self.assertEqual(response.status_code, 200)

    def test_profile_redirects_when_not_logged_in(self):
        response = self.client.get(reverse('wisme:profile'))
        self.assertRedirects(response, '/accounts/login/?next=/wisme/profile/', fetch_redirect_response=False)


# DoD: 表示名を変更して保存できる
class ProfileUpdateTest(TestCase):
    def setUp(self):
        self.user = make_verified_user('update@example.com', 'Testpass123!')
        self.client.force_login(self.user)

    def test_update_display_name(self):
        self.client.post(reverse('wisme:profile_update'), {'display_name': '新しい名前', 'profile_image': ''})
        self.user.refresh_from_db()
        self.assertEqual(self.user.display_name, '新しい名前')

    def test_update_redirects_to_profile(self):
        response = self.client.post(reverse('wisme:profile_update'), {'display_name': 'テスト', 'profile_image': ''})
        self.assertRedirects(response, reverse('wisme:profile'), fetch_redirect_response=False)


# DoD: 未ログインでプロフィール更新画面にアクセスするとリダイレクト
class ProfileUpdateUnauthTest(TestCase):
    def test_profile_update_redirects_when_not_logged_in(self):
        response = self.client.get(reverse('wisme:profile_update'))
        self.assertRedirects(response, '/accounts/login/?next=/wisme/profile/update/', fetch_redirect_response=False)


# DoD: 他ユーザーのプロフィールを直接URL操作で編集できない
class ProfileOtherUserTest(TestCase):
    def setUp(self):
        self.user1 = make_verified_user('u1@example.com', 'Testpass123!')
        self.user2 = make_verified_user('u2@example.com', 'Testpass123!')

    def test_update_only_affects_own_profile(self):
        self.client.force_login(self.user1)
        self.client.post(reverse('wisme:profile_update'), {'display_name': 'ハッカー', 'profile_image': ''})
        self.user2.refresh_from_db()
        self.assertNotEqual(self.user2.display_name, 'ハッカー')
