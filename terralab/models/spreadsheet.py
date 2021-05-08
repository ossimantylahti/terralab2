# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging
from googleapiclient.discovery import build
import google.oauth2.credentials
import re

logger = logging.getLogger(__name__)

def get_google_spreadsheets(access_token):
    credentials = google.oauth2.credentials.Credentials(access_token)
    service = build('sheets', 'v4', credentials=credentials, cache_discovery=False)
    sheets = service.spreadsheets()
    return sheets

class Spreadsheet(models.Model):
    _name = 'terralab.spreadsheet'
    _inherit = ['mail.thread']
    _description = 'TerraLab Spreadsheet'

    name = fields.Char(track_visibility='onchange', translate=True)
    spreadsheet_url = fields.Char(track_visibility='onchange')
    spreadsheet_id = fields.Char(track_visibility='onchange')
    test_types = fields.One2many('terralab.testtype', 'spreadsheet', 'Test Types', track_visibility='onchange') # Test Types attached to this spreadsheet
    test_products = fields.One2many('product.template', 'terralab_spreadsheet', 'Test Products', track_visibility='onchange') # Test products attached to this spreadsheet
    import_date = fields.Datetime(string='Import Date', readonly=True)
    import_status = fields.Char(readonly=True)

    @api.model
    def create(self, values):
        self._detect_spreadsheet_id(values)
        spreadsheet = super(Spreadsheet, self).create(values)
        return spreadsheet

    def write(self, values):
        self._detect_spreadsheet_id(values)
        super(Spreadsheet, self).write(values)
        logger.info('Writing Spreadsheet %s' % (values))
        return True

    def _detect_spreadsheet_id(self, values):
        new_url = values.get('spreadsheet_url', None)
        if new_url:
            # Extract spreadsheet ID
            m = re.match(r'.*/([^/]+)/edit.*', new_url)
            if m:
                values['spreadsheet_id'] = m.group(1)
            else:
                raise ValidationError('Invalid Spreadsheet URL - Could not detect Spreadsheet ID')

    def calculate_result(self, test_type, submitted_test_variables):
        access_token = self.env['google.drive.config'].get_access_token(scope='https://spreadsheets.google.com/feeds')
        spreadsheets = get_google_spreadsheets(access_token)
        variable_values = {}
        for submitted_test_variable in submitted_test_variables:
            variable_values[submitted_test_variable.num] = submitted_test_variable.value
        logger.info('Calculating spreadsheet %s test result with variables: %s' % (self.spreadsheet_id, variable_values))
        # Scan the spreadsheet and find the test location, its variable slots and the result slot
        test_values = spreadsheets.values().get(spreadsheetId=self.spreadsheet_id, range='Tests!A:Z').execute()
        test_rows = test_values['values']
        col_mapping = {}
        for index, col in enumerate(test_rows[0]):
            col_mapping[col] = index
        getting_test = False
        row_num = 1
        value_col_letter = chr(ord('A') + col_mapping['Values'])
        variable_refs = {}
        variable_ref_values = {}
        result_ref = None
        for test_row in test_rows[1:]:
            row_num += 1
            field_name = test_row[col_mapping['Field']] if col_mapping['Field'] < len(test_row) else None
            field_value = test_row[col_mapping['Values']] if col_mapping['Values'] < len(test_row) else None
            if field_name == 'terralab.test_name' and field_value == test_type.default_code:
                # Begin test
                logger.info('Found test %s at %s%s' % (field_value, value_col_letter, row_num))
                getting_test = True
            elif field_name == 'terralab.test_name':
                # End test
                getting_test = False
            elif getting_test and field_name:
                if field_name.startswith('terralab.variable_'):
                    var_num = int(field_name[18:])
                    if var_num in variable_values:
                        var_value = variable_values[var_num]
                        var_ref = '%s%s' % (value_col_letter, row_num)
                        variable_refs[var_num] = var_ref
                        variable_ref_values[var_ref] = var_value
                        logger.info('Got variable %s slot %s %s %s' % (var_num, var_ref, field_name, field_value))
                elif field_name == 'terralab.test_result':
                    result_ref = '%s%s' % (value_col_letter, row_num)
                    logger.info('Got result slot %s %s %s' % (result_ref, field_name, field_value))

        logger.info('Configuring test with result slot %s variable slots %s' % (result_ref, variable_refs))

        # Check that we have all slots
        if not result_ref:
            raise ValidationError('Test Result Slot Not Found')
        for var_num in variable_values.keys():
            if not var_num in variable_refs:
                raise ValidationError('Variable Slot %s Not Found' % (var_num))

        # Update the variables into the sheet
        value_range = []
        for var_ref, var_value in variable_ref_values.items():
            value_range.append({
                'range': var_ref,
                'values': [[var_value]],
            })
        update_response = spreadsheets.values().batchUpdate(spreadsheetId=self.spreadsheet_id, body={'data': value_range, 'valueInputOption': 'USER_ENTERED'}).execute()
        logger.info('Update response: %s' % (update_response))

        # Retrieve result from sheet
        result = spreadsheets.values().get(spreadsheetId=self.spreadsheet_id, range=result_ref).execute()
        values = result.get('values', [])
        logger.debug('RESULT VALUE: %s' % (values))
        return values[0][0]

    def action_import_tests_and_products(self):
        self.write({
            'import_date': fields.Datetime.now(),
            'import_status': 'in_progress',
        })
        access_token = self.env['google.drive.config'].get_access_token(scope='https://spreadsheets.google.com/feeds')
        spreadsheets = get_google_spreadsheets(access_token)
        logger.info('Importing tests from spreadsheet %s' % (self.spreadsheet_id))
        # The ranges that we'll read in one batch operation
        ranges = ['Sample types!A:Z', 'Sample type allowed tests!A:Z', 'Tests!A:Z', 'Products!A:Z', 'Product categories!A:Z', 'Target uses!A:Z', 'Target use ranges!A:Z', 'Odoo!A:Z']
        value_batches = spreadsheets.values().batchGet(spreadsheetId=self.spreadsheet_id, ranges=ranges).execute()
        value_ranges = value_batches['valueRanges']
        sample_types_range = value_ranges[0]
        sample_type_allowed_tests_range = value_ranges[1]
        tests_range = value_ranges[2]
        products_range = value_ranges[3]
        product_categories_range = value_ranges[4]
        target_uses_range = value_ranges[5]
        target_use_ranges_range = value_ranges[6]
        odoo_range = value_ranges[7]
        self.import_sample_types(sample_types_range['values'])
        self.import_tests(tests_range['values'])
        self.import_product_categories(product_categories_range['values'])
        self.import_target_uses(target_uses_range['values'])
        self.import_target_use_ranges(target_use_ranges_range['values'])
        self.import_sample_type_allowed_tests(sample_type_allowed_tests_range['values'])
        self.import_products(products_range['values'])
        self.write({
            'import_date': fields.Datetime.now(),
            'import_status': 'success',
        })

    def import_sample_types(self, rows):
        SampleType = self.env['terralab.sampletype']
        Translation = self.env['ir.translation']
        logger.info('Importing %s sample type row(s)' % (len(rows)))
        col_mapping = {}
        for index, col in enumerate(rows[0]):
            col_mapping[col] = index
        logger.info('Sample type column mapping: %s' % (col_mapping))
        for row in rows[1:]:
            logger.debug('SAMPLE TYPE: %s' % (row))
            default_code = row[col_mapping['sample_type.id']]
            # Check if sample type already exists
            existing_sample_types = SampleType.search([('spreadsheet', '=', self.id), ('default_code', '=', default_code)])
            if len(existing_sample_types) <= 0:
                # Create new sample type
                sample_type = SampleType.create({
                    'default_code': default_code,
                    'spreadsheet': self.id,
                    'name': row[col_mapping['sample_type.name en_US']],
                })
            else:
                # Update existing category
                sample_type = existing_sample_types[0]
                sample_type.write({
                    'name': row[col_mapping['sample_type.name en_US']],
                })
            # Translations
            logger.debug('SAMPLE TYPE TRANSLATIONS: %s' % (sample_type))
            for key, col_num in col_mapping.items():
                if key.startswith('sample_type.name '):
                    lang = key[17:]
                    sample_type.with_context(lang=lang).write({
                        'name': row[col_num]
                    })

    # Call import_samples() and import_tests() before calling this
    def import_sample_type_allowed_tests(self, rows):
        SampleType = self.env['terralab.sampletype']
        TestType = self.env['terralab.testtype']
        logger.info('Importing %s sample type allowed test row(s)' % (len(rows)))
        col_mapping = {}
        for index, col in enumerate(rows[0]):
            col_mapping[col] = index
        logger.info('Sample type allowed test column mapping: %s' % (col_mapping))
        sample_test_mapping = {}
        for row in rows[1:]:
            #logger.info('SAMPLE TYPE ALLOWED TEST: %s' % (row))
            sample_type_id = row[col_mapping['sample_type.id']]
            test_name = row[col_mapping['terralab.test_name']]
            if not sample_type_id in sample_test_mapping:
                sample_test_mapping[sample_type_id] = set()
            existing_test_types = TestType.search([('spreadsheet', '=', self.id), ('default_code', '=', test_name)])
            if len(existing_test_types) > 0:
                sample_test_mapping[sample_type_id].add(existing_test_types[0].id)
        for sample_type_id, test_type_ids in sample_test_mapping.items():
            logger.debug('SAMPLE TYPE %s ALLOWED TESTS %s' % (sample_type_id, test_type_ids))
            existing_sample_types = SampleType.search([('spreadsheet', '=', self.id), ('default_code', '=', sample_type_id)])
            if len(existing_sample_types) <= 0:
                raise ValidationError('Sample Type Not Found: %s (while setting allowed tests)' % (sample_type_id))
            existing_sample_types.write({
                'test_types': list(test_type_ids),
            })

    def import_tests(self, rows):
        TestType = self.env['terralab.testtype']
        #Uom = self.env['uom.uom']
        logger.info('Importing %s test row(s)' % (len(rows)))
        col_mapping = {}
        for index, col in enumerate(rows[0]):
            col_mapping[col] = index
        logger.info('Test column mapping: %s' % (col_mapping))
        current_test = {}

        def save_test_variables(test_type, current_test):
            TestVariableType = self.env['terralab.testvariabletype']
            logger.debug('TEST VARIABLES FOR %s' % (test_type))
            existing_test_variable_types = TestVariableType.search([('spreadsheet', '=', self.id), ('test_type', '=', test_type.id)])
            logger.debug(' Existing variables: %s' % (existing_test_variable_types))
            for key, item in current_test.items():
                if key.startswith('terralab.variable_') and item.get('name'):
                    var_num = int(key[18:])
                    test_variable_type = None
                    for existing_test_variable_type in existing_test_variable_types:
                        if existing_test_variable_type.num == var_num:
                            test_variable_type = existing_test_variable_type
                            break
                    if test_variable_type:
                        logger.debug(' - UPDATE VAR %s %s %s' % (var_num, item['name'], item['name_translations']))
                        test_variable_type.write({
                            'name': item['name'],
                        })
                    else:
                        logger.debug(' - CREATE VAR %s %s %s' % (var_num, item['name'], item['name_translations']))
                        test_variable_type = TestVariableType.create({
                            'spreadsheet': self.id,
                            'test_type': test_type.id,
                            'num': var_num,
                            'name': item['name'],
                        })
                    # Translations
                    for lang, value in item['name_translations'].items():
                        logger.debug('TEST VARIABLE TRANSLATION %s: %s' % (lang, value))
                        test_variable_type.with_context(lang=lang).write({
                            'name': value,
                        })

        def save_test_type(current_test):
            #logger.debug('PROCESSING TEST %s' % (current_test))
            default_code = current_test.get('terralab.test_name', {}).get('value', None)
            if not default_code:
                raise ValidationError('Test Name Missing')
            existing_test_types = TestType.search([('spreadsheet', '=', self.id), ('default_code', '=', default_code)])
            uom_name = ''
            uom_name_obj = current_test.get('terralab.test_result_uom')
            if uom_name_obj and uom_name_obj.get('value'):
                uom_name = uom_name_obj['value']
            if len(existing_test_types) <= 0:
                logger.debug('CREATE TEST %s' % (current_test))
                test_type = TestType.create({
                    'default_code': default_code,
                    'name': default_code,
                    'spreadsheet': self.id,
                    'test_result_uom_name': uom_name,
                })
            else:
                test_type = existing_test_types[0]
                logger.debug('UPDATE TEST %s' % (test_type))
                test_type.write({
                    'name': default_code,
                    'test_result_uom_name': uom_name,
                })
            # Test has no translations (only the test variables are translated)
            save_test_variables(test_type, current_test)

        for row in rows[1:]:
            field = row[col_mapping['Field']] if col_mapping['Field'] < len(row) else None
            value = row[col_mapping['Values']] if col_mapping['Values'] < len(row) else None
            name = row[col_mapping['Name en_US']] if col_mapping['Name en_US'] < len(row) else None
            name_translations = {}
            for key, col_num in col_mapping.items():
                if key.startswith('Name '):
                    lang = key[5:]
                    name_value = row[col_num] if col_num < len(row) else None
                    #logger.debug('TRANSLATION %s %s %s' % (field, lang, name_value))
                    name_translations[lang] = name_value
            if field == 'terralab.test_name':
                # Start new test definition
                if len(current_test.keys()) > 0:
                    save_test_type(current_test)
                current_test = {}
            if field and field[0] != '#':
                current_test[field] = {
                    'value': value,
                    'name': name,
                    'name_translations': name_translations,
                }
        if len(current_test.keys()) > 0:
            save_test_type(current_test)

    def import_product_categories(self, rows):
        ProductCategory = self.env['product.category']
        logger.info('Importing %s product category row(s)' % (len(rows)))
        col_mapping = {}
        for index, col in enumerate(rows[0]):
            col_mapping[col] = index
        logger.info('Product category column mapping: %s' % (col_mapping))
        for row in rows[1:]:
            logger.debug('PRODUCT CATEGORY: %s' % (row))
            default_code = row[col_mapping['product.category_id']]
            # Check if category already exists
            existing_categories = ProductCategory.search([('terralab_spreadsheet', '=', self.id), ('terralab_default_code', '=', default_code)])
            if len(existing_categories) <= 0:
                # Create new category
                category = ProductCategory.create({
                    'terralab_default_code': default_code,
                    'terralab_spreadsheet': self.id,
                    'name': row[col_mapping['product.category_name en_US']],
                })
            else:
                # Update existing category
                category = existing_categories[0]
                category.write({
                    'name': row[col_mapping['product.category_name en_US']],
                })
            # Translations
            logger.debug('CATEGORY TRANSLATIONS: %s' % (category))
            for key, col_num in col_mapping.items():
                if key.startswith('product.category_name '):
                    lang = key[22:]
                    logger.debug('CATEGORY TRANSLATION %s: %s' % (lang, row[col_num]))
                    category.with_context(lang=lang).write({
                        'name': row[col_num],
                    })

    def import_products(self, rows):
        Product = self.env['product.template']
        ProductCategory = self.env['product.category']
        TestType = self.env['terralab.testtype']
        logger.info('Importing %s product row(s)' % (len(rows)))
        col_mapping = {}
        for index, col in enumerate(rows[0]):
            col_mapping[col] = index
        logger.info('Product column mapping: %s' % (col_mapping))

        product_map = {}
        for row in rows[1:]:
            default_code = row[col_mapping['product.default_code']]
            if not default_code in product_map:
                # First instance of product
                product_map[default_code] = {
                    'row': row,
                    'tests': [row[col_mapping['terralab.test_name']]]
                }
            else:
                # Continuing same product, just add the test name
                product_map[default_code]['tests'].append(row[col_mapping['terralab.test_name']])

        for default_code, product_def in product_map.items():
            logger.debug('PRODUCT: %s %s' % (default_code, product_def['tests']))
            row = product_def['row']

            # Lookup related tests
            test_type_ids = []
            for test_name in product_def['tests']:
                existing_test_types = TestType.search([('spreadsheet', '=', self.id), ('default_code', '=', test_name)])
                if len(existing_test_types) > 0:
                    test_type_ids.append(existing_test_types[0].id)

            # Lookup related category
            existing_categories = ProductCategory.search([('terralab_spreadsheet', '=', self.id), ('terralab_default_code', '=', row[col_mapping['product.category_id']])])
            if len(existing_categories) > 0:
                category_id = existing_categories[0].id
            else:
                category_id = None

            # Check if product already exists
            existing_products = Product.search([('terralab_spreadsheet', '=', self.id), ('default_code', '=', default_code)])
            if len(existing_products) <= 0:
                # Create new product
                product = Product.create({
                    'default_code': default_code,
                    'terralab_spreadsheet': self.id,
                    'terralab_test_types': test_type_ids,
                    'categ_id': category_id,
                    'name': row[col_mapping['product.name en_US']] if col_mapping['product.name en_US'] < len(row) else None,
                    'barcode': (row[col_mapping['product.barcode']] if col_mapping['product.barcode'] < len(row) else None) or None,
                    'list_price': row[col_mapping['product.list_price']] if col_mapping['product.list_price'] < len(row) else None,
                    'description': row[col_mapping['product.description en_US']] if col_mapping['product.description en_US'] < len(row) else None,
                })
            else:
                # Update existing category
                product = existing_products[0]
                product.write({
                    'terralab_test_types': test_type_ids,
                    'categ_id': category_id,
                    'name': row[col_mapping['product.name en_US']] if col_mapping['product.name en_US'] < len(row) else None,
                    'barcode': (row[col_mapping['product.barcode']] if col_mapping['product.barcode'] < len(row) else None) or None,
                    'list_price': row[col_mapping['product.list_price']] if col_mapping['product.list_price'] < len(row) else None,
                    'description': row[col_mapping['product.description en_US']] if col_mapping['product.description en_US'] < len(row) else None,
                })
            # Translations
            logger.debug('PRODUCT TRANSLATIONS: %s' % (product))
            for key, col_num in col_mapping.items():
                if key.startswith('product.name '):
                    lang = key[13:]
                    if col_num < len(row):
                        logger.debug('PRODUCT NAME TRANSLATION %s: %s' % (lang, row[col_num]))
                        product.with_context(lang=lang).write({
                            'name': row[col_num],
                        })
                if key.startswith('product.description '):
                    lang = key[20:]
                    if col_num < len(row):
                        logger.debug('PRODUCT DESCRIPTION TRANSLATION %s: %s' % (lang, row[col_num]))
                        product.with_context(lang=lang).write({
                            'description': row[col_num],
                        })

    def import_target_uses(self, rows):
        TargetUseType = self.env['terralab.targetusetype']
        Translation = self.env['ir.translation']
        logger.info('Importing %s target use row(s)' % (len(rows)))
        col_mapping = {}
        for index, col in enumerate(rows[0]):
            col_mapping[col] = index
        logger.info('Target use column mapping: %s' % (col_mapping))
        for row in rows[1:]:
            logger.debug('TARGET USE: %s' % (row))
            default_code = row[col_mapping['terralab.targetuse']]
            # Does this target use already exist?
            existing_target_use_types = TargetUseType.search([('spreadsheet', '=', self.id), ('default_code', '=', default_code)])
            if len(existing_target_use_types) <= 0:
                # Create new
                target_use = TargetUseType.create({
                    'default_code': default_code,
                    'spreadsheet': self.id,
                    'name': row[col_mapping['terralab.targetuse en_US']],
                })
            else:
                # Update existing
                target_use = existing_target_use_types[0]
                target_use.write({
                    'name': row[col_mapping['terralab.targetuse en_US']],
                })
            # Translations
            logger.debug('TARGET USE TRANSLATIONS: %s' % (target_use))
            for key, col_num in col_mapping.items():
                if key.startswith('terralab.targetuse '):
                    lang = key[19:]
                    logger.debug('TARGET USE TRANSLATION %s: %s' % (lang, row[col_num]))
                    target_use.with_context(lang=lang).write({
                        'name': row[col_num],
                    })


    def import_target_use_ranges(self, rows):
        TargetUseType = self.env['terralab.targetusetype']
        SubmittedTargetUse = self.env['terralab.submittedtargetuse']
        TestType = self.env['terralab.testtype']
        logger.info('Importing %s target use range row(s)' % (len(rows)))

        col_mapping = {}
        for index, col in enumerate(rows[0]):
            col_mapping[col] = index
        logger.info('Target use range mapping: %s' % (col_mapping))
        for row in rows[1:]:
            logger.debug('TARGET USE RANGE: %s' % (row))
            target_use_default_code = row[col_mapping['terralab.targetuse']]
            test_default_code = row[col_mapping['terralab.test_name']]
            # Does the referred test exist? Find it
            existing_test_types = TestType.search([('spreadsheet', '=', self.id), ('default_code', '=', test_default_code)])
            if len(existing_test_types) <= 0:
                raise ValidationError('Test Not Found: %s (while adding submitted target use)' % (test_default_code))
            existing_test_type = existing_test_types[0]
            # Does this submitted target use already exist?
            existing_target_use_types = TargetUseType.search([('spreadsheet', '=', self.id), ('default_code', '=', target_use_default_code)])
            if len(existing_target_use_types) <= 0:
                raise ValidationError('Target Use Type Not Found: %s (while adding submitted target use)' % (target_use_default_code))
            existing_target_use_type = existing_target_use_types[0]
            existing_submitted_target_types = SubmittedTargetUse.search([('spreadsheet', '=', self.id), ('target_use_type', '=', existing_target_use_type.id), ('test_type', '=', existing_test_type.id)])
            if len(existing_submitted_target_types) <= 0:
                logger.debug('SUBMITTED TARGET TYPE: %s %s' % (existing_target_use_type, existing_test_type))
                SubmittedTargetUse.create({
                    'target_use_type': existing_target_use_type.id,
                    'test_type': existing_test_type.id,
                    'threshold_1': row[col_mapping['very_low_threshold']] if col_mapping['very_low_threshold'] < len(row) else None,
                    'threshold_2': row[col_mapping['low_threshold']] if col_mapping['low_threshold'] < len(row) else None,
                    'threshold_3': row[col_mapping['ideal_value']] if col_mapping['ideal_value'] < len(row) else None,
                    'threshold_4': row[col_mapping['high_threshold']] if col_mapping['high_threshold'] < len(row) else None,
                    'threshold_5': row[col_mapping['very_high_threshold']] if col_mapping['very_high_threshold'] < len(row) else None,
                })
            else:
                logger.info('Submitted target type already exists: %s %s' % (existing_target_use_type, existing_test_type))
                existing_submitted_target_types[0].write({
                    'threshold_1': row[col_mapping['very_low_threshold']] if col_mapping['very_low_threshold'] < len(row) else None,
                    'threshold_2': row[col_mapping['low_threshold']] if col_mapping['low_threshold'] < len(row) else None,
                    'threshold_3': row[col_mapping['ideal_value']] if col_mapping['ideal_value'] < len(row) else None,
                    'threshold_4': row[col_mapping['high_threshold']] if col_mapping['high_threshold'] < len(row) else None,
                    'threshold_5': row[col_mapping['very_high_threshold']] if col_mapping['very_high_threshold'] < len(row) else None,
                })
