{
    "name" : "Cash & Bank Reconciliation",
    "version" : "1.0",
    "author" : "OdooKu",
    "category" : "Accounting",
    "website" : "http://www.odoo.com",
    'summary': 'Cash-Bank Reconciliation & Transaction',
    'currency': 'EUR',
    'price': 159,
    "description": """
Cash-Bank Reconciliation & Transaction
======================================
    Cash & Bank Reconciliation Menu
    """,
    "depends" : [
                "account","report_xls","hr","account_cancel"
                ],
    "init_xml" : [],
    "data" : [
                    "bank_reconciliation_view.xml",
                    "report/bank_reconciliation_list_xls.xml",
                    "bank_cash_summary_view.xml",
                    "report/cash_bank_summary_xls.xml",
                    ],
#     'qweb': [
#         'static/src/xml/*.xml'
#     ],
    "active": False,
    "installable": True
}