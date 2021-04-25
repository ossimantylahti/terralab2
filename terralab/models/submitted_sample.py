# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import logging

logger = logging.getLogger(__name__)

class SubmittedSample(models.Model):
    _name = 'terralab.submittedsample'
    _inherit = ['mail.thread']
    _description = 'TerraLab Submitted Sample'

    sample_type = fields.Many2one('terralab.sampletype', 'Sample Type', track_visibility='onchange') # Submitted Sample is of specific Sample Type
    test_products = fields.Many2many('product.template', track_visibility='onchange') # Assigned test products
    submitted_tests = fields.One2many('terralab.submittedtest', 'submitted_sample', 'Submitted Tests', track_visibility='onchange') # Submitted Sample may have many Submitted Tests attached to it
    order = fields.Many2one('sale.order', 'Order', track_visibility='onchange') # Submitted Sample is always attached to an Order
    order_line = fields.Many2one('sale.orderline', 'Order Line', track_visibility='onchange') # Submitted Sample is automatically attached to an Order Line when creating or updating order
    serial_number = fields.Char(track_visibility='onchange') # Freeform serial number to identify submitted sample

    def name_get(self):
        return [(submitted_sample.id, '%s %s' % (submitted_sample.sample_type.name if submitted_sample.sample_type else '(no sample)', submitted_sample.serial_number if submitted_sample.serial_number else '(no serial number)')) for submitted_sample in self]

    # What's the next required action for this submitted sample?
    def compute_terralab_next_action(self, order_terralab_status):
        if not self.sample_type:
            return _('Set sample type for submitted sample %s') % (self.name_get()[0][1])
        if not self.serial_number:
            return _('Set serial number for submitted sample %s') % (self.name_get()[0][1])
        if len(self.submitted_tests) <= 0:
            return _('Add submitted tests for submitted sample %s') % (self.name_get()[0][1])
        for submitted_test in self.submitted_tests:
            required_action = submitted_test.compute_terralab_next_action(order_terralab_status)
            if required_action:
                return required_action
        # No action required for this sample
        return ''
