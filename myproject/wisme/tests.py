from django.test import TestCase, override_settings
from django.urls import reverse
from django.core import mail
from allauth.account.models import EmailAddress
from wisme.models import CustomUser, Page, Chapter, SearchedWord
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


# --- 004 単語帳機能 ---

def make_word(owner, word="apple", meaning="りんご", note=None):
    return SearchedWord.objects.create(owner=owner, word=word, meaning=meaning, note=note)


# DoD: /wisme/words/ に単語一覧が表示される（ログイン必須）
class WordListAccessTest(TestCase):
    def setUp(self):
        self.user = make_verified_user('wl@example.com', 'Testpass123!')

    def test_word_list_accessible_when_logged_in(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('wisme:word_list'))
        self.assertEqual(response.status_code, 200)

    def test_word_list_redirects_when_not_logged_in(self):
        response = self.client.get(reverse('wisme:word_list'))
        self.assertRedirects(response, '/accounts/login/?next=/wisme/words/', fetch_redirect_response=False)


# DoD: 他のユーザーの単語が表示されない
class WordListOwnerFilterTest(TestCase):
    def setUp(self):
        self.user1 = make_verified_user('wl1@example.com', 'Testpass123!')
        self.user2 = make_verified_user('wl2@example.com', 'Testpass123!')
        make_word(self.user1, word='hello')
        make_word(self.user2, word='world')

    def test_shows_only_own_words(self):
        self.client.force_login(self.user1)
        response = self.client.get(reverse('wisme:word_list'))
        words = response.context['words']
        self.assertEqual(words.count(), 1)
        self.assertEqual(words.first().word, 'hello')


# DoD: アルファベット順ソートに切り替えられる
class WordListSortTest(TestCase):
    def setUp(self):
        self.user = make_verified_user('wls@example.com', 'Testpass123!')
        make_word(self.user, word='zebra')
        make_word(self.user, word='apple')
        make_word(self.user, word='mango')

    def test_default_sort_by_created_at_desc(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('wisme:word_list'))
        words = list(response.context['words'])
        self.assertEqual(words[0].word, 'mango')

    def test_alpha_sort(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('wisme:word_list') + '?sort=alpha')
        words = list(response.context['words'])
        self.assertEqual(words[0].word, 'apple')


# --- 012 章単位メモ機能 ---

def _chapter_formset_post(prefix='chapters', initial=0, total=1, chapters=None):
    """ChapterFormSet の POST データを生成するヘルパー"""
    data = {
        f'{prefix}-TOTAL_FORMS': str(total),
        f'{prefix}-INITIAL_FORMS': str(initial),
        f'{prefix}-MIN_NUM_FORMS': '0',
        f'{prefix}-MAX_NUM_FORMS': '1000',
    }
    for i, c in enumerate(chapters or []):
        data[f'{prefix}-{i}-title'] = c.get('title', '')
        data[f'{prefix}-{i}-content'] = c.get('content', '')
        data[f'{prefix}-{i}-order'] = c.get('order', i)
        if 'id' in c:
            data[f'{prefix}-{i}-id'] = c['id']
        if c.get('DELETE'):
            data[f'{prefix}-{i}-DELETE'] = 'on'
    return data


# DoD: Chapter は Page との FK 関係と related_name='chapters' を持ち、order 順に取得できる
class ChapterModelTest(TestCase):
    def setUp(self):
        self.user = make_verified_user('ch-model@example.com', 'Testpass123!')
        self.page = make_page(self.user, title='本A')

    def test_chapters_related_name(self):
        Chapter.objects.create(page=self.page, order=1, title='第2章', content='b')
        Chapter.objects.create(page=self.page, order=0, title='第1章', content='a')
        chapters = list(self.page.chapters.all())
        self.assertEqual(len(chapters), 2)
        self.assertEqual(chapters[0].title, '第1章')
        self.assertEqual(chapters[1].title, '第2章')

    def test_cascade_delete_removes_chapters(self):
        Chapter.objects.create(page=self.page, order=0, content='x')
        self.assertEqual(Chapter.objects.count(), 1)
        self.page.delete()
        self.assertEqual(Chapter.objects.count(), 0)


# DoD: 新規作成時に Page と章を同時保存できる
class PageCreateWithChaptersTest(TestCase):
    def setUp(self):
        self.user = make_verified_user('ch-create@example.com', 'Testpass123!')
        self.client.force_login(self.user)

    def test_create_page_with_two_chapters(self):
        data = {
            'title': 'テスト本',
            'thoughts': '全体の感想',
            'page_date': '2026-04-19',
        }
        data.update(_chapter_formset_post(
            total=2, initial=0,
            chapters=[
                {'title': '序章', 'content': '始まり'},
                {'title': '終章', 'content': '終わり'},
            ],
        ))
        response = self.client.post(reverse('wisme:page_create'), data)
        self.assertEqual(response.status_code, 302)
        page = Page.objects.get(owner=self.user, title='テスト本')
        chapters = list(page.chapters.all())
        self.assertEqual(len(chapters), 2)
        self.assertEqual(chapters[0].order, 0)
        self.assertEqual(chapters[0].title, '序章')
        self.assertEqual(chapters[1].order, 1)
        self.assertEqual(chapters[1].title, '終章')

    def test_create_page_without_chapters_still_works(self):
        data = {
            'title': '章なし本',
            'thoughts': '',
            'page_date': '2026-04-19',
        }
        data.update(_chapter_formset_post(total=1, initial=0, chapters=[{}]))
        response = self.client.post(reverse('wisme:page_create'), data)
        self.assertEqual(response.status_code, 302)
        page = Page.objects.get(owner=self.user, title='章なし本')
        self.assertEqual(page.chapters.count(), 0)


# DoD: 編集時に既存章の更新・削除・新規章の追加ができる
class PageUpdateWithChaptersTest(TestCase):
    def setUp(self):
        self.user = make_verified_user('ch-upd@example.com', 'Testpass123!')
        self.client.force_login(self.user)
        self.page = make_page(self.user, title='旧タイトル')
        self.c1 = Chapter.objects.create(page=self.page, order=0, title='旧1章', content='旧1')
        self.c2 = Chapter.objects.create(page=self.page, order=1, title='旧2章', content='旧2')

    def test_update_existing_chapter_and_delete_one_and_add_new(self):
        data = {
            'title': '新タイトル',
            'thoughts': '',
            'page_date': '2026-04-19',
        }
        data.update(_chapter_formset_post(
            total=3, initial=2,
            chapters=[
                {'id': str(self.c1.id), 'title': '更新1章', 'content': '更新1'},
                {'id': str(self.c2.id), 'title': '旧2章', 'content': '旧2', 'DELETE': True},
                {'title': '新3章', 'content': '新3'},
            ],
        ))
        response = self.client.post(reverse('wisme:page_update', args=[self.page.id]), data)
        self.assertEqual(response.status_code, 302)

        self.page.refresh_from_db()
        self.assertEqual(self.page.title, '新タイトル')

        chapters = list(self.page.chapters.all())
        self.assertEqual(len(chapters), 2)
        titles = [c.title for c in chapters]
        self.assertIn('更新1章', titles)
        self.assertIn('新3章', titles)
        self.assertNotIn('旧2章', titles)


# DoD: page_detail で chapters コンテキストが提供される
class PageDetailChaptersContextTest(TestCase):
    def setUp(self):
        self.user = make_verified_user('ch-det@example.com', 'Testpass123!')
        self.client.force_login(self.user)
        self.page = make_page(self.user)
        Chapter.objects.create(page=self.page, order=0, title='章A', content='a')

    def test_chapters_in_context(self):
        response = self.client.get(reverse('wisme:page_detail', args=[self.page.id]))
        self.assertEqual(response.status_code, 200)
        self.assertIn('chapters', response.context)
        self.assertEqual(list(response.context['chapters'])[0].title, '章A')
