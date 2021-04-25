# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import logging

logger = logging.getLogger(__name__)

class SubmittedTest(models.Model):
    _name = 'terralab.submittedtest'
    _inherit = ['mail.thread']
    _description = 'TerraLab Submitted Test'

    test_type = fields.Many2one('terralab.testtype', 'Test Type', track_visibility='onchange') # A Submitted Test is a specific Test Type
    order = fields.Many2one('sale.order', 'Order', track_visibility='onchange') # Submitted Test is always attached to an Order
    submitted_sample = fields.Many2one('terralab.submittedsample', 'Submitted Sample', track_visibility='onchange') # A Submitted Test is attached to a specific Submitted Sample
    submitted_test_variables = fields.One2many('terralab.submittedtestvariable', 'submitted_test', 'Submitted Test Variables', track_visibility='onchange') # A Submitted Test has a number of Submitted Test Variables
    test_result = fields.Char(track_visibility='onchange')
    test_result_uom = fields.Many2one('uom.uom', track_visibility='onchange')

    def name_get(self):
        return [(submitted_test.id, '%s %s %s' % (submitted_test.submitted_sample.sample_type.name, submitted_test.submitted_sample.serial_number, submitted_test.test_type.name)) for submitted_test in self]

    # Order form action: Calculate test results
    def action_terralab_calculate(self):
        self.calculate_test_result()
        return None

    # What's the next required action for this submitted test?
    def compute_terralab_next_action(self, order_terralab_status):
        if order_terralab_status in ('draft', 'submitted'):
            # In draft or submitted state test variables not yet needed; must accept first
            return ''
        if len(self.submitted_test_variables) <= 0:
            return _('Add submitted test variables for submitted test %s') % (self.name_get()[0][1])
        for submitted_test_variable in self.submitted_test_variables:
            required_action = submitted_test_variable.compute_terralab_next_action(order_terralab_status)
            if required_action:
                return required_action
        # No action required for this test
        return ''

    # Calculate test result
    def calculate_test_result(self):
        spreadsheet = self.test.spreadsheet
        result = spreadsheet.calculate_result(self.test_type, self.submitted_test_variables)
        self.write({
            'test_result': result,
        })
