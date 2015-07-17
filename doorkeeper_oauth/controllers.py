# -*- coding: utf-8 -*-
from xml.dom.expatbuilder import FragmentBuilder
import openerp
from openerp import SUPERUSER_ID
from openerp.addons.auth_oauth.controllers.main import fragment_to_query_string
from openerp.addons.web import http
from openerp.addons.web.controllers.main import db_monodb, ensure_db, set_cookie_and_redirect, login_and_redirect
from openerp.addons.web.controllers.main import Session
from openerp.addons.web.http import request
from openerp.modules.registry import RegistryManager
from openerp.tools import config, DEFAULT_SERVER_DATETIME_FORMAT

from datetime import datetime, timedelta

import werkzeug
import simplejson
import uuid
import random
import logging


_logger = logging.getLogger(__name__)

class DoorkeeperOauth (http.Controller):

    def __create_app_for_db (self, dbname):
        provider = self.get_provider ()
        client_id = provider.client_id

        request.registry['oauth.application'].create (
            request.cr, SUPERUSER_ID, {
                'client_id': client_id,
                'name': dbname
            }
        )

        return provider

    def __signup_user (self, provider, values):
        u = request.registry.get('res.users')
        credentials = u.auth_oauth (request.cr, SUPERUSER_ID, provider.id, values, context={})

        user = u.search_read (
            request.cr, SUPERUSER_ID, [
                ('login', '=', credentials[1])
            ]
        )[0]

        return user['oauth_uid'], credentials

    def __save_access_token(self, cr, uid, login, token, app_id, params):
        oat_pool = request.registry.get('oauth.access_token')
        if not oat_pool:
            return False

        user_pool = request.registry.get('res.users')
        user_id = user_pool.search(cr, uid, [('login', '=', login)])[0]

        expires_in = int(params.get('expires_in', '7200'))
        expires = datetime.now() + timedelta(seconds=expires_in)

        scope = params.get('scope', 'userinfo')

        candidates = oat_pool.search(cr, uid, [
            ('user_id', '=', user_id),
            ('application_id', '=', app_id)
        ])

        if candidates:
            oat_id = candidates[0]
            oat_pool.write(cr, uid, oat_id, {
                'scope': scope,
                'expires': expires.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                'token': token,
            })
        else:
            oat_id = oat_pool.create(cr, uid, {
                'user_id': user_id,
                'scope': scope,
                'expires': expires.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                'token': token,
                'application_id': app_id
            })
        cr.commit()

        return oat_id

    @http.route ('/auth_oauth/doorkeeper_cb', type='http', auth='none')
    @fragment_to_query_string
    def doorkeeper_cb (self, **kw):
        _logger.info("\n\nDOORKEEPER_CB args: %s\n", kw)
        if kw.get('state', False):
            state = simplejson.loads(kw['state'])

            master_db = db_monodb ()
            proto, root_url = request.httprequest.url_root.split ("://")
            if not master_db:
                return BadRequest()

            if state.get ('login', False):
                login = state['login']

                db_prefix = state['login'].split ('@')[0].replace(".", "_")
                if state.get ('demo', False):
                    db_prefix = "%s-%s" % (db_prefix, 'demo')

                dbname = "%s_%s" %(db_prefix, master_db)
                redirect = "%s://%s.%s" %(proto, db_prefix, root_url)
                if not redirect.endswith ("/"):
                    redirect += "/"
            else:
                url = "/web/login?oauth_error=2"
                return set_cookie_and_redirect(url)

            state.update ({'d': dbname})
            kw['state'] = simplejson.dumps (state)
            if openerp.service.db.exp_db_exist (dbname):
                registry = RegistryManager.get (dbname)

                with registry.cursor() as cr:
                    IMD = registry['ir.model.data']
                    try:
                        model, provider_id = IMD.get_object_reference(
                            cr, SUPERUSER_ID,
                            'cenit_saas_server', 'saas_oauth_provider'
                        )
                    except ValueError:
                        # LEGACY
                        try:
                            model, provider_id = IMD.get_object_reference(
                                cr, SUPERUSER_ID,
                                'saas_server', 'saas_oauth_provider'
                            )
                        except ValueError:
                            return set_cookie_and_redirect('/web?db=%s' % dbname)
                    assert model == 'auth.oauth.provider'

                    master_reg = RegistryManager.get(master_db)
                    master_cr = master_reg.cursor()
                    oapp_pool = master_reg.get('oauth.application')
                    uid = SUPERUSER_ID
                    if oapp_pool:
                        candidates = oapp_pool.search(master_cr, uid, [('name', '=', dbname)])
                        if candidates:
                            app_id = candidates[0]
                            self.__save_access_token(
                                master_cr, SUPERUSER_ID,
                                login, kw['access_token'], app_id, kw
                            )

                params = {
                    'access_token': kw['access_token'],
                    'expires_in': kw.get('expires_in', '7200'),
                    'scope': kw.get('scope', 'userinfo'),
                    'state': simplejson.dumps({
                        'd': dbname,
                        'p': provider_id,
                        }),
                    }

                return werkzeug.utils.redirect('{host}{controller}?{params}'.format(
                        host = redirect,
                        controller = 'auth_oauth/signin',
                        params = werkzeug.url_encode(params)
                    )
                )
            else:
                registry = RegistryManager.get (master_db)

                if not state.get ('name', False):
                    state.update ({
                        'name': db_prefix.capitalize ()
                    })

                if not state.get ('organization', False):
                    state.update ({
                        'organization': db_prefix.capitalize ()
                    })

                if state.get ('demo', False):
                    plan = self.get_demo_plan ()
                else:
                    if state.get ('plan', False):
                        plan = self.get_plan (state.get ('plan'))
                    else:
                        plan = self.get_default_plan ()
                state.update ({
                    'db_template': plan['template'],
                    'plan': plan['id']
                })

                kw['state'] = simplejson.dumps (state)
                if not kw.get('scope', False):
                    kw['scope'] = 'userinfo'
                try:
                    provider = self.__create_app_for_db (state['d'])
                    partner_id, credentials = self.__signup_user (provider, kw)
                    request.cr.commit ()

                except Exception, e:
                    _logger.exception (e)
                    url = "/web/login?oauth_error=2"
                    return set_cookie_and_redirect (url)

                oapp_pool = registry.get('oauth.application')
                cr = registry.cursor()
                uid = SUPERUSER_ID
                if oapp_pool:
                    candidates = oapp_pool.search(cr, uid,
                                                  [('name', '=', dbname)])
                    if candidates:
                        app_id = candidates[0]
                        self.__save_access_token(
                            cr, SUPERUSER_ID,
                            login, kw['access_token'], app_id, kw
                        )

                url = "/saas_server/new_database"
                kw['admin_data'] = simplejson.dumps ({
                    'user_id': partner_id,
                    'client_id': provider.client_id,
                    'email': login,
                    'name': state['name']
                })

                full_url = '%s?%s' % (url, werkzeug.url_encode(kw))
                return login_and_redirect (*credentials, redirect_url=full_url)
        else:
            _logger.exception ('OAuth2: No state provided.')
            url = "/web/login?oauth_error=2"

        return set_cookie_and_redirect(url)

    def get_provider(self):
        imd = request.registry['ir.model.data']
        return imd.xmlid_to_object (
            request.cr, SUPERUSER_ID,
            'cenit_saas_server.saas_oauth_provider'
        )

    def get_demo_plan (self):
        icp = request.registry.get ('ir.config_parameter')
        name = icp.get_param (
            request.cr, SUPERUSER_ID, "cenit.plan.demo", default=None
        )
        ssp = request.registry.get ('saas_server.plan')
        conditions = [
            ('state', '=', 'confirmed'),
            ('template', '=', name)
        ]

        plans = ssp.search_read (
            request.cr, SUPERUSER_ID, conditions
        )

        return plans[0]

    def get_default_plan (self):
        icp = request.registry.get ('ir.config_parameter')
        name = icp.get_param (
            request.cr, SUPERUSER_ID, "cenit.plan.default", default=None
        )
        ssp = request.registry.get ('saas_server.plan')
        conditions = [
            ('state', '=', 'confirmed'),
            ('template', '=', name)
        ]

        plans = ssp.search_read (
            request.cr, SUPERUSER_ID, conditions
        )

        return plans[0]

    def get_plan (self, name=None):
        ssp = request.registry['saas_server.plan']
        conditions = [
            ('state', '=', 'confirmed'),
        ]
        if name is not None:
            conditions.append (('name', '=', name))

        plans = ssp.search_read (
            request.cr, SUPERUSER_ID, conditions
        )

        if name is not None:
            assert len(plans) == 1
        else:
            assert len(plans) > 0

        return plans[0]


class SessionController (Session):

    @http.route('/web/session/logout', type='http', auth="none")
    def logout(self, redirect='/web'):
        icp = request.registry.get ('ir.config_parameter')
        redirect_url = icp.get_param (request.cr, SUPERUSER_ID, 'web.logout.redirect')

        redirect = redirect_url if redirect_url else redirect

        return super(SessionController, self).logout (redirect)
