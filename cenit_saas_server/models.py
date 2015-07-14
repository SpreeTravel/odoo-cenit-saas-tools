import openerp
from openerp import models
from openerp.addons.saas_utils import connector


class CenitSaasServerPlan(models.Model):
    _name = "saas_server.plan"
    _inherit = 'saas_server.plan'

    def create_template(self, cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids[0])
        openerp.service.db.exp_create_database(obj.template, obj.demo,
                                               obj.lang.code)
        addon_names = [x.name for x in obj.required_addons_ids]
        if 'cenit_saas_client' not in addon_names:
            addon_names.append('cenit_saas_client')
        to_search = [('name', 'in', addon_names)]
        addon_ids = connector.call(obj.template, 'ir.module.module',
                                   'search', to_search)
        for addon_id in addon_ids:
            connector.call(obj.template, 'ir.module.module',
                           'button_immediate_install', addon_id)
        return self.write(cr, uid, obj.id, {'state': 'confirmed'})
