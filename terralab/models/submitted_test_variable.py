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
    test_variable = fields.Many2one('terralab.testvariable', 'Test Variable', track_visibility='onchange') # Every Submitted Test Variable is a specific TestVariable
    order = fields.Many2one('sale.order', 'Order', track_visibility='onchange') # Submitted Test Variable is always attached to an Order
    value = fields.Char(track_visibility='onchange')
    name = fields.Char(compute='_get_name', store=True, track_visibility='onchange')
    order_name = fields.Char(compute='_get_order_name', store=True, track_visibility='onchange')

    @api.depends('submitted_test', 'test_variable', 'value')
    def _get_name(self):
        for item in self:
            if item.submitted_test and item.test_variable:
                # This is ugly, sorry.
                for submitted_test in item.submitted_test:
                    for submitted_test_id, submitted_test_name in submitted_test.name_get():
                        item.name = '%s %s' % (submitted_test_name, item.test_variable.name)
            else:
                item.name = ''

    @api.depends('submitted_sample', 'submitted_sample.order')
    def _get_order_name(self):
        for item in self:
            if item.submitted_sample and item.submitted_sample.order:
                item.order_name = item.submitted_sample.order.name
            else:
                item.order_name = ''

    # What's the next required action for this submitted_test variable?
    def compute_terralab_next_action(self, order_terralab_status):
        if order_terralab_status in ('submitted', 'accepted', 'rejected'):
            if self.value == '' or self.value == False:
                return _('Add value for submitted test variable %s') % (self.name)
        # No action required for this test variable
        return ''