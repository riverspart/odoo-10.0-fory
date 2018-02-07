# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
import time

class PosOrder(models.Model):
    _inherit = 'pos.order'
    fory_has_return_point = fields.Boolean(string='Has Return Point?', default=False )

    fory_is_return_product = fields.Boolean(string="Is return?", default= False)
    card_id = fields.Many2one('corefory.loyalty.card',string='Loyalty Card',readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}, domain=[('state', '=', 'active')] )
    apply_loyalty_card = fields.Boolean(string='Apply loyalty card?', default=False, readonly=True,
                                        states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}, )

    state = fields.Selection(inverse="_update_loyalty_point")
    changed_point = fields.Float(string='Changed Points' ,readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},)
    changed_money = fields.Float(string='Changed Money', readonly=True,
                                    states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}, )
    added_point = fields.Float(string='Added Point', readonly=True,
                                states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}, )
    has_added_point = fields.Boolean(string='Has Added Point?', default=False,readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}, )

    added_money = fields.Float(string='Added Money', readonly=True,
                               states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}, )
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', readonly=True,
                                          help='Utility field to express amount currency')
    # amount_total = fields.Float(compute='_compute_amount_total', string='Total', digits=0)
    apply_coupon = fields.Boolean(string='Apply Coupon?', default=False, readonly=True,
                                  states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}, )

    coupon_code = fields.Char('Coupon Code', readonly=True,
                              states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
                              domain=[('state', '=', 'active')])
    coupon_id = fields.Many2one('corefory.coupon', string='Coupon', readonly=True,
                                states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
                                domain=[('state', '=', 'active')])
    coupon_discount_percentage = fields.Float('Coupon Discount Percentage')
    coupon_discount_percentage_amount = fields.Float('Coupon Discount Percentage')
    coupon_discount_fix = fields.Float('Coupon Discount Fix Price')

    @api.depends('statement_ids', 'lines.price_subtotal_incl', 'lines.discount')
    def _compute_amount_all(self):
        super(PosOrder, self)._compute_amount_all()
        for order in self:
            currency = order.pricelist_id.currency_id
            # amount_untaxed = currency.round(sum(line.price_subtotal for line in order.lines))
            # order.amount_total = order.amount_tax + amount_untaxed

            if(order.card_id):
                if(order.fory_is_return_product == False):
                    order.amount_total = order.amount_total - order.changed_money

            if (order.coupon_id):
                order.amount_total = order.amount_total - order.coupon_discount_percentage_amount - order.coupon_discount_fix

    @api.multi
    def _update_loyalty_point(self):
        for order in self:
            if order.state != 'paid' and order.state != 'invoiced'and order.state != 'done':
                continue

            # check had added point
            if(order.has_added_point == False):
                if(order.fory_is_return_product == False):
                    card = self.env['corefory.loyalty.card']._get_card(order.partner_id.id)
                else:
                    card = order.card_id

                if (order.fory_is_return_product == False):

                    if not card:
                        continue

                    is_converted, points = card.convert_amount_to_point(order.amount_total, card)

                    total_point = card.total_point
                    convertible_point = card.convertible_point
                    total_point += points
                    convertible_point += points
                    order.write({
                        'has_added_point' : True,
                        'added_point': points,
                        'added_money': order.amount_total,
                        'card_id' : card.id
                    })
                    if (is_converted):
                        history = {
                            'card_id': card.id,
                            'changed_point': points,
                            'user_id': self.env.uid,
                            'type': 'plus',
                            'origin': order.pos_reference,
                            'point_to_money': card.point_to_money,
                            'money_to_point': card.money_to_point
                        }

                        self.env['corefory.loyalty.card.history'].create(history)

                        history = {
                            'card_id': card.id,
                            'changed_point': order.changed_point,
                            'user_id': self.env.uid,
                            'type': 'minus',
                            'origin': order.pos_reference,
                            'point_to_money': card.point_to_money,
                            'money_to_point': card.money_to_point
                        }
                        convertible_point -= order.changed_point

                        self.env['corefory.loyalty.card.history'].create(history)
                        card.write({
                            'total_point': total_point,
                            'convertible_point': convertible_point
                        })
                # return point
                else:
                    if(order.fory_has_return_point == False):
                        total_return_amount = abs(order.amount_total)
                        card_change_history = self.env['corefory.loyalty.card.history'].sudo().search(
                            [('origin', '=', order.pos_reference), ('money_to_point', '>', 0)], limit=1);
                        if(len(card_change_history.ids)) :
                            is_converted, added_point = self.env['corefory.loyalty.card'].sudo().convert_amount_to_point_with_param(total_return_amount, card_change_history.money_to_point)

                            if(added_point >= order.added_point):
                                order.return_loyalty_point(order.changed_point, order.added_point)
                            else:
                                if (order.changed_point > 0):
                                    is_converted, changed_point = self.env['corefory.loyalty.card'].sudo().convert_amount_to_point_base_with_param(total_return_amount,
                                                                                                                card_change_history.point_to_money)
                                    if (changed_point >= order.changed_point):
                                        changed_point = order.changed_point
                                else:
                                    changed_point = 0.0

                                order.return_loyalty_point(changed_point, added_point)


    @api.multi
    def return_loyalty_point(self, return_changed_point , return_added_point):
        for order in self:
            if order.state != 'paid' and order.state != 'invoiced'and order.state != 'done':
                continue
            card = self.env['corefory.loyalty.card']._get_card(order.partner_id.id)
            if not card:
                continue
            # is_converted , points = card.convert_amount_to_point(order.amount_total)
            points = return_added_point
            total_point = card.total_point
            convertible_point = card.convertible_point
            total_point -= points
            convertible_point = convertible_point - return_added_point + return_changed_point

            history = {
                'card_id': card.id,
                'changed_point': +return_changed_point,
                'user_id': self.env.uid,
                'type': 'plus',
                'origin': order.pos_reference,
                'description': 'back '+ str(return_changed_point)
            }

            self.env['corefory.loyalty.card.history'].create(history)

            history = {
                'card_id': card.id,
                'changed_point': return_added_point,
                'user_id': self.env.uid,
                'type': 'minus',
                'origin': order.pos_reference,
                'description': 'return ' + str(return_added_point)
            }
            # convertible_point = convertible_point -return_added_point+return_changed_point

            self.env['corefory.loyalty.card.history'].create(history)
            card.update({
                'total_point' : total_point,
                'convertible_point' : convertible_point
            })

            order.update({
                'fory_has_return_point' : True
            })
    @api.model
    def _order_fields(self, ui_order):
        order_fields = super(PosOrder, self)._order_fields(ui_order)

        if(ui_order['loyalty_card']):
            order_fields['card_id'] = ui_order['loyalty_card']['id']
            order_fields['apply_loyalty_card'] = True
            order_fields['changed_point'] = ui_order['loyalty_card']['changed_point']
            order_fields['changed_money'] = ui_order['loyalty_card']['changed_money']


        if(ui_order['coupon']):
            order_fields['coupon_id'] = ui_order['coupon']['id']
            order_fields['apply_coupon'] = True
            order_fields['coupon_code'] = ui_order['coupon']['code']
            order_fields['coupon_discount_percentage'] = ui_order['coupon']['coupon_discount_percentage']
            order_fields['coupon_discount_percentage_amount'] = ui_order['coupon']['coupon_discount_percentage_amount']
            order_fields['coupon_discount_fix'] = ui_order['coupon']['coupon_discount_fix']

        return order_fields


    @api.multi
    def create(self, vals):
        res = super(PosOrder, self).create(vals)
        return res

    @api.multi
    def write(self, vals):
        res = super(PosOrder, self).write(vals)
        return res

    @api.multi
    def create_picking(self):
        super(PosOrder, self).create_picking()
        for order in self:
            picking_type = order.picking_type_id
            if picking_type:
                pos_qty = any([x.qty > 0 for x in order.lines if x.product_id.type in ['product', 'consu']])

                # for order picking
                if pos_qty:
                    order_picking = order.picking_id
                    if (order_picking.state == 'assigned'):
                        order_picking.do_new_transfer()
