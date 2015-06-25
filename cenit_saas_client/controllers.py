# -*- coding: utf-8 -*-

import werkzeug

from openerp.http import request
from openerp.addons.auth_oauth.controllers import main as oauth


class SaasOAuthLogin (oauth.OAuthLogin):
    def list_providers(self):
        try:
            provider_obj = request.registry.get ('auth.oauth.provider')
            providers = provider_obj.search_read (
                request.cr, SUPERUSER_ID, [
                    ('enabled', '=', True),
                    ('auth_endpoint', '!=', False),
                    ('validation_endpoint', '!=', False)
                ]
            )
            # TODO in forwardport: remove conditions on 'auth_endpoint' and 'validation_endpoint' when these fields will be 'required' in model
        except Exception:
            providers = []

        for provider in providers:
            provider_return_url = provider.get ('return_url', False)
            if not provider_return_url:
                provider_return_url = 'auth_oauth/signin'

            provider_response_type = provider.get ('response_type', False)
            if not provider_response_type:
                provider_response_type = 'token'

            return_url = request.httprequest.url_root + provider_return_url
            state = self.get_state(provider)
            params = dict(
                debug=request.debug,
                response_type=provider_response_type,
                client_id=provider['client_id'],
                redirect_uri=return_url,
                scope=provider['scope'],
                state=simplejson.dumps(state),
            )
            provider['auth_link'] = provider['auth_endpoint'] + '?' + werkzeug.url_encode(params)

        return providers
