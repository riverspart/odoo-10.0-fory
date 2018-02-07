odoo.define('corefory.pos', function (require) {
"use strict";

// This file contains the Screens definitions. Screens are the
// content of the right pane of the pos, containing the main functionalities.
//
// Screens must be defined and named in chrome.js before use.
//
// Screens transitions are controlled by the Gui.
//  gui.set_startup_screen() sets the screen displayed at startup
//  gui.set_default_screen() sets the screen displayed for new orders
//  gui.show_screen() shows a screen
//  gui.back() goes to the previous screen
//
// Screen state is saved in the order. When a new order is selected,
// a screen is displayed based on the state previously saved in the order.
// this is also done in the Gui with:
//  gui.show_saved_screen()
//
// All screens inherit from ScreenWidget. The only addition from the base widgets
// are show() and hide() which shows and hides the screen but are also used to
// bind and unbind actions on widgets and devices. The gui guarantees
// that only one screen is shown at the same time and that show() is called after all
// hide()s
//
// Each Screens must be independant from each other, and should have no
// persistent state outside the models. Screen state variables are reset at
// each screen display. A screen can be called with parameters, which are
// to be used for the duration of the screen only.

var screens = require('point_of_sale.screens');
var point_of_sale_model = require('point_of_sale.models');
var point_of_sale_popups = require('point_of_sale.popups');
var ActionpadWidget = screens.ActionpadWidget;
var gui = require('point_of_sale.gui');
var models = require('point_of_sale.models');
var core = require('web.core');
var Model = require('web.DataModel');
var utils = require('web.utils');
var formats = require('web.formats');
var session = require('web.session');
var QWeb = core.qweb;
var _t = core._t;

var round_pr = utils.round_precision;

var CoreforyActionpadWidget = ActionpadWidget.include({

    renderElement: function() {
        var self = this;
        this._super();
        console.log(self.pos);
        // console.log(self.pos.get_client());
        // console.log('loyalty_card');
        // this.$('.actionpad').prepend(QWeb.render('corefory_crm.LoyaltyCardButton'));
        this.$('#apply_loyalty_card').change(function() {
             var client = self.pos.get_client();
             var order = self.pos.get_order();
             console.log('loyalty_card click ');
             if(this.checked) {
                 // if(client){
                  if(client){
                     console.log(client);
                     var params = {
                        'partner_id': client.id,
                         'total_amount':order.get_total_with_tax()
                     };
                     self.rpc(
                            '/corefory_crm/loyalty_card/get_card',params).done(function(result) {
                                console.log(result);
                                // var data = JSON.stringify(result);
                                var data = result;

                                if(data.status){
                                    self.$('#card_id').val(data.card.id);
                                    self.$('#card_name').text(data.card.name);


                                    console.log(order);
                                    // order.set('loyalty_card',data.card);
                                    // console.log(order.get('loyalty_card'));
                                    // order.set_client(self.pos.db.get_partner_by_id(96));
                                    order.set_loyalty_card(data.card);
                                    // console.log(self.pos.get_loyalty_card());
                                }
                            }
                        );
                 } else {
                     alert(_t("Please select customer"));
                 }
             } else {
                 var order = self.pos.get_order();
                 order.set_loyalty_card(null);
                 self.$('#card_id').val(0);
                 self.$('#card_name').text('Loyalty Card');
                 $(this).attr('checked', false);
             }


        });


        this.$('#apply_coupon').change(function() {
             var client = self.pos.get_client();
             var order = self.pos.get_order();
             if(this.checked) {
                 // if(client){
                  if(client){
                     console.log(client);
                     self.$('.coupon-code-input').show();
                  } else {
                     alert(_t("Please select customer"));
                     order.set_coupon(null);
                     self.$('.coupon-code-input').hide();
                  }
             } else {
                 var order = self.pos.get_order();
                 order.set_coupon(null);
                 self.$('#coupon_id').val(0);
                 self.$('#fory_coupon_code').val('');
                 self.$('#coupon_code').text('Coupon');
                 $(this).attr('checked', false);
                 self.$('.coupon-code-input').hide();
             }
        });

        this.$('#button_coupon_code_apply').click(function(){
             var order = self.pos.get_order();
             var client = self.pos.get_client();
             var amount_total = order.get_total_with_tax();
             console.log("order_lines");
             console.log(order.get_orderlines());
             var order_lines = order.get_orderlines();
             var order_line_length = order.get_orderlines().length;
             var order_lines_array = [];
             for(var i = 0; i < order_line_length; i++){
                var product = order_lines[i].get_product();
                order_lines_array.push({
                    'product_id' : product
                })
             }
             var params = {
                 'coupon_code': self.$('#fory_coupon_code').val(),
                 'amount_total': amount_total,
                 'partner_id': client.id,
                 'order_lines' :  order_lines_array,
             };
             self.rpc(
                 '/corefory_crm/coupon/get_coupon',params).done(function(result) {
                    console.log(result);
                     var data = result;

                     if(data.status){
                         var new_coupon = data.coupon;
                         self.$('#coupon_id').val(new_coupon.id);
                         self.$('#coupon_code').text(new_coupon.code);
                         order.set_coupon(new_coupon);

                         if(new_coupon.gifts.length > 0){
                             var i;
                             for (i = 0; i < new_coupon.gifts.length; i++) {
                                 var product = self.pos.db.get_product_by_id(new_coupon.gifts[i]);
                                 order.add_product(product, {quantity: 1, price: 0});
                             }
                         }

                         if(new_coupon.applied_on == '3_global') {
                             var coupon_discount_percentage = new_coupon.percentage;
                             var coupon_discount_percentage_amount = 0.0;
                             var coupon_discount_fix = new_coupon.fixed_price;
                             var number_product_can_apply = order.get_orderlines().length;
                             if (new_coupon.number_product_can_apply <= number_product_can_apply){
                                if(new_coupon.compute_price == 'percentage'){
                                    coupon_discount_percentage_amount = ( amount_total*coupon_discount_percentage/100 );
                                    amount_total = amount_total - coupon_discount_percentage_amount;
                                } else if(new_coupon.compute_price == 'fixed') {
                                    amount_total = amount_total -  coupon_discount_fix;
                                    if(amount_total < 0) {
                                         amount_total = 0.0;
                                    }
                                }

                                new_coupon.amount_total = amount_total;
                                new_coupon.coupon_discount_percentage = coupon_discount_percentage;
                                new_coupon.coupon_discount_percentage_amount = coupon_discount_percentage_amount;
                                new_coupon.coupon_discount_fix= coupon_discount_fix;
                                new_coupon.coupon_id = new_coupon.id;
                                 order.set_coupon(new_coupon);
                             }
                         } else if(new_coupon.applied_on == '2_product_category' || new_coupon.applied_on=='1_product'){
                              var amount_need_discount = 0;
                              var  amount_donot_need_discount = 0;
                              number_product_can_apply = 0;
                              var i = 0;
                              var order_lines = order.get_orderlines();
                              var order_line_length = order.get_orderlines().length;
                              for(i = 0; i < order_line_length; i++){
                                    if(new_coupon.applied_on == '2_product_category') {
                                        if (order_lines[i].get_product().categ_id == new_coupon.categ_id){
                                            amount_need_discount += order_lines[i].get_price_with_tax();
                                            number_product_can_apply += 1;
                                        }else{
                                            amount_donot_need_discount += order_lines[i].get_price_with_tax();
                                        }

                                    }else if(new_coupon.applied_on=='1_product'){
                                        console.log('product id');
                                        console.log(order_lines[i].get_product().id);
                                        console.log('new_coupon.product_ids');
                                        console.log(new_coupon.product_ids);

                                        console.log(new_coupon.product_ids.indexOf(order_lines[i].get_product().id));

                                        if (new_coupon.product_ids.indexOf(order_lines[i].get_product().id) > -1){
                                            amount_need_discount += order_lines[i].get_price_with_tax();
                                            number_product_can_apply += 1;
                                        } else{
                                            amount_donot_need_discount += order_lines[i].get_price_with_tax();
                                        }
                                    }
                              }

                              console.log('number_product_can_apply');
                              console.log(number_product_can_apply);
                              if(new_coupon.number_product_can_apply <= number_product_can_apply){
                                   coupon_discount_percentage = new_coupon.percentage;
                                   coupon_discount_percentage_amount = 0.0;
                                   coupon_discount_fix = new_coupon.fixed_price;
                                   console.log('new_coupon.compute_price');
                                   console.log(new_coupon.compute_price);
                                   console.log(new_coupon.compute_price == 'percentage');
                                  if (new_coupon.compute_price == 'percentage'){
                                        coupon_discount_percentage_amount = (amount_need_discount * coupon_discount_percentage / 100);
                                        console.log(coupon_discount_percentage_amount);
                                        amount_need_discount = amount_need_discount - coupon_discount_percentage_amount;
                                  } else if (new_coupon.compute_price == 'fixed'){
                                      amount_need_discount = amount_need_discount - coupon_discount_fix;
                                      if (amount_need_discount < 0){
                                           amount_need_discount = 0.0;
                                      }
                                  }
                                    new_coupon.amount_total= amount_need_discount + amount_donot_need_discount;
                                    new_coupon.coupon_discount_percentage = coupon_discount_percentage;
                                    new_coupon.coupon_discount_percentage_amount = coupon_discount_percentage_amount;
                                    new_coupon.coupon_discount_fix = coupon_discount_fix;
                                    new_coupon.coupon_id = new_coupon.id;
                                    console.log('after updating new_coupon');
                                    console.log(new_coupon);
                                    order.set_coupon(new_coupon);
                              }

                         }
                     } else {
                        alert(data.message);
                     }
                 }
             );
        });

    }
});
var _super_order = models.Order.prototype;
point_of_sale_model.Order = point_of_sale_model.Order.extend({
    initialize: function() {
        _super_order.initialize.apply(this,arguments);
        this.loyalty_card = this.loyalty_card || null;
        this.set_loyalty_card(this.loyalty_card);

        this.coupon = this.coupon || null;
        this.set_coupon(this.coupon);

        this.save_to_db();
    },
    set_loyalty_card: function(loyalty_card){
        this.assert_editable();
        this.set('loyalty_card',loyalty_card);
        this.loyalty_card = loyalty_card;
        this.save_to_db();
    },

    get_loyalty_card: function(){
        return this.get('loyalty_card');
    },


    set_coupon: function(coupon){
        this.assert_editable();
        this.set('coupon',coupon);
        this.coupon = coupon;
        this.save_to_db();
    },

    get_coupon: function(){
        return this.get('coupon');
    },

    init_from_JSON: function(json) {
        _super_order.init_from_JSON.apply(this,arguments);
        this.set_loyalty_card(json.loyalty_card);
        this.set_coupon(json.coupon);
    },

    export_as_JSON: function() {
        var json = _super_order.export_as_JSON.apply(this,arguments);
        json.loyalty_card = this.loyalty_card;
        json.coupon = this.coupon;
        return json;
    },


    export_for_printing: function() {
        var json = _super_order.export_for_printing.apply(this,arguments);
        json.loyalty_card = this.get_loyalty_card();
        json.coupon = this.get_coupon();
        return json;
    },

    get_total_with_tax: function(){
        var total_with_tax_with_other_discount = _super_order.get_total_with_tax.apply(this,arguments);

        if(this.get_loyalty_card() != null){
            total_with_tax_with_other_discount = total_with_tax_with_other_discount - this.get_loyalty_card().changed_money
        }


        if(this.get_coupon() != null){
            total_with_tax_with_other_discount = total_with_tax_with_other_discount - this.get_coupon().coupon_discount_percentage_amount -  this.get_coupon().coupon_discount_fix;
        }


        if(total_with_tax_with_other_discount < 0){
            total_with_tax_with_other_discount = 0;
        }

        return total_with_tax_with_other_discount;
    },

    get_total_with_tax_with_other_discount: function(){
        var total_with_tax_with_other_discount = _super_order.get_total_with_tax();

        if(this.get_loyalty_card() != null) {
            total_with_tax_with_other_discount = total_with_tax_with_other_discount - this.get_loyalty_card().changed_money

        }

        return total_with_tax_with_other_discount;
    },

    // get_total_without_tax: function() {
    //     var total_without_tax = _super_order.get_total_without_tax.apply(this,arguments);
    //
    //     if(this.get_loyalty_card() != null) {
    //         total_without_tax = total_without_tax - this.get_loyalty_card().changed_money
    //     }
    //
    //     return total_without_tax;
    // },
    display_lot_popup: function() {
        var order_line = this.get_selected_orderline();
        var self = this;

        if (order_line){

            console.log(order_line);
            var pack_lot_lines =  order_line.compute_lot_lines();

            var params = {
                product_id: order_line.product.id,
                stock_location_id: order_line.pos.config.stock_location_id[0]
            };
            session.rpc('/corefory_crm/pack_lot/get_available_pack_lot',params).done(function(result) {
                console.log(result);
                var available_pack_lot = result;
                self.pos.gui.show_popup('corefory_crm_packlotline', {
                    'title': _t('Lot/Serial Number(s) Required'),
                    'pack_lot_lines': pack_lot_lines,
                    'order': self,
                    'available_pack_lot' : available_pack_lot
                });
            });
        }
    },
});


point_of_sale_model.PosModel = point_of_sale_model.PosModel.extend({
    // set_loyalty_card: function(loyalty_card){
    //     this.set('loyalty_card',loyalty_card);
    // },

    get_loyalty_card: function(){
        var order = this.get_order();
        // console.log('get_order');
        // console.log(order);
        // console.log(order.get_loyalty_card());
        if (order) {
            return order.get_loyalty_card();
        }
        return null;
    },


    get_coupon: function(){
        var order = this.get_order();
        // console.log('get_order');
        // console.log(order);
        // console.log(order.get_loyalty_card());
        if (order) {
            return order.get_coupon();
        }
        return null;
    },
});
// var _super_pack_lot_line = models.Packlotline.prototype;
// point_of_sale_model.Packlotline = point_of_sale_model.Packlotline.extend({
//     initialize: function(attributes, options){
//         _super_pack_lot_line.initialize.apply(this,arguments);
//
//         console.log(attributes);
//         console.log(options);
//     },
// });
screens.OrderWidget.include({
    update_summary: function(){
        console.log('update_summary');

        this._super();
        var self = this;
        var order = this.pos.get_order();
        if (!order.get_orderlines().length) {
            return;
        }
        this.el.querySelector('.summary .total .changed_money').style.display = "none";
        this.el.querySelector('.summary .total .coupon_discount_percentage').style.display = "none";
        this.el.querySelector('.summary .total .coupon_discount_fix').style.display = "none";

        var order = this.pos.get_order();
        var total = order ? order.get_total_with_tax() : 0;
        // total = total - order.get_loyalty_card().changed_money;
        var taxes = order ? order.get_total_tax() : 0;

        this.el.querySelector('.summary .total > .value').textContent = this.format_currency(total);
        this.el.querySelector('.summary .total .subentry .value').textContent = this.format_currency(taxes);


        if(this.pos.get_loyalty_card() != null) {
            this.el.querySelector('.summary .total .changed_money').style.display = "block";
            this.el.querySelector('.summary .total .changed_money .value').textContent = order.get_loyalty_card().changed_money;
        }
        if(this.pos.get_coupon() != null) {
            this.el.querySelector('.summary .total .coupon_discount_percentage').style.display = "block";
            this.el.querySelector('.summary .total .coupon_discount_percentage .value').textContent = order.get_coupon().coupon_discount_percentage + "% = " + order.get_coupon().coupon_discount_percentage_amount ;

            this.el.querySelector('.summary .total .coupon_discount_fix').style.display = "block";
            this.el.querySelector('.summary .total .coupon_discount_fix .value').textContent = order.get_coupon().coupon_discount_fix;
        }
    }
});

var CoreforyPackLotLinePopupWidget = point_of_sale_popups.extend({
    template: 'CoreforyPackLotLinePopupWidget',
    events: _.extend({}, point_of_sale_popups.prototype.events, {
        'click .remove-lot': 'remove_lot',
        'keydown': 'add_lot',
        'blur .packlot-line-input': 'lose_input_focus',
        'change select.corefory_available_pack_lot': 'select_available_pack_lot',
    }),

    show: function(options){
        this._super(options);
        this.focus();
    },

    click_confirm: function(){
        var pack_lot_lines = this.options.pack_lot_lines;
        this.$('.packlot-line-input').each(function(index, el){
            var cid = $(el).attr('cid'),
                lot_name = $(el).val();
            var pack_line = pack_lot_lines.get({cid: cid});
            pack_line.set_lot_name(lot_name);
        });
        pack_lot_lines.remove_empty_model();
        pack_lot_lines.set_quantity_by_lot();
        this.options.order.save_to_db();
        this.gui.close_popup();
    },

    add_lot: function(ev) {
        if (ev.keyCode === $.ui.keyCode.ENTER){
            var pack_lot_lines = this.options.pack_lot_lines,
                $input = $(ev.target),
                cid = $input.attr('cid'),
                lot_name = $input.val();

            var lot_model = pack_lot_lines.get({cid: cid});
            lot_model.set_lot_name(lot_name);  // First set current model then add new one
            if(!pack_lot_lines.get_empty_model()){
                var new_lot_model = lot_model.add();
                this.focus_model = new_lot_model;
            }
            pack_lot_lines.set_quantity_by_lot();
            this.renderElement();
            this.focus();
        }
    },

    remove_lot: function(ev){
        var pack_lot_lines = this.options.pack_lot_lines,
            $input = $(ev.target).prev(),
            cid = $input.attr('cid');
        var lot_model = pack_lot_lines.get({cid: cid});
        lot_model.remove();
        pack_lot_lines.set_quantity_by_lot();
        this.renderElement();
    },
    select_available_pack_lot: function (ev) {
        console.log('select_available_pack_lot');
        console.log(ev);
        var target = ev.target;
        var option = target.options[ target.selectedIndex];
        var value_product_qty = option.dataset.value_product_qty;
        var value_name = option.dataset.value_name;
        if(value_name != '0' && value_product_qty > 0){

            var available_pack_lot_array = {};
            var qty_added_count = 0;
            this.$('.packlot-line-input').each(function(index, el){
                var cid = $(el).attr('cid'),
                    lot_name = $(el).val();

                if(lot_name == value_name){
                    qty_added_count ++;
                    if(qty_added_count >= value_product_qty) {
                        alert('You can not input larger than available!');
                        return false;
                    }
                }
                if (lot_name == ''){
                    $(el).val(value_name);
                    return false;
                }
            });



        }

    },

    lose_input_focus: function(ev){
        var $input = $(ev.target),
            cid = $input.attr('cid');
        var lot_model = this.options.pack_lot_lines.get({cid: cid});
        lot_model.set_lot_name($input.val());
    },

    focus: function(){
        this.$("input[autofocus]").focus();
        this.focus_model = false;   // after focus clear focus_model on widget
    }
});
gui.define_popup({name:'corefory_crm_packlotline', widget:CoreforyPackLotLinePopupWidget});
});

