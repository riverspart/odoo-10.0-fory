# -*- coding: utf-8 -*-
##############################################################################
#
# OdooBro - odoobro.contact@gmail.com
#
##############################################################################
from __builtin__ import super

from odoo import api, fields, models
import odoo.addons.decimal_precision as dp
from odoo.tools.translate import _


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    card_id = fields.Many2one('corefory.loyalty.card',string='Loyalty Card',readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}, domain=[('state', '=', 'active')] )
    apply_loyalty_card = fields.Boolean(string='Apply loyalty card?', default=False, readonly=True,
                                        states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}, )

    state = fields.Selection(inverse="_update_loyalty_point")
    changed_point = fields.Float(string='Changed Points' ,readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},)
    changed_money = fields.Monetary(string='Changed Money', readonly=True,
                                    states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}, )
    added_point = fields.Float(string='Added Point', readonly=True,
                                states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}, )
    added_money = fields.Monetary(string='Added Money', readonly=True,
                               states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}, )

    pos_store_id = fields.Many2one('pos.config', string='Store')

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
    @api.onchange('apply_coupon')
    def onchange_apply_coupon(self):
        for order in self:
            if(not order.apply_coupon):
                order.coupon_code = ''
                order.coupon_id = None
                order.coupon_discount_percentage = 0.0
                order.coupon_discount_fix = 0.0
                order.coupon_discount_percentage_amount = 0.0

    @api.onchange('coupon_code')
    def onchange_coupon_code(self):

        def reset(order):
            order.coupon_code = ''
            order.coupon_id = None
            order.coupon_discount_percentage = 0.0
            order.coupon_discount_percentage_amount = 0.0
            order.coupon_discount_fix = 0.0

        if(self.apply_coupon):
            Coupon_object = self.env['corefory.coupon']
            coupon = Coupon_object.get_coupon([('code', '=', self.coupon_code)])
            if(coupon.can_use):
                amount_all = self.compute_amount_all_base()
                if(amount_all['amount_total'] < coupon.total_amount_can_apply):
                    reset(self)
                    return {
                        'warning': {
                            'title': _('Invalid Coupon code'),
                            'message': _("Total amount is less than " + str(coupon.total_amount_can_apply))
                        }
                    }
                if(not self.partner_id):
                    reset(self)
                    return {
                        'warning': {
                            'title': _('Invalid Coupon code'),
                            'message': _("Please choose Customer")
                        }
                    }

                if(coupon.compute_number_of_use_each_customer(self.partner_id.id) >= coupon.number_order_for_each_customer):
                    reset(self)
                    return {
                        'warning': {
                            'title': _('Invalid Coupon code'),
                            'message': _("This customer has used maximum code")
                        }
                    }
                # check Number product can apply?
                number_product_can_apply = 0
                if (coupon.applied_on == '3_global'):
                    number_product_can_apply = len(self.order_line.ids)
                elif (coupon.applied_on == '2_product_category' or coupon.applied_on == '1_product'):
                    number_product_can_apply = 0
                for line in self.order_line:
                    if (coupon.applied_on == '2_product_category'):
                        if (line.product_id.categ_id.id == coupon.categ_id.id):
                            number_product_can_apply += 1
                    elif (coupon.applied_on == '1_product'):
                        if (line.product_id.id in coupon.product_ids.ids):
                            number_product_can_apply += 1

                if (coupon.number_product_can_apply > number_product_can_apply):
                    reset(self)
                    return {
                        'warning': {
                            'title': _('Invalid Coupon code'),
                            'message': _("You order less than "+ str(coupon.number_product_can_apply ) + " product(s)")
                        }
                    }

                # end check Number product can apply?

                # Create SO line
                if(len(coupon.gifts.ids) > 0):
                    order_lines = []
                    product_id_lines = []
                    # existing order line
                    for line in self.order_line:
                        product_id_lines.append(line.product_id.id)
                        order_lines.append((0, 0, {
                            'analytic_tag_ids': line.analytic_tag_ids.ids,
                            'currency_id': line.currency_id.id,
                            'customer_lead': line.customer_lead,
                            'discount': line.discount,
                            'invoice_lines': line.invoice_lines.ids,
                            'invoice_status': line.invoice_status,
                            'layout_category_id': line.layout_category_id,
                            'name': line.name,
                            'price_subtotal' : line.price_subtotal,
                            'price_tax': line.price_tax,
                            'price_unit':line.price_unit,
                            'price_total': line.price_total,
                            'procurement_ids':line.procurement_ids.ids,
                            'product_id' : line.product_id.id,
                            'product_packaging': line.product_packaging,
                            'product_qty': line.product_qty,
                            'product_tmpl_id': line.product_tmpl_id.id,
                            'product_uom': line.product_uom.id,
                            'product_uom_qty': line.product_uom_qty,
                            'qty_delivered':line.qty_delivered,
                            'qty_delivered_updateable': line.qty_delivered_updateable,
                            'qty_invoiced': line.qty_invoiced,
                            'qty_to_invoice': line.qty_to_invoice,
                            'route_id' : line.route_id,
                            'sequence': line.sequence,
                            'state': line.state,
                            'tax_id': line.tax_id.ids
                        }))

                    # order_lines.append((6, 0, self.order_line.ids))
                    # gift
                    for gift in coupon.gifts:
                        if(gift.id not in product_id_lines):
                            order_lines.append((0, 0, {
                                'product_id': gift.id,
                                'price_unit': 0.00,
                                'product_uom':  gift.uom_id.id,
                                'product_uom_qty': 1.0,
                                'name': 'Gift for you',
                            }))

                    self.order_line = order_lines

                self._amount_all()
            else:
                reset(self)
                return {'warning': {
                    'title': _('Invalid Coupon code'),
                    'message': _("You had inputted invalid coupon code. Please check start date, end date, golden hour and the number of orders which had been used this coupon code.")
                    }
                }
        else:
            reset(self)
            # self.coupon_code = ''
            # self.coupon_id = None
            # self.coupon_discount_percentage = 0.0
            # self.coupon_discount_percentage_amount = 0.0
            # self.coupon_discount_fix = 0.0

    @api.onchange('apply_loyalty_card')
    def onchange_apply_loyalty_card(self):
        for order in self:
            if(order.apply_loyalty_card):
                card = self.env['corefory.loyalty.card']._get_card(order.partner_id.id)
                if not card:
                    order.card_id = None
                    order.apply_loyalty_card = False
                    return {
                        'warning': {
                            'title': 'Invalid value',
                            'message': _('This customer have not Loyal Card yet Or Their cards are not activated')
                        }
                    }
                else:
                    order.card_id = card.id
            else:
                order.changed_point = 0
                order.changed_money = 0
                order.card_id = None

    @api.multi
    def return_loyalty_point(self, return_changed_point , return_added_point):
        for order in self:
            if order.state != 'done':
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
                'order_id': order.id,
                'origin': order.name,
                'description': 'back '+ str(return_changed_point)
            }

            self.env['corefory.loyalty.card.history'].create(history)

            history = {
                'card_id': card.id,
                'changed_point': return_added_point,
                'user_id': self.env.uid,
                'type': 'minus',
                'order_id': order.id,
                'origin': order.name,
                'description': 'return ' + str(return_added_point)
            }
            # convertible_point = convertible_point -return_added_point+return_changed_point

            self.env['corefory.loyalty.card.history'].create(history)
            card.update({
                'total_point' : total_point,
                'convertible_point' : convertible_point
            })

    @api.multi
    def _update_loyalty_point(self):
        for order in self:
            if order.state != 'done':
                continue
            card = self.env['corefory.loyalty.card']._get_card(order.partner_id.id)
            if not card:
                continue
            is_converted, points = card.convert_amount_to_point(order.amount_total,card)

            total_point = card.total_point
            convertible_point = card.convertible_point
            total_point += points
            convertible_point += points
            order.update({
                'added_point' : points,
                'added_money' : order.amount_total
            })
            if (is_converted):
                history = {
                    'card_id': card.id,
                    'changed_point': points,
                    'user_id': self.env.uid,
                    'type': 'plus',
                    'order_id': order.id,
                    'origin' : order.name,
                    'point_to_money': card.point_to_money,
                    'money_to_point':card.money_to_point

                }

                self.env['corefory.loyalty.card.history'].create(history)

                history = {
                    'card_id': card.id,
                    'changed_point': order.changed_point,
                    'user_id': self.env.uid,
                    'type': 'minus',
                    'order_id': order.id,
                    'origin' : order.name,
                    'point_to_money': card.point_to_money,
                    'money_to_point': card.money_to_point
                }
                convertible_point -= order.changed_point

                self.env['corefory.loyalty.card.history'].create(history)
                card.update({
                    'total_point': total_point,
                    'convertible_point': convertible_point
                })

    # @api.onchange('card_id')
    # def onchange_card_id(self):
    #     for order in self:
    #         if not self.card_id or not self.card_id.partner_id:
    #             continue
    #         order.partner_id = self.card_id.partner_id
    #
    #         card = self.env['corefory.loyalty.card']._get_card(order.partner_id.id)
    #
    #         if not card:
    #             continue
    #
    #         amount = card.convert_point_to_amount(card.convertible_point)
    #         amount_total = order.amount_total - amount
    #
    #         self._amount_all()
    #
    #         order.update({
    #             'amount_total': amount_total,
    #         })


    @api.onchange('card_id')
    def onchange_card_id(self):
        self._amount_all()

    @api.multi
    @api.depends('card_id')
    def _update_amount_total(self):
        for order in self:
            order.amount_total = 10000

    @api.depends('order_line.price_total')
    def _amount_all(self):
        super(SaleOrder, self)._amount_all()

        def reset_coupon():
            vals['coupon_discount_percentage'] = 0.0
            vals['coupon_discount_percentage_amount'] = 0.0
            vals['coupon_discount_fix'] = 0.0
            vals['coupon_id'] = None
            return vals

        # compute to apply loyalty card
        for order in self:
            amount_total = order.amount_total
            vals = {
                'amount_total': amount_total
            }
            if self.card_id and self.card_id.partner_id:
                order.partner_id = self.card_id.partner_id

                card = self.env['corefory.loyalty.card']._get_card(order.partner_id.id)

                if card:
                    points = 0
                    remain_points = 0
                    remain_amount = 0
                    # if (order.changed_point == 0) :
                    #     is_convert, amount = card.convert_point_to_amount(card.convertible_point,card)
                    # else:
                    #     is_convert, amount = card.convert_point_to_amount(order.changed_point,card)
                    is_convert, convertible_amount = card.convert_point_to_amount(card.convertible_point, card)
                    convertible_point = card.convertible_point
                    if((order.amount_total - convertible_amount) > 0):
                        amount_total = (order.amount_total - convertible_amount)
                    else:
                        amount_total = 0
                        remain_amount = convertible_amount - order.amount_total
                        remain_is_converted, remain_points = card.convert_amount_to_point_base(remain_amount, card)

                    # if (is_convert) :
                    #     is_converted, points = card.convert_amount_to_point_base(amount,card)
                    #      card.convertible_point = card.convertible_point - points

                    vals['amount_total'] = amount_total
                    vals['changed_point'] = convertible_point - remain_points
                    vals['changed_money'] = convertible_amount - remain_amount

            if(order.apply_coupon):
                Coupon_object = self.env['corefory.coupon']
                coupon = Coupon_object.get_coupon([('code','=',order.coupon_code)])
                if(coupon):
                    if(coupon.applied_on == '3_global'):
                        coupon_discount_percentage = coupon.percentage
                        coupon_discount_percentage_amount = 0.0
                        coupon_discount_fix = coupon.fixed_price

                        if(coupon.compute_price == 'percentage'):
                            coupon_discount_percentage_amount = ( amount_total*coupon_discount_percentage/100 )
                            amount_total = amount_total - coupon_discount_percentage_amount

                        elif(coupon.compute_price == 'fixed'):
                            amount_total = amount_total -  coupon_discount_fix
                            if(amount_total < 0) :
                                amount_total = 0.0

                        vals['amount_total'] = amount_total
                        vals['coupon_discount_percentage'] = coupon_discount_percentage
                        vals['coupon_discount_percentage_amount'] = coupon_discount_percentage_amount
                        vals['coupon_discount_fix'] = coupon_discount_fix
                        vals['coupon_id'] = coupon.id

                    elif(coupon.applied_on == '2_product_category' or coupon.applied_on=='1_product'):
                        amount_need_discount = 0
                        amount_donot_need_discount = 0
                        number_product_can_apply = 0
                        for line in order.order_line:
                            if(coupon.applied_on == '2_product_category'):
                                if(line.product_id.categ_id.id == coupon.categ_id.id):
                                    amount_need_discount += line.price_total
                                    number_product_can_apply += 1
                                else:
                                    amount_donot_need_discount += line.price_total
                            elif(coupon.applied_on=='1_product'):
                                if (line.product_id.id in coupon.product_ids.ids):
                                    amount_need_discount += line.price_total
                                    number_product_can_apply += 1
                                else:
                                    amount_donot_need_discount += line.price_total
                        if(coupon.number_product_can_apply <= number_product_can_apply):
                            coupon_discount_percentage = coupon.percentage
                            coupon_discount_percentage_amount = 0.0
                            coupon_discount_fix = coupon.fixed_price
                            if (coupon.compute_price == 'percentage'):
                                coupon_discount_percentage_amount = (amount_need_discount * coupon_discount_percentage / 100)
                                amount_need_discount = amount_need_discount - coupon_discount_percentage_amount

                            elif (coupon.compute_price == 'fixed'):
                                amount_need_discount = amount_need_discount - coupon_discount_fix
                                if (amount_need_discount < 0):
                                    amount_need_discount = 0.0

                            vals['amount_total'] = amount_need_discount + amount_donot_need_discount
                            vals['coupon_discount_percentage'] = coupon_discount_percentage
                            vals['coupon_discount_percentage_amount'] = coupon_discount_percentage_amount
                            vals['coupon_discount_fix'] = coupon_discount_fix
                            vals['coupon_id'] = coupon.id
                        else:
                            vals = reset_coupon()
                else:
                    vals = reset_coupon()
            order.update(vals)

    def get_discount_using_coupon(self, coupon,amount_total):
        coupon_discount_percentage = coupon.percentage
        coupon_discount_percentage_amount = 0.0
        coupon_discount_fix = coupon.fixed_price
        if (coupon.compute_price == 'percentage'):
            coupon_discount_percentage_amount = (amount_total * coupon_discount_percentage / 100)
            amount_total = amount_total - coupon_discount_percentage_amount

        elif (coupon.compute_price == 'fixed'):
            amount_total = amount_total - coupon_discount_fix
            if (amount_total < 0):
                amount_total = 0.0

        return amount_total

    def compute_amount_all_base(self):
        """
        Compute the total amounts of the SO.
        """
        output = {
            'amount_untaxed': 0,
            'amount_tax': 0,
            'amount_total': 0
        }
        for order in self:
            amount_untaxed = amount_tax = 0.0
            for line in order.order_line:
                amount_untaxed += line.price_subtotal
                # FORWARDPORT UP TO 10.0
                if order.company_id.tax_calculation_rounding_method == 'round_globally':
                    price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
                    taxes = line.tax_id.compute_all(price, line.order_id.currency_id, line.product_uom_qty,
                                                    product=line.product_id, partner=order.partner_shipping_id)
                    amount_tax += sum(t.get('amount', 0.0) for t in taxes.get('taxes', []))
                else:
                    amount_tax += line.price_tax

            output = {
                'amount_untaxed': order.pricelist_id.currency_id.round(amount_untaxed),
                'amount_tax': order.pricelist_id.currency_id.round(amount_tax),
                'amount_total': amount_untaxed + amount_tax,
            }

        return output