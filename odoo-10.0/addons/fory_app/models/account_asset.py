from odoo import api, fields, models, _


class AccountAssetAsset(models.Model):
    _inherit = 'account.asset.asset'

    code = fields.Char(string='Reference', size=32, readonly=True, required=True, states={'draft': [('readonly', False)]})

    @api.multi
    def copy(self, default=None):  # pylint: disable=W0622

        if not default:
            default = {}

        default['code'] = self.code and\
            self.code + ' (copy)' or False

        return super(AccountAssetAsset, self).copy(default=default)

    _sql_constraints = [
        ('code_unique', 'unique (code)', 'The code of Asset must be unique !'),
    ]
