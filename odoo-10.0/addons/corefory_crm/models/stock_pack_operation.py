# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, tools, SUPERUSER_ID
from odoo.tools.translate import _
from odoo.tools import email_re, email_split
from odoo.exceptions import UserError, AccessError

from odoo.addons.base.res.res_partner import FormatAddress
from odoo.exceptions import UserError, ValidationError

class PackOperation(models.Model):

    _inherit = "stock.pack.operation"

    @api.onchange('pack_lot_ids')
    def _onchange_packlots(self):
        action_ctx = dict(self.env.context)
        stock_picking = self.env['stock.picking'].browse(action_ctx.get('default_picking_id'))

        if(stock_picking and stock_picking.picking_type_id.code == 'internal'):
            Quant = self.env['stock.quant']

            qty_done = 0
            for lot in self.pack_lot_ids:
                countries = Quant.sudo().read_group([('product_id', '=', self.product_id.id), ('lot_id', '=', lot.lot_id.id),
                                                     ('location_id', '=', action_ctx.get('default_location_id'))],
                                                    ["product_id", "location_id", "qty"],
                                                    groupby=['product_id', "location_id"], )

                available_quantity = sum(country_dict['qty'] for country_dict in countries)
                if (lot.qty > available_quantity):
                    lot.qty = available_quantity
                    raise ValidationError('Lot : ' + lot.lot_id.name + ' has available ' + str(available_quantity) + ' product(s)')
                    return False

                qty_done = qty_done + lot.qty

            self.qty_done = qty_done
        else:
            super(PackOperation, self)._onchange_packlots()
    @api.multi
    def save(self):
        action_ctx = dict(self.env.context)
        stock_picking = self.env['stock.picking'].browse(action_ctx.get('default_picking_id'))

        if (stock_picking and stock_picking.picking_type_id.code == 'internal'):
            Quant = self.env['stock.quant']

            for lot in self.pack_lot_ids:
                countries = Quant.sudo().read_group([('product_id', '=', self.product_id.id), ('lot_id', '=', lot.lot_id.id),
                                                     ('location_id', '=', action_ctx.get('default_location_id'))],
                                                    ["product_id", "location_id", "qty"],
                                                    groupby=['product_id', "location_id"], )

                available_quantity = sum(country_dict['qty'] for country_dict in countries)
                if (lot.qty > available_quantity):
                    raise ValidationError('Lot / Series : ' + lot.lot_id.name + ' has available ' + str(available_quantity) + ' product(s)')
                    return False

        super(PackOperation, self).save()