# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Extend Odoo Order Line to link to TerraLab tests.
# By default, the order line is linked to the Order and to the Test Products.
# We add a link to the Submitted Sample that generated the Order Line.
class OrderLine(models.Model):
    _name = 'sale.order.line'
    _inherit = 'sale.order.line'
    terralab_submitted_sample = fields.Many2one('terralab.submittedsample', 'Submitted Sample', track_visibility='onchange') # An Order Line is attached to a specific Submitted Sample
    terralab_submitted_tests = fields.One2many('terralab.submittedtest', 'order_line', 'Submitted Tests', track_visibility='onchange') # An Order Line is attached to multiple Submitted Tests

# Extend Odoo Order
class Order(models.Model):
    _name = 'sale.order'
    _inherit = 'sale.order'
    terralab_status = fields.Selection([
        ('draft', _('Draft')),
        ('submitted', _('Submitted')),
        ('accepted', _('Accepted')),
        ('rejected', _('Rejected')),
        ('calculated', _('Calculated')),
        ('validated', _('Validated')),
        ('completed', _('Completed')),
    ], string='TerraLab Status', default=None)
    terralab_draft_date = fields.Datetime(string='Draft Date', readonly=True)
    terralab_submitted_date = fields.Datetime(string='Submitted Date', readonly=True)
    terralab_accepted_date = fields.Datetime(string='Accepted Date', readonly=True)
    terralab_rejected_date = fields.Datetime(string='Rejected Date', readonly=True)
    terralab_calculated_date = fields.Datetime(string='Calculated Date', readonly=True)
    terralab_validated_date = fields.Datetime(string='Validated Date', readonly=True)
    terralab_completed_date = fields.Datetime(string='Completed Date', readonly=True)

    # Samples
    terralab_submitted_samples = fields.One2many('terralab.submittedsample', 'order', 'TerraLab Samples') # All Samples Submitted to this Order
    terralab_submitted_samples_count = fields.Integer(compute='_compute_submitted_samples_count', store=True)

    # Tests
    terralab_submitted_tests = fields.One2many('terralab.submittedtest', 'order', 'TerraLab Tests') # All Tests Submitted to this Order
    terralab_submitted_tests_count = fields.Integer(compute='_compute_submitted_tests_count', store=True)

    # Test Variables
    terralab_submitted_test_variables = fields.One2many('terralab.submittedtestvariable', 'order', 'TerraLab Test Variables') # All Test Variables Submitted to this Order
    terralab_submitted_test_variables_count = fields.Integer(compute='_compute_submitted_test_variables_count', store=True)

    # Other
    terralab_next_action = fields.Char(compute='_compute_terralab_next_action', store=True) # Next action required

    @api.depends('terralab_submitted_samples', 'terralab_status', 'terralab_submitted_samples.submitted_tests', 'terralab_submitted_samples.submitted_tests.submitted_test_variables', 'terralab_submitted_samples.submitted_tests.submitted_test_variables.value')
    def _compute_terralab_next_action(self):
        for item in self:
            item.terralab_next_action = item.compute_terralab_next_action(self.terralab_status)

    @api.depends('terralab_submitted_samples')
    def _compute_submitted_samples_count(self):
        for item in self:
            submitted_samples_count = 0
            for submitted_sample in item.terralab_submitted_samples:
                submitted_samples_count += 1
            item.terralab_submitted_samples_count = submitted_samples_count

    @api.depends('terralab_submitted_tests')
    def _compute_submitted_tests_count(self):
        for item in self:
            submitted_tests_count = 0
            for submitted_test in item.terralab_submitted_tests:
                submitted_tests_count += 1
            item.terralab_submitted_tests_count = submitted_tests_count

    @api.depends('terralab_submitted_test_variables')
    def _compute_submitted_test_variables_count(self):
        for item in self:
            submitted_test_variables_count = 0
            for submitted_test_variable in item.terralab_submitted_test_variables:
                submitted_test_variables_count += 1
            item.terralab_submitted_test_variables_count = submitted_test_variables_count

    def compute_terralab_next_action(self, order_terralab_status):
        if len(self.terralab_submitted_samples) <= 0:
            return _('Add at least one submitted sample')
        for submitted_sample in self.terralab_submitted_samples:
            required_action = submitted_sample.compute_terralab_next_action(order_terralab_status)
            if required_action:
                return required_action
        # XXX TODO We should check if any tests in attached products are missing submitted samples
        # No required action found; check status
        if self.terralab_status == 'draft':
            # Order should be submitted
            return _('Submit order')
        elif self.terralab_status == 'submitted':
            # Order should be accepted
            return _('Accept or reject order')
        elif self.terralab_status == 'accepted':
            # Order should be calculated
            return _('Calculate test results')
        elif self.terralab_status == 'calculated':
            # Order should be validated
            return _('Validate test results')
        elif self.terralab_status == 'validated':
            # Order should be completed
            return _('Complete order')
        return ''

    # Create Submitted Tests and Submitted Test Variables for all tests in this Test Product
    def _add_terralab_test_objects(self, terralab_test_type, submitted_sample, test_product, is_from_bom):
        SubmittedTest = self.env['terralab.submittedtest']
        SubmittedTestVariable = self.env['terralab.submittedtestvariable']
        OrderLine = self.env['sale.order.line']

        # Do we already have an order line for this test product in this order?
        submitted_test = None
        order_line = None
        for existing_order_line in self.order_line:
            if existing_order_line.product_template_id.id == test_product.id and existing_order_line.terralab_submitted_sample and existing_order_line.terralab_submitted_sample.id == submitted_sample.id:
                logger.info(' - Found existing order line %s' % (existing_order_line))
                order_line = existing_order_line
                # Do we already have a submitted test for this submitted sample and test type
                for existing_submitted_test in existing_order_line.terralab_submitted_tests:
                    if existing_submitted_test.test_type and existing_submitted_test.test_type.id == terralab_test_type.id:
                        submitted_test = existing_submitted_test

        if not order_line:
            # Create order line
            order_line = OrderLine.create({
                'order_id': self.id,
                'product_id': test_product.id,
                'name': test_product.name,
                'product_uom': test_product.uom_id.id if test_product.uom_id else None,
                'terralab_submitted_sample': submitted_sample.id,
            })
            order_line.product_id_change()

        if not submitted_test:
            # Create Submitted Test
            submitted_test = SubmittedTest.create({
                'test_type': terralab_test_type.id,
                'order': self.id,
                'order_line': order_line.id,
                'submitted_sample': submitted_sample.id,
                'test_result_uom': terralab_test_type.test_result_uom.id if terralab_test_type.test_result_uom else None,
            })

        # Create Submitted Test Variables
        for test_variable_type in terralab_test_type.test_variable_types:
            logger.info('Creating Submitted Test Variable for Test Variable Type: %s' % (test_variable_type))
            submitted_test_variable = None
            for existing_submitted_test_variable in self.terralab_submitted_test_variables:
                if existing_submitted_test_variable.test_variable_type.id == test_variable_type.id and \
                    existing_submitted_test_variable.order.id == self.id and \
                    existing_submitted_test_variable.submitted_sample.id == submitted_sample.id and \
                    existing_submitted_test_variable.submitted_test.id == submitted_test.id:
                        submitted_test_variable = existing_submitted_test_variable
            if not submitted_test_variable:
                submitted_test_variable = SubmittedTestVariable.create({
                    'test_variable_type': test_variable_type.id,
                    'order': self.id,
                    'submitted_sample': submitted_sample.id,
                    'submitted_test': submitted_test.id,
                })

    def _create_order_lines_for_test_types(self):
        # Create Order Lines for all Submitted Samples
        for submitted_sample in self.terralab_submitted_samples:
            logger.info('Checking Order Submitted Sample %s' % (submitted_sample))
            # Create OrderLines for all Test Products
            for test_product in submitted_sample.test_products:
                logger.info('Checking Order Sample Test Product %s' % (test_product))

                # Direct tests
                if hasattr(test_product, 'terralab_test_types'):
                    for terralab_test in test_product.terralab_test_types:
                        self._add_terralab_test_objects(terralab_test, submitted_sample, test_product, False)

                # BoM tests
                if hasattr(test_product, 'bom_ids'):
                    for bom_id in test_product.bom_ids:
                        if hasattr(bom_id, 'bom_line_ids'):
                            for bom_line_id in bom_id.bom_line_ids:
                                if bom_line_id.product_id and hasattr(bom_line_id.product_id, 'terralab_test_types'):
                                    for terralab_test in bom_line_id.product_id.terralab_test_types:
                                        self._add_terralab_test_objects(terralab_test, submitted_sample, test_product, True)

    def _set_terralab_status_date(self, values, old_status):
        new_status = values.get('terralab_status', '')
        if new_status != old_status:
            if new_status == 'draft':
                values['terralab_draft_date'] = fields.Datetime.now()
            if new_status == 'submitted':
                values['terralab_submitted_date'] = fields.Datetime.now()
            if new_status == 'accepted':
                values['terralab_accepted_date'] = fields.Datetime.now()
            if new_status == 'rejected':
                values['terralab_rejected_date'] = fields.Datetime.now()
            if new_status == 'calculated':
                values['terralab_calculated_date'] = fields.Datetime.now()
            if new_status == 'validated':
                values['terralab_validated_date'] = fields.Datetime.now()
            if new_status == 'completed':
                values['terralab_completed_date'] = fields.Datetime.now()

    @api.model
    def create(self, values):
        # If any TerraLab Submitted Samples are included in the order, set the TerraLab status to Draft so it appears in lists
        if len(values.get('terralab_submitted_samples', [])) > 0 and not values.get('terralab_status', ''):
            logger.info('Created Order contains TerraLab Submitted Samples, setting status to draft')
            values['terralab_status'] = 'draft'
            values['terralab_draft_date'] = fields.Date.to_string(datetime.now())
        self._set_terralab_status_date(values, '')
        order = super(Order, self).create(values)
        order._create_order_lines_for_test_types()
        return order

    def write(self, values):
        self._set_terralab_status_date(values, self.terralab_status)
        super(Order, self).write(values)
        self._create_order_lines_for_test_types()
        # If TerraLab stauts it not set yet, check if order contains TerraLab tests and set to draft
        if not self.terralab_status:
            is_terralab_order = False
            for order_line in self.order_line:
                if len(order_line.product_id.terralab_test_types) > 0:
                    is_terralab_order = True
            if is_terralab_order:
                # Default order to draft status
                super(Order, self).write({
                    'terralab_status': 'draft',
                    'terralab_draft_date': fields.Date.to_string(datetime.now()),
                })
        return True

    # Order form action: Mark order TerraLab status as submitted
    def action_terralab_submit(self):
        self.write({
            'terralab_status': 'submitted',
        })

    # Order form action: Mark order TerraLab status as draft
    def action_terralab_draft(self):
        self.write({
            'terralab_status': 'draft',
        })

    # Order form action: Mark order TerraLab status as accepted
    def action_terralab_accept(self):
        self.write({
            'terralab_status': 'accepted',
        })

    # Order form action: Mark order TerraLab status as rejected
    def action_terralab_reject(self):
        self.write({
            'terralab_status': 'rejected',
        })


    # Order form action: Calculate test results
    def action_terralab_calculate(self):
        self.calculate_all_test_results()
        self.write({
            'terralab_status': 'calculated',
        })

    # Order form action: Mark order TerraLab status as validated
    def action_terralab_validate(self):
        self.write({
            'terralab_status': 'validated',
        })

    # Order form action: Mark order TerraLab status as complete
    def action_terralab_complete(self):
        self.write({
            'terralab_status': 'completed',
        })

    # Calculate test results using spreadsheet
    def calculate_all_test_results(self):
        for order in self:
            for submitted_sample in order.terralab_submitted_samples:
                for submitted_test in submitted_sample.submitted_tests:
                    submitted_test.calculate_test_result()
