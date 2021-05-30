from rest_framework.test import APIClient
from testing.testcases import TestCase
from accounts.models import UserProfile


LOGIN_URL = '/api/accounts/login/'
LOGOUT_URL = '/api/accounts/logout/'
SIGNUP_URL = '/api/accounts/signup/'
LOGIN_STATUS_URL = '/api/accounts/login_status/'


class AccountApiTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = self.create_user(
            username='admin',
            email='admin@gmail.com',
            password='correct password',
        )

    def test_login(self):
        # login fail, as should be POST, not GET
        response = self.client.get(LOGIN_URL, {
            'username': self.user.username,
            'password': 'test password'
        })
        # 405 = METHOD_NOT_ALLOWED
        self.assertEqual(response.status_code, 405)

        # POST, login fail, while wrong password
        response = self.client.post(LOGIN_URL, {
            'username': self.user.username,
            'password': 'test password'
        })
        self.assertEqual(response.status_code, 400)

        # test login_status as False
        response = self.client.get(LOGIN_STATUS_URL)
        self.assertEqual(response.data['has_logged_in'], False)

        # with correct password, login success
        response = self.client.post(LOGIN_URL, {
            'username': self.user.username,
            'password': 'correct password'
        })
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(response.data['user'], None)
        self.assertEqual(response.data['user']['email'], 'admin@gmail.com')

        # check user profile has been created, but is None
        created_user_id = response.data['user']['id']
        profile = UserProfile.objects.filter(user_id=created_user_id).first()
        self.assertEqual(profile, None)

        # login status as True
        response = self.client.get(LOGIN_STATUS_URL)
        self.assertEqual(response.data['has_logged_in'], True)

    def test_logout(self):
        # login
        self.client.post(LOGIN_URL, {
            'username': self.user.username,
            'password': 'correct password'
        })

        # test user has already logged in
        response = self.client.get(LOGIN_STATUS_URL)
        self.assertEqual(response.data['has_logged_in'], True)

        # test logout must use method POST, not GET
        response = self.client.get(LOGOUT_URL)
        self.assertEqual(response.status_code, 405)

        # logout successfully with method POST
        response = self.client.post(LOGOUT_URL)
        self.assertEqual(response.status_code, 200)

        # test user has already logged out
        response = self.client.get(LOGIN_STATUS_URL)
        self.assertEqual(response.data['has_logged_in'], False)

    def test_signup(self):
        data = {
            'username': 'someone',
            'email': 'someone@gmail.com',
            'password': 'any password',
        }

        # test signup fail with method GET
        response = self.client.get(SIGNUP_URL)
        self.assertEqual(response.status_code, 405)

        # test with wrong email
        response = self.client.post(SIGNUP_URL, {
            'username': 'someone',
            'email': 'someone@com',
            'password': 'any password',
        })
        self.assertEqual(response.status_code, 400)

        # test with too short password
        response = self.client.post(SIGNUP_URL, {
            'username': 'someone',
            'email': 'someone@com',
            'password': 'any password',
        })
        self.assertEqual(response.status_code, 400)

        # test with too long username
        response = self.client.post(SIGNUP_URL, {
            'username': 'someonesomeonesomeonesomeonesomeonesomeone',
            'email': 'someone@gmail.com',
            'password': 'any password',
        })
        self.assertEqual(response.status_code, 400)

        # test with signup successfully
        response = self.client.post(SIGNUP_URL, data)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['user']['username'], 'someone')
        # test login_status as True
        response = self.client.get(LOGIN_STATUS_URL)
        self.assertEqual(response.data['has_logged_in'], True)
