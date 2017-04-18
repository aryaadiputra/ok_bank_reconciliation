import time
from openerp import pooler
from openerp.osv import fields, osv

class wizz_cash_bank_summary(osv.osv_memory):
    _name = "wizz.cash.bank.summary"
    _columns = {
            'company_id'    : fields.many2one('res.company', 'Company', required=True),
            'fiscalyear_id' : fields.many2one('account.fiscalyear', 'Fiscal Year'),
            'start_date'    : fields.date('Start Date'),
            'end_date'      : fields.date('End Date'),
            'period_from'   : fields.many2one('account.period', 'Period From'),
            'period_to'     : fields.many2one('account.period', 'Period To'),
            'filter'        : fields.selection([('date','Date'),('period','Period')],'Filter')
                }
    _defaults = {
            'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'wizz.cash.bank.summary', context=c),
                 } 
    
    def create_cash_bank_report(self, cr, uid, ids, context=None):
        res = {}
        if context is None:
            context = {}
        datas = {'ids': ids}
        datas['model'] = 'wizz.cash.bank.summary'
        datas['form'] = self.read(cr, uid, ids)[0]
        return { 
            'type': 'ir.actions.report.xml',
            'report_name': 'cash.bank.summary.xls',
            'datas': datas,
                }
    
wizz_cash_bank_summary()