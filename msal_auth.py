from msal import ConfidentialClientApplication

MS_AUTH_URL = 'https://login.microsoftonline.com'
IMAP_SCOPE = 'https://outlook.office.com/IMAP.AccessAsUser.All'


class MSAuthException(Exception):
    pass


def get_msal_access_token(app_id, app_secret, tenant_id, username, password):
    """
    Author: Anton Kolobov
    Description: function for obtaining a Microsoft access token
    """
    client_app = ConfidentialClientApplication(
        client_id=app_id,
        client_credential=app_secret,
        authority=f'{MS_AUTH_URL}/{tenant_id}',
    )
    aad_payload = client_app.acquire_token_by_username_password(username, password, [IMAP_SCOPE])
    if 'access_token' not in aad_payload.keys():
        if 'error_description' in aad_payload.keys():
            message = aad_payload['error_description']
        else:
            message = 'Access token can\'t be found in request payload.'
        raise MSAuthException(message)
    return aad_payload['access_token']
