# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _
import odoo.http as http
from odoo.http import request
from odoo.tools.safe_eval import safe_eval
import json
import time

class Corefory_crm(http.Controller):

    @http.route('/corefory_crm/loyalty_card/get_card', type='json', auth='user')
    def get_card(self, req, partner_id,total_amount, **kw):
        card_object = request.env['corefory.loyalty.card']
        card = card_object._get_card(partner_id)
        account_prec = card.company_id.currency_id.decimal_places
        if(card):

            remain_points = 0
            remain_amount = 0

            is_convert, convertible_amount = card.convert_point_to_amount(card.convertible_point, card)
            convertible_point = card.convertible_point
            if ((total_amount - convertible_amount) > 0):
                amount_total = (total_amount - convertible_amount)
            else:
                amount_total = 0
                remain_amount = convertible_amount - total_amount
                remain_is_converted, remain_points = card.convert_amount_to_point_base(remain_amount, card)

            out_put_array = {
                'card': {
                            'id' : card.id,
                            'name' : card.name,
                            'total_point' : card.total_point,
                            'convertible_point' : card.convertible_point,
                            'changed_point' : convertible_point - remain_points,
                            'changed_money' : round(convertible_amount - remain_amount, account_prec)
                        },
                'status' : True
            }
        else:
            out_put_array = {
                'card': None,
                'status': False
            }
        return out_put_array


    @http.route('/corefory_crm/loyalty_card/convert_point_to_amount', type='json', auth='user')
    def convert_point_to_amount(self, req, card, **kw):
        account_prec = card.company_id.currency_id.decimal_places
        is_convert, amount = card.convert_point_to_amount(card.convertible_point, card)

        out_put_array = {
            'is_convert': is_convert,
            'amount': round(amount, account_prec)
        }
        return out_put_array

    @http.route('/corefory_crm/pack_lot/get_available_pack_lot', type='json', auth='user')
    def get_available_pack_lot(self, req, product_id,stock_location_id):
        pack_lot_object = request.env['stock.production.lot']

        domains = [('product_id','=' , product_id) ,
                    ('product_id.qty_available' ,'>=' ,1) ,
                    ('life_date','>=' , fields.Datetime.now())
                   ]

        pack_lots = pack_lot_object.search(domains);

        out_put_array = []
        Quant = request.env['stock.quant']
        for pack_lot in pack_lots:
            countries = Quant.sudo().read_group([('product_id','=',product_id ),('lot_id','=',pack_lot.id ),('location_id','=',stock_location_id )],
                                                  ["product_id", "location_id","qty"], groupby=['product_id',"location_id"],)
            available_quantity = sum(country_dict['qty'] for country_dict in countries)
            if(available_quantity > 0):
                out_put_array.append({
                    'id' : pack_lot.id,
                    'name' : pack_lot.name,
                    'life_date' : time.strftime('%d/%m/%Y', time.strptime(pack_lot.life_date,'%Y-%m-%d %H:%M:%S')),
                    'product_qty' : available_quantity,
                })

        return out_put_array

    @http.route('/corefory_crm/coupon/get_coupon', type='json', auth='user')
    def get_coupon(self, req, coupon_code,amount_total,partner_id,order_lines, **kw):
        coupon_object = request.env['corefory.coupon']
        coupon = coupon_object.get_coupon([('code', '=', coupon_code)])
        if(coupon and coupon.can_use):
            if(amount_total < coupon.total_amount_can_apply):
                out_put_array = {
                    'coupon': None,
                    'status': False,
                    'message': _("Total amount is less than " + str(coupon.total_amount_can_apply)),
                }

                return out_put_array;

            if (coupon.compute_number_of_use_each_customer(partner_id) >= coupon.number_order_for_each_customer):
                out_put_array = {
                    'coupon': None,
                    'status': False,
                    'message': _("This customer has used maximum code"),
                }

                return out_put_array
            # check Number product can apply?
            number_product_can_apply = 0
            if (coupon.applied_on == '3_global'):
                number_product_can_apply = len(order_lines)
            elif (coupon.applied_on == '2_product_category' or coupon.applied_on == '1_product'):
                number_product_can_apply = 0
            for line in order_lines:
                if (coupon.applied_on == '2_product_category'):
                    if (line.get('product_id').get('categ_id').get('id') == coupon.categ_id.id):
                        number_product_can_apply += 1
                elif (coupon.applied_on == '1_product'):
                    if(line.get('product_id').get('id') in coupon.product_ids.ids):
                        number_product_can_apply += 1

            if (coupon.number_product_can_apply > number_product_can_apply):
                out_put_array = {
                    'coupon': None,
                    'status': False,
                    'message': _("You order less than " + str(coupon.number_product_can_apply) + " product(s)"),
                }

                return out_put_array
            # end check Number product can apply?
            out_put_array = {
                'coupon': {
                    'id': coupon.id,
                    'name': coupon.name,
                    'code':coupon.code,
                    'compute_price': coupon.compute_price,
                    'applied_on': coupon.applied_on,
                    'apply_golden_hour': coupon.apply_golden_hour,
                    'can_use': coupon.can_use,
                    'categ_id':  coupon.categ_id.id if (coupon.categ_id) else  0,
                    'end_date': coupon.end_date,
                    'end_time': coupon.end_time,
                    'fixed_price': coupon.fixed_price,
                    'gifts':coupon.gifts.ids,
                    'max_use': coupon.max_use,
                    'number_of_remaining_use': coupon.number_of_remaining_use,
                    'number_of_use': coupon.number_of_use,
                    'number_order_for_each_customer': coupon.number_order_for_each_customer,
                    'number_product_can_apply': coupon.number_product_can_apply,
                    'percentage': coupon.percentage,
                    'price_discount': coupon.price_discount,
                    'price_max_margin': coupon.price_max_margin,
                    'price_min_margin': coupon.price_min_margin,
                    'price_round': coupon.price_round,
                    'price_surcharge': coupon.price_surcharge,
                    'product_ids': coupon.product_ids.ids,
                    'start_date' : coupon.start_date,
                    'start_time':coupon.start_time,
                    'total_amount_can_apply': coupon.total_amount_can_apply,

                    # for saving order
                    'coupon_discount_percentage' : 0,
                    'coupon_discount_percentage_amount': 0,
                    'coupon_discount_fix': 0,
                    'coupon_id': 0,
                    'amount_total': 0

                },
                'status': True
            }
        else:
            out_put_array = {
                'coupon': None,
                'status': False,
                'message': _("Invalid coupon code! Please other code"),
            }

        return out_put_array