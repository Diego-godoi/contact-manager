from pytest import mark

from app.services.email_service import EmailService


@mark.asyncio
class TestEmailServiceSendPasswordResetEmail:
    async def test_send_email_successfully(self, mocker, create_users):
        token = 'token_example_123'

        user = create_users(count=1)[0]
        mock_fm = mocker.AsyncMock()

        await EmailService(mail_engine=mock_fm).send_password_reset_email(user, token)

        mock_fm.send_message.assert_called_once()

        args, kwargs = mock_fm.send_message.call_args
        message = args[0]

        assert message.subject.startswith('Reset Password')
        assert message.recipients[0].email == user.email
        assert token in message.template_body['activate_url']
        assert kwargs['template_name'] == 'user/password-reset.html'
