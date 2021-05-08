# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import logging

logger = logging.getLogger(__name__)

class SubmittedTestVariable(models.Model):
    _name = 'terralab.submittedtestvariable'
    _inherit = ['mail.thread']
    _description = 'TerraLab Submitted Test Variable'

    submitted_sample = fields.Many2one('terralab.submittedsample', 'Submitted Sample', track_visibility='onchange') # Every Submitted Test Variable is attached to a specific Submitted Sample
    submitted_test = fields.Many2one('terralab.submittedtest', 'Submitted Test', track_visibility='onchange') # Every Submitted Test Variable is attached to a specific Submitted Test
    test_variable_type = fields.Many2one('terralab.testvariabletype', 'Test Variable Type', track_visibility='onchange') # Every Submitted Test Variable is a specific Test Variable Type
    order = fields.Many2one('sale.order', 'Order', track_visibility='onchange') # Submitted Test Variable is always attached to an Order
    order_name = fields.Char(compute='_get_order_fields', store=True, track_visibility='onchange')
    order_terralab_status = fields.Char(compute='_get_order_fields', store=True, track_visibility='onchange')
    num = fields.Integer(compute='_get_num', store=True, track_visibility='onchange')
    value = fields.Char(track_visibility='onchange')
    name = fields.Char(compute='_get_name', store=True, track_visibility='onchange')

    @api.depends('test_variable_type')
    def _get_num(self):
        for item in self:
            if item.test_variable_type:
                item.num = item.test_variable_type.num
            else:
                item.num = None

    @api.depends('submitted_test', 'test_variable_type', 'value')
    def _get_name(self):
        for item in self:
            if item.submitted_test and item.test_variable_type:
                # This is ugly, sorry.
                for submitted_test in item.submitted_test:
                    for submitted_test_id, submitted_test_name in submitted_test.name_get():
                        item.name = '%s %s' % (submitted_test_name, item.test_variable_type.name)
            else:
                item.name = ''

    @api.depends('order', 'order.name', 'order.terralab_status')
    def _get_order_fields(self):
        for item in self:
            if item.order:
                item.order_name = item.order.name
                item.terralab_status = item.order.terralab_status
            else:
                item.order_name = ''
                item.terralab_status = ''

    # What's the next required action for this submitted_test variable?
    def compute_terralab_next_action(self, order_terralab_status):
        if order_terralab_status in ('submitted', 'accepted', 'rejected'):
            if self.value == '' or self.value == False:
                return _('Add value for submitted test variable %s') % (self.name)
        # No action required for this test variable
        return ''
