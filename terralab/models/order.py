# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import logging

logger = logging.getLogger(__name__)

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
#    terralab_draft_date = fields.Date(string='Draft Date', readonly=True)
#    terralab_submitted_date = fields.Date(string='Draft Date', readonly=True)
#    terralab_accepted_date = fields.Date(string='Draft Date', readonly=True)
#    terralab_rejected_date = fields.Date(string='Draft Date', readonly=True)
#    terralab_draft_date = fields.Date(string='Draft Date', readonly=True)
#    terralab_draft_date = fields.Date(string='Draft Date', readonly=True)
#    terralab_draft_date = fields.Date(string='Draft Date', readonly=True)
#    terralab_draft_date = fields.Date(string='Draft Date', readonly=True)

    # Samples
    terralab_submitted_samples = fields.One2many('terralab.submittedsample', 'order', 'TerraLab Samples') # All Samples Submitted to this Order
    terralab_submitted_samples_count = fields.Integer(compute='_compute_submitted_samples_count', store=True)

    # Tests
    terralab_submitted_tests = fields.One2many('terralab.submittedtest', 'order', 'TerraLab Tests') # All Tests Submitted to this Order
    terralab_submitted_tests_count = fields.Integer(compute='_compute_submitted_tests_count', store=True)

    # Test Variables
    terralab_submitted_test_variables = fields.One2many('terralab.submittedtestvariable', 'order', 'TerraLab Test Variables') # All Test Variables Submitted to this Order
    terralab_submitted_test_variables_count = fields.Integer(compute='_compute_submitted_test_variables_count', store=True)

    # Reports
    terralab_submitted_reports = fields.One2many('terralab.submittedreport', 'order', 'TerraLab Reports') # All Reports attached to this Order
    terralab_submitted_reports_count = fields.Integer(compute='_compute_submitted_reports_count', store=True)

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

    @api.depends('terralab_submitted_reports')
    def _compute_submitted_reports_count(self):
        for item in self:
            submitted_reports_count = 0
            for report in item.terralab_submitted_reports:
                submitted_reports_count += 1
            item.terralab_submitted_reports_count = submitted_reports_count

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
            # Report should be generated
            return _('Generate report')
        elif self.terralab_status == 'report_generated':
            # Order should be completed
            return _('Complete order')
        return ''

    # Create Submitted Tests and Submitted Test Variables for all tests in this Test Product
    def _add_terralab_test_objects(self, terralab_test_type, submitted_sample):
        SubmittedTest = self.env['terralab.submittedtest']
        SubmittedTestVariable = self.env['terralab.submittedtestvariable']

        # Do we already have a submitted test with same parameters?
        submitted_test = None
        for existing_submitted_test in self.terralab_submitted_tests:
            if existing_submitted_test.test_type.id == terralab_test_type.id and existing_submitted_test.submitted_sample.id == submitted_sample.id:
                submitted_test = existing_submitted_test
        if not submitted_test:
            # Create Submitted Test
            submitted_test = SubmittedTest.create({
                'test_type': terralab_test_type.id,
                'order': self.id,
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
        OrderLine = self.env['sale.order.line']
        SubmittedTest = self.env['terralab.submittedtest']
        SubmittedTestVariable = self.env['terralab.submittedtestvariable']

        # Create Order Lines for all Tests
        for submitted_sample in self.terralab_submitted_samples:
            logger.info('Checking Order Submitted Sample %s' % (submitted_sample))
            for test_product in submitted_sample.test_products:
                logger.info('Checking Order Sample Test Product %s' % (test_product))

                # Add order line for test product if it doesn't exist yet
                if submitted_sample.order_line:
                    logger.info('Submitted Sample already has an order line: %s' % (submitted_sample))
                else:
                    #test_product = Product.browse(submitted_test.test.id)
                    logger.info('Test Product: %s' % (test_product))
                    # Create Order Line for this Test Product
                    logger.info('Creating Order Line for Order %s Test Product %s' % (self.id, test_product))
                    order_line = OrderLine.create({
                        'order_id': self.id,
                        'product_id': test_product.id,
                        'name': test_product.name,
                        'product_uom': test_product.uom_id.id,
                    })
                    order_line.product_id_change()
                    submitted_sample.write({ 'order_line': order_line.id })

                # Direct tests
                if hasattr(test_product, 'terralab_test_types'):
                    for terralab_test in test_product.terralab_test_types:
                        self._add_terralab_test_objects(terralab_test, submitted_sample)

                # BoM tests
                if hasattr(test_product, 'bom_ids'):
                    for bom_id in test_product.bom_ids:
                        if hasattr(bom_id, 'bom_line_ids'):
                            for bom_line_id in bom_id.bom_line_ids:
                                if bom_line_id.product_id and hasattr(bom_line_id.product_id, 'terralab_test_types'):
                                    for terralab_test in bom_line_id.product_id.terralab_test_types:
                                        self._add_terralab_test_objects(terralab_test, submitted_sample)

    @api.model
    def create(self, values):
        # If any TerraLab Submitted Samples are included in the order, set the TerraLab status to Draft so it appears in lists
        if len(values.get('terralab_submitted_samples', [])) > 0:
            logger.info('Created Order contains TerraLab Submitted Samples, setting status to draft')
            values['terralab_status'] = 'draft'
        order = super(Order, self).create(values)
        order._create_order_lines_for_test_types()
        return order

    def write(self, values):
        super(Order, self).write(values)
        # Check if order contains TerraLab tests
        is_terralab_order = False
        for order_line in self.order_line:
            if len(order_line.product_id.terralab_test_types) > 0:
                is_terralab_order = True
        if is_terralab_order and not self.terralab_status:
            # Default order to draft status
            super(Order, self).write({ 'terralab_status': 'draft' })
        self._create_order_lines_for_test_types()
        return True

    # Order form action: Mark order TerraLab status as submitted
    def action_terralab_submit(self):
        # self.ensure_one()
        self.write({
            'terralab_status': 'submitted',
        })
        #next_action = self.env.ref('terralab.orders_list_action').read()[0]
        #next_action['target'] = 'main'
        #return next_action

    # Order form action: Mark order TerraLab status as draft
    def action_terralab_draft(self):
        # self.ensure_one()
        self.write({
            'terralab_status': 'draft',
        })
        #next_action = self.env.ref('terralab.orders_list_action').read()[0]
        #next_action['target'] = 'main'
        #return next_action

    # Order form action: Mark order TerraLab status as accepted
    def action_terralab_accept(self):
        # self.ensure_one()
        self.write({
            'terralab_status': 'accepted',
        })
        #next_action = self.env.ref('terralab.orders_list_action').read()[0]
        #next_action['target'] = 'main'
        #return next_action

    # Order form action: Mark order TerraLab status as rejected
    def action_terralab_reject(self):
        # self.ensure_one()
        self.write({
            'terralab_status': 'rejected',
        })
        #next_action = self.env.ref('terralab.orders_list_action').read()[0]
        #next_action['target'] = 'main'
        #return next_action

    # Order form action: Calculate test results
    def action_terralab_calculate(self):
        # self.ensure_one()
        self.calculate_all_test_results()
        self.write({
            'terralab_status': 'calculated',
        })
        #next_action = self.env.ref('terralab.calculated_orders_list_action').read()[0]
        #next_action['target'] = 'main'
        #return next_action

    # Order form action: Generate report
    def action_terralab_generate_report(self):
        self.generate_report()
        self.write({
            'terralab_status': 'report_generated',
        })
        #next_action = self.env.ref('terralab.report_generated_orders_list_action').read()[0]
        #next_action['target'] = 'main'
        #return next_action

    # Order form action: Mark order TerraLab status as complete
    def action_terralab_complete(self):
        # self.ensure_one()
        self.write({
            'terralab_status': 'completed',
        })
        #next_action = self.env.ref('terralab.completed_orders_list_action').read()[0]
        #next_action['target'] = 'main'
        #return next_action

    # Calculate test results using spreadsheet
    def calculate_all_test_results(self):
        for order in self:
            for submitted_sample in order.terralab_submitted_samples:
                for submitted_test in submitted_sample.submitted_tests:
                    submitted_test.calculate_test_result()

    # Generate test report
    def generate_report(self):
        SubmittedReport = self.env['terralab.submittedreport']
        for order in self:
            SubmittedReport.create({
                'order': order.id,
                'generated_at': fields.Datetime.now(),
            })
