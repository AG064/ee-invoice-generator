import datetime
import json
import os
import pathlib
import tempfile
import unittest
import xml.etree.ElementTree as ET
from decimal import Decimal
from einvoice.generator import InvoiceData, InvoiceGenerator, InvoiceLine, PartyDetails, PaymentDetails


def sample(lines):
    return InvoiceData(
        seller=PartyDetails('12345678', 'Seller & Company', vat_number='EE123456789', address='Test street', city='Test city', email='seller@example.test', phone='123'),
        buyer=PartyDetails('87654321', 'Buyer', email='buyer@example.test'),
        invoice_number='TEST-1', invoice_date=datetime.date(2026, 10, 7),
        due_date=datetime.date(2026, 10, 21), payment=PaymentDetails('TEST-IBAN', 'TEST-BIC', bank_name='Test bank', payer_reference='TEST-1', due_days=14),
        lines=lines, notes='Test note', order_reference='TEST-ORDER')


class InvoiceTests(unittest.TestCase):
    def test_namespace_order_notes_and_totals(self):
        data = sample([InvoiceLine('Service', 3, 'h', Decimal('0.335'), Decimal('0.24'), 'Line note'), InvoiceLine('Zero rated', 1, 'pcs', 10, 0)])
        root = ET.fromstring(InvoiceGenerator(data).generate())
        ns = {'cac': InvoiceGenerator.NS_CAC, 'cbc': InvoiceGenerator.NS_CBC}
        self.assertEqual(root.tag, '{' + InvoiceGenerator.NS_INV + '}Invoice')
        self.assertEqual(root.find('cac:LegalMonetaryTotal/cbc:PayableAmount', ns).text, '11.25')
        subtotals = root.findall('cac:TaxTotal/cac:TaxSubtotal', ns)
        self.assertEqual([item.find('cbc:TaxableAmount', ns).text for item in subtotals], ['10.00', '1.01'])
        self.assertEqual(root.find('cac:InvoiceLine/cbc:Note', ns).text, 'Line note')
        self.assertEqual(root.find('cac:InvoiceLine/cbc:InvoicedQuantity', ns).get('unitCode'), 'HUR')
        totals = InvoiceGenerator.calculate_totals(data.lines)
        self.assertEqual(totals['subtotal'], 11.01)
        self.assertEqual(totals['total'], 11.25)

    def test_nonfinite_data_and_missing_lines_are_rejected(self):
        for value in [float('nan'), float('inf')]:
            with self.assertRaises(ValueError):
                InvoiceGenerator(sample([InvoiceLine('Invalid', unit_price=value)])).generate()
        with self.assertRaises(ValueError):
            InvoiceGenerator(sample([])).generate()

    def test_invalid_invoice_does_not_truncate_an_existing_export(self):
        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory) / 'invoice.xml'
            path.write_text('existing export')
            with self.assertRaises(ValueError):
                InvoiceGenerator(sample([])).save(str(path))
            self.assertEqual(path.read_text(), 'existing export')

    @unittest.skipUnless(os.environ.get('UBL_SCHEMA'), 'Set UBL_SCHEMA to the downloaded official schema')
    def test_exports_match_official_ubl_schema(self):
        from lxml import etree
        schema_path = pathlib.Path(os.environ['UBL_SCHEMA'])
        manifest_path = next(parent / 'manifest.json' for parent in schema_path.parents if (parent / 'manifest.json').exists())
        files = json.loads(manifest_path.read_text())
        class LocalSchemas(etree.Resolver):
            def resolve(self, url, pubid, context):
                if url in files:
                    return self.resolve_filename(files[url]['path'], context)
                return None
        parser = etree.XMLParser(no_network=True, resolve_entities=False)
        parser.resolvers.add(LocalSchemas())
        schema = etree.XMLSchema(etree.parse(str(schema_path), parser))
        for data in [sample([InvoiceLine('Service', 2, 'h', 10, 0.24, 'Line note')]), sample([InvoiceLine('Item', 1, 'pcs', 10, 0)])]:
            document = etree.fromstring(InvoiceGenerator(data).generate().encode('utf-8'), parser)
            self.assertTrue(schema.validate(document), str(schema.error_log))


if __name__ == '__main__':
    unittest.main()
