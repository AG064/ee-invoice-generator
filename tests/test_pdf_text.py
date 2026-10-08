import ast
from io import BytesIO
from pathlib import Path
import unittest
from unittest.mock import patch
from einvoice.generator import InvoiceData
from test_invoice_xml import sample
from einvoice.generator import InvoiceLine
from reportlab.platypus import Paragraph


class PDFTextTests(unittest.TestCase):
    def test_invoice_fields_remain_literal_text_while_trusted_labels_keep_formatting(self):
        source = Path(__file__).resolve().parents[1] / 'gui/main.py'
        tree = ast.parse(source.read_text(encoding='utf-8'))
        languages = next(node.value for node in tree.body if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == 'INVOICE_LANG' for target in node.targets))
        owner = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == 'ProfessionalInvoiceGenerator')
        namespace = {'InvoiceData': InvoiceData, 'INVOICE_LANG': ast.literal_eval(languages)}
        exec(compile(ast.Module(body=[owner], type_ignores=[]), str(source), 'exec'), namespace)
        text = '<b>Literal</b> & Company'
        data = sample([InvoiceLine(text, 1, '<i>unit</i>', 10, 0)])
        data.buyer.name = text
        data.buyer.address = '<img src="file:nonexistent-pdf-fixture">'
        data.seller.name = text
        data.notes = '<b>Note</b> & text'
        data.order_reference = '<i>Ref</i>'
        data.invoice_number = '<b>INV</b>'
        data.payment.bank_name = '<b>Bank</b> & Co'
        rendered = []
        def paragraph(*args, **kwargs):
            value = Paragraph(*args, **kwargs)
            rendered.append(value.getPlainText())
            return value
        output = BytesIO()
        with patch('reportlab.platypus.Paragraph', side_effect=paragraph), patch('reportlab.lib.utils.ImageReader', side_effect=AssertionError('Invoice text must not request an image')):
            namespace['ProfessionalInvoiceGenerator'](data).build_pdf(output)
        self.assertTrue(output.getvalue().startswith(b'%PDF-'))
        self.assertGreater(len(output.getvalue()), 1000)
        for expected in [text, data.buyer.address, data.notes, data.order_reference, data.payment.bank_name, '<i>unit</i>', 'Nr. <b>INV</b>', 'BUYER']:
            self.assertIn(expected, rendered)
        self.assertNotIn('<b>BUYER</b>', rendered)


if __name__ == '__main__':
    unittest.main()
