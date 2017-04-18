import logging
from datetime import datetime
from dateutil.relativedelta import relativedelta
from operator import itemgetter
import time

import openerp
from openerp import SUPERUSER_ID
from openerp import pooler, tools
from openerp.osv import fields, osv, expression
from openerp.tools.translate import _
from openerp.tools.float_utils import float_round as round

import openerp.addons.decimal_precision as dp


class bank_reconciliation(osv.osv):
    _name = 'bank.reconciliation'
    
    def create(self, cr, uid, data, context=None):
        context = dict(context or {})
        data['lock'] = True
        
        vals = super(bank_reconciliation, self).create(cr, uid, data, context=context)
        return vals
    
    def _get_balance(self, cr, uid, ids, name, args, context=None):
        res = {}
        for statement in self.browse(cr, uid, ids, context=context):
            account_id      = statement.account_id.id
            start_date      = statement.start_date
            end_date        = statement.end_date
            company_id      = statement.company_id.id
            fiscalyear_id   = statement.fiscalyear_id.id
            if statement.account_id.currency_id.id:
                cr.execute('select SUM(amount_currency) from account_move_line where account_id = %s and date < %s and company_id = %s and period_id IN (SELECT id FROM account_period WHERE fiscalyear_id IN (%s))', (account_id,start_date,company_id,fiscalyear_id))
            else:
                cr.execute('select SUM(debit-credit) from account_move_line where account_id = %s and date < %s and company_id = %s and period_id IN (SELECT id FROM account_period WHERE fiscalyear_id IN (%s))', (account_id,start_date,company_id,fiscalyear_id))
            beginning_balance = cr.fetchone()[0] or 0.0
            
            if statement.account_id.currency_id.id:
                cr.execute('select SUM(amount_currency) from account_move_line where account_id = %s and date >= %s and date <= %s and company_id = %s', (account_id,start_date, end_date,company_id,))
            else:
                cr.execute('select SUM(debit-credit) from account_move_line where account_id = %s and date >= %s and date <= %s and company_id = %s', (account_id,start_date, end_date,company_id,))
            trasaction_total = cr.fetchone()[0] or 0.0
            
            
            #####Increase Line#####
            if statement.account_id.currency_id.id:
                cr.execute('select SUM(amount_currency), count(id) from account_move_line where account_id = %s and date >= %s and date <= %s and company_id = %s and amount_currency > 0', (account_id,start_date, end_date,company_id,))
            else:
                cr.execute('select SUM(debit), count(id) from account_move_line where account_id = %s and date >= %s and date <= %s and company_id = %s', (account_id,start_date, end_date,company_id,))
            increase_line = cr.fetchone()
            
            increase_line_item = 0
            for l in statement.reconciliation_debit_line:
                increase_line_item += 1
            
            #######################
            
             #####Decrease Line#####
            if statement.account_id.currency_id.id:
                cr.execute('select SUM(amount_currency), count(id) from account_move_line where account_id = %s and date >= %s and date <= %s and company_id = %s and amount_currency < 0', (account_id,start_date, end_date,company_id,))
            else:
                cr.execute('select SUM(credit), count(id) from account_move_line where account_id = %s and date >= %s and date <= %s and company_id = %s', (account_id,start_date, end_date,company_id,))
            decrease_line = cr.fetchone()
            
            decrease_line_item = 0
            for l in statement.reconciliation_credit_line:
                decrease_line_item += 1
            
            #######################
            
            ending_balance = beginning_balance + trasaction_total 
            res[statement.id] = {
                'beginning_balance'     : beginning_balance or 0.0,
                'ending_balance'        : ending_balance or 0.0,
                
                "increase_total"        : abs(increase_line[0] or 0.0),
                "increase_line_item"    : increase_line_item,
                "decrease_total"        : abs(decrease_line[0] or 0.0),
                "decrease_line_item"    : decrease_line_item,
                
                    }
        return res
    
    _order = 'start_date desc'
    _columns = {
            'name'                      : fields.char('Description', size=264, required=True),
            'fiscalyear_id'             : fields.many2one('account.fiscalyear', 'Fiscalyear', required=True,),
            'company_id'                : fields.many2one('res.company', 'Company', required=True, readonly=False,),
            'start_date'                : fields.date("Start Date", required=True,),
            'end_date'                  : fields.date("End Date", required=True,),            
            'journal_id'                : fields.many2one('account.journal', 'Cash/ Bank', required=True, readonly=False, domain=[('type', 'in', ['cash','bank'])]),
            'account_id'                : fields.many2one('account.account', 'Account', required=True, domain=[('type', '=', 'liquidity')], readonly=True, states={'draft': [('readonly', False)]}),
            'currency_id'               : fields.many2one('res.currency', 'Currency', required=True,),
            'reconciliation_debit_line' : fields.one2many('bank.reconciliation.line', 'reconciliation_id','Reconciliation Line', domain=[('type','=','dr')]),
            'reconciliation_credit_line': fields.one2many('bank.reconciliation.line', 'reconciliation_id','Reconciliation Line', domain=[('type','=','cr')]),
            'mutation_reconciliation'   : fields.one2many('bank.reconciliation.mutation', 'reconciliation_id','Reconciliation Mutation Line'),
            
            'beginning_balance'         : fields.function(_get_balance, method=True, string='Beginning Balance', digits_compute=dp.get_precision('Account'),
                                            type='float', multi="balance"),
            'ending_balance'            : fields.function(_get_balance, method=True, string='Ending Balance', digits_compute=dp.get_precision('Account'),
                                            type='float', multi="balance"),
            
            'increase_total'            : fields.function(_get_balance, method=True, string='Deposits, Credits, and Interest', digits_compute=dp.get_precision('Account'),
                                            type='float', multi="balance"),
            'decrease_total'            : fields.function(_get_balance, method=True, string='Checks, Withdrawals, Debits, and Service Charges', digits_compute=dp.get_precision('Account'),
                                            type='float', multi="balance"),
            
            
            'increase_line_item'        : fields.function(_get_balance, method=True, string='Deposits, Credits, and Interest # of items', digits_compute=dp.get_precision('Account'),
                                            type='integer', multi="balance"),
            'decrease_line_item'        : fields.function(_get_balance, method=True, string='Checks, Withdrawals, Debits, and Service Charges # of items', digits_compute=dp.get_precision('Account'),
                                            type='integer', multi="balance"),      
            'state'                     : fields.selection([
                            ('draft', 'Open'),('close', 'Close')
                            ], 'State', readonly=True, size=32),
            'user_id'           : fields.many2one('res.users','Created By'),
            'check_by'          : fields.many2one('hr.employee',"Checked By"),
            'lock'              : fields.boolean('Lock')
                }
        
    _defaults={
            'state' :  'draft',
            'user_id': lambda s, cr, uid, c: uid,
            'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'bank.reconciliation', context=c),
               }
    
    def refresh_record(self, cr, uid, ids, context=None):
        reconciliation = self.browse(cr, uid, ids, context=None)[0]
        start_date      = reconciliation.start_date
        end_date        = reconciliation.end_date
        account_id      = reconciliation.account_id.id
        company_id      = reconciliation.company_id.id
        
        start_date, end_date, account_id, company_id
        
        move_line_obj               = self.pool.get('account.move.line')
        reconcile_line_obj          = self.pool.get('bank.reconciliation.line')
        reconcile_line_mutation_obj = self.pool.get('bank.reconciliation.mutation')
        
                            
        move_line_search = move_line_obj.search(cr, uid, [('date','>=',start_date),('date','<=',end_date), ('account_id','=',account_id), ('company_id','=',company_id)])
        move_line_browse = move_line_obj.browse(cr, uid, move_line_search)
        
        val = {'value': {'reconciliation_debit_line': [], 'reconciliation_credit_line': [], 'mutation_reconciliation':[]}}
        
        reconcile_line_ids = ids and reconcile_line_obj.search(cr, uid, [('reconciliation_id', '=', ids[0])]) or False
        reconcile_line_mutation_ids = ids and reconcile_line_mutation_obj.search(cr, uid, [('reconciliation_id', '=', ids[0])]) or False
        
        if reconcile_line_ids:
            reconcile_line_obj.unlink(cr, uid, reconcile_line_ids)
        
        if reconcile_line_mutation_ids:
            reconcile_line_mutation_obj.unlink(cr, uid, reconcile_line_mutation_ids)
        
        balance = 0.0
        for move_line in move_line_browse:
            res = {
                    'date'              : move_line.date,
                    'name'              : move_line.name,
                    'reference'         : move_line.move_id.ref,
                    'partner_id'        : move_line.partner_id.id,
                    'amount'            : abs(move_line.amount_currency or (move_line.debit-move_line.credit)),
                    'currency_id'       : move_line.currency_id.id,
                    'type'              : move_line.credit and 'cr' or 'dr',
                    'move_line_id'      : move_line.id,
                    'reconciliation_id' : reconciliation.id,
                    'status'            : True,
                    ###
                    'bank_recon_id'     : move_line.bank_recon_id,
                              }
            print "move_line.bank_recon_id", move_line.bank_recon_id
            
            debit   = abs(move_line.debit and move_line.amount_currency or move_line.debit),
            credit  = abs(move_line.credit and move_line.amount_currency or move_line.credit),
            balance = balance + debit[0] - credit[0]
            res_mutation = {
                    'date'              : move_line.date,
                    'name'              : move_line.name,
                    'reference'         : move_line.move_id.ref,
                    'partner_id'        : move_line.partner_id.id,
                    'debit'             : debit[0],
                    'credit'            : credit[0],
                    'balance'           : balance,
                    'currency_id'       : move_line.currency_id.id,
                    'type'              : move_line.credit and 'cr' or 'dr',
                    'move_line_id'      : move_line.id,
                    'reconciliation_id' : reconciliation.id,
                    'status'            : True,
                    ###
                    'bank_recon_id'     : move_line.bank_recon_id,
                        }
            
            reconcile_line_mutation_obj.create(cr, uid, res_mutation)
            reconcile_line_obj.create(cr, uid, res)
        return True
    
    def onchange_journal(self, cr, uid, ids, journal_id, context=None):
        reconciliation_line_obj = self.pool.get('bank.reconciliation.line')
        
        try:
            for recon in self.browse(cr,uid,ids,context=None):
                reconciliation_line_obj.unlink(cr, uid, [line.id for line in recon.reconciliation_debit_line], context=context)
                reconciliation_line_obj.unlink(cr, uid, [line.id for line in recon.reconciliation_credit_line], context=context)
            
            journal = self.pool.get('account.journal').browse(cr, uid, [journal_id], context=None)
            result = {}
            
            result['value'] = {
                    'account_id'    : journal.default_debit_account_id.id,
                    'start_date'    : recon.start_date,
                    'end_date'      : recon.end_date,
                    'company_id'    : recon.company_id.id,
                    'fiscalyear_id' : recon.fiscalyear_id.id,
                    'journal_id'    : journal_id,
                    'currency_id'   : journal.currency.id or recon.company_id.currency_id.id
                }
        except:
            journal = self.pool.get('account.journal').browse(cr, uid, [journal_id], context=None)
            result = {}
            
            result['value'] = {
                    'account_id'    : journal.default_debit_account_id.id,
                    }
            
        return result
    
    def onchange_reconcile(self, cr, uid, ids, start_date, end_date, account_id, company_id, fiscalyear_id,context=None):
        move_line_obj       = self.pool.get('account.move.line')
        reconcile_line_obj  = self.pool.get('bank.reconciliation.line')

        move_line_search = move_line_obj.search(cr, uid, [('date','>=',start_date),('date','<=',end_date), ('account_id','=',account_id), ('company_id','=',company_id)], order="date")
        move_line_browse = move_line_obj.browse(cr, uid, move_line_search)
        
        val = {'value': {'reconciliation_debit_line': [], 'reconciliation_credit_line': [], 'mutation_reconciliation':[]}}
        
        
        
        reconcile_line_ids = ids and reconcile_line_obj.search(cr, uid, [('reconciliation_id', '=', ids[0])]) or False
        if reconcile_line_ids:
            reconcile_line_obj.unlink(cr, uid, reconcile_line_ids)
        
        beginning_balance = 0.0
        ####for statement in self.browse(cr, uid, ids, context=context):
        
        if account_id and start_date and company_id and fiscalyear_id:
            account_currency_id = self.pool.get('account.account').browse(cr, uid, [account_id], context=None)[0].currency_id
            if account_currency_id:
                cr.execute('select SUM(amount_currency) from account_move_line where account_id = %s and date < %s and company_id = %s and period_id IN (SELECT id FROM account_period WHERE fiscalyear_id IN (%s))', (account_id,start_date,company_id,fiscalyear_id))
            else:
                cr.execute('select SUM(debit-credit) from account_move_line where account_id = %s and date < %s and company_id = %s and period_id IN (SELECT id FROM account_period WHERE fiscalyear_id IN (%s))', (account_id,start_date,company_id,fiscalyear_id))
            beginning_balance = cr.fetchone()[0] or 0.0
            
            currency_company_id = self.pool.get('res.company').browse(cr, uid, [company_id], context=None)[0].currency_id
            val['value']['currency_id'] = account_currency_id.id or currency_company_id.id
        elif account_id and company_id:
            account_currency_id = self.pool.get('account.account').browse(cr, uid, [account_id], context=None)[0].currency_id
            currency_company_id = self.pool.get('res.company').browse(cr, uid, [company_id], context=None)[0].currency_id
            
            val['value']['currency_id'] = account_currency_id.id or currency_company_id.id
        else:
            return val
        
        balance = 0.0 + beginning_balance
        
        for move_line in move_line_browse:
            #############################################
            res = {
                    'date'              : move_line.date,
                    'name'              : move_line.name,
                    'reference'         : move_line.ref,
                    'partner_id'        : move_line.partner_id.id,
                    'amount'            : abs(move_line.amount_currency or (move_line.debit-move_line.credit)),
                    'currency_id'       : move_line.currency_id.id,
                    'type'              : move_line.credit and 'cr' or 'dr',
                    'move_line_id'      : move_line.id,
                    'status'            : True,
                              }
            if res['type'] == 'cr':
                    val['value']['reconciliation_credit_line'].append(res)
            else:
                val['value']['reconciliation_debit_line'].append(res)
            ####################Mutation###########################
            
            debit   = abs(move_line.debit and move_line.amount_currency or move_line.debit),
            credit  = abs(move_line.credit and move_line.amount_currency or move_line.credit),
            balance = balance + debit[0] - credit[0]
            res_mutation = {
                    'date'              : move_line.date,
                    'name'              : move_line.name,
                    'reference'         : move_line.ref,
                    'partner_id'        : move_line.partner_id.id,
                    'debit'             : debit[0],
                    'credit'            : credit[0],
                    'balance'           : balance,
                    'currency_id'       : move_line.currency_id.id,
                    'type'              : move_line.credit and 'cr' or 'dr',
                    'move_line_id'      : move_line.id,
                    'status'            : True,
                    
                    'bank_recon_id'     : move_line.bank_recon_id,
                              }
            
            val['value']['mutation_reconciliation'].append(res_mutation)
            ##########################################################
        return val
        
    def close(self, cr, uid, ids, context=None):
        self.refresh_record(cr, uid, ids, context)
        self.write(cr, uid, ids, {'state' : 'close'}, context)
        return True
    
    def open(self, cr, uid, ids, context=None):
        self.refresh_record(cr, uid, ids, context)
        self.write(cr, uid, ids, {'state' : 'draft'}, context)
        return True
    
bank_reconciliation()


class bank_reconciliation_line(osv.osv):
    _order = 'date'
    _name = 'bank.reconciliation.line'
    _columns = {
            'reconciliation_id'     : fields.many2one('bank.reconciliation', 'Reconciliation'),
            'type'                  : fields.selection([('dr','Debit'),('cr','Credit')], 'Cr/Dr'),
            'cleared'               : fields.boolean('Cleared ?'),
            'date'                  : fields.date("Date",),
            'name'                  : fields.char('Description', size=264),
            'reference'             : fields.char('Reference', size=264),
            'partner_id'            : fields.many2one('res.partner', 'Partner'),
            'amount'                : fields.float('Amount'),
            'currency_id'           : fields.many2one('res.currency', 'Currency'),
            'research_required'     : fields.boolean('Research Required ?'),
            'move_line_id'          : fields.many2one('account.move.line', 'Journal Item'),
            'status'                : fields.boolean('Posted'),
            'account_id'            : fields.many2one('account.account', 'Account', domain = [('type', '=', 'other')]),
            'bank_recon_id'         : fields.boolean('Bank Recon Id'),
                }
    _defaults = {
            'status' : False,
                 }
    
    def posted_action(self, cr, uid, ids, context=None):
        if not context:
            context={}
            
        bank_recon_obj = self.pool.get('bank.reconciliation')
        account_obj = self.pool.get('account.account')
        analytic_obj = self.pool.get('account.analytic.account')
        move_pool = self.pool.get('account.move')
        move_line_pool = self.pool.get('account.move.line')
        seq_obj = self.pool.get('ir.sequence')
        currency_obj = self.pool.get('res.currency')
        
        
        for line in self.browse(cr, uid, ids, context=context):
            company_currency    = line.reconciliation_id.company_id.currency_id.id
            period              = self.pool.get('account.period').search(cr, uid, [('date_start','<=',line.date),('date_stop','>=',line.date)])[0],
            currency            = line.reconciliation_id.account_id.currency_id.id or line.reconciliation_id.company_id.currency_id.id 
            if line.reconciliation_id.journal_id.sequence_id:
                name = seq_obj.get_id(cr, uid, line.reconciliation_id.journal_id.sequence_id.id)
            else:
                raise osv.except_osv(_('Error !'), _('Please define a sequence on the journal !'))
            move = {
                'name': name,
                'journal_id': line.reconciliation_id.journal_id.id,
                'narration': line.reference,
                'date': line.date,
                'ref': line.reference,
                'period_id': period,
                }
            move_id = move_pool.create(cr, uid, move)
            
            amount_cr_dr = currency_obj.compute(cr, uid, currency, company_currency, line.amount, context={'date': line.date})
            
            analytic_account_id = False
            ##
            if line.type == 'cr':
                #########Increase/ Decrease Account##########
                print "period>>>>>>>>>>>>>",period
                
                move_line_debit = {
                    'name': line.name or '/',
                    'debit': amount_cr_dr,
                    'credit': 0.0,
                    'account_id': line.account_id.id,
                    'move_id': move_id,
                    'journal_id': line.reconciliation_id.journal_id.id,
                    'period_id': period[0],
                    
                    'partner_id': line.partner_id.id,
                    'currency_id': company_currency <> currency and currency or False,
                    'amount_currency': company_currency <> currency and line.amount or 0.0,
                    'date': line.date,
                    
                    'district'          : line.district_id.id,
                    'project_sub_id'    : line.project_sub_id.id,
                    'analytic_account_id': analytic_account_id,
                            }
                
                move_line_credit = {
                    'name': line.name or '/',
                    'debit': 0.0,
                    'credit': amount_cr_dr,
                    'account_id': line.reconciliation_id.account_id.id,
                    'move_id': move_id,
                    'journal_id': line.reconciliation_id.journal_id.id,
                    'period_id': period[0],
                    #'analytic_account_id': ext_pay_line.analytic_account_id.id,
                    'partner_id': line.partner_id.id,
                    'currency_id': company_currency <> currency and currency or False,
                    'amount_currency': company_currency <> currency and -line.amount or 0.0,
                    'date': line.date,
                    ###
                    'bank_recon_id' : True,
                    ###
                            }
                
                move_line_pool.create(cr, uid, move_line_debit)
                move_line_id = move_line_pool.create(cr, uid, move_line_credit)
                self.write(cr,uid,line.id,{'bank_recon_id' : True})
                
            else:
                move_line_debit = {
                    'name': line.name or '/',
                    'debit': amount_cr_dr,
                    'credit': 0.0,
                    'account_id': line.reconciliation_id.account_id.id,
                    'move_id': move_id,
                    'journal_id': line.reconciliation_id.journal_id.id,
                    'period_id': period[0],
                    #'analytic_account_id': ext_pay_line.analytic_account_id.id,
                    'partner_id': line.partner_id.id,
                    'currency_id': company_currency <> currency and currency or False,
                    'amount_currency': company_currency <> currency and line.amount or 0.0,
                    'date': line.date,
                    ###
                    'bank_recon_id' : True,
                    ###
                            }
                
                move_line_credit = {
                    'name': line.name or '/',
                    'debit': 0.0,
                    'credit': amount_cr_dr,
                    'account_id': line.account_id.id,
                    'move_id': move_id,
                    'journal_id': line.reconciliation_id.journal_id.id,
                    'period_id': period[0],
                    #'analytic_account_id': ext_pay_line.analytic_account_id.id,
                    'partner_id': line.partner_id.id,
                    'currency_id': company_currency <> currency and currency or False,
                    'amount_currency': company_currency <> currency and -line.amount or 0.0,
                    'date': line.date,
                    
                    'analytic_account_id': analytic_account_id,
                            }
                
                move_line_id = move_line_pool.create(cr, uid, move_line_debit)
                move_line_pool.create(cr, uid, move_line_credit)
                self.write(cr,uid,line.id,{'bank_recon_id' : True})
        self.write(cr, uid, ids, {'move_line_id' : move_line_id ,'status' : True}, context=None)
        bank_recon_obj.write(cr, uid, [line.reconciliation_id[0].id], {'additional_list': [(0, 0, [move_line_id])]})
        return True
    
    def cancel_action(self, cr, uid, ids, context=None):
        move_pool = self.pool.get('account.move')
        bank_reconciliation_obj = self.pool.get('bank.reconciliation')
        
        for line in self.browse(cr,uid,ids,context=None):
            if line.move_line_id:
                move_pool.button_cancel(cr, uid, [line.move_line_id.move_id.id])
                move_pool.unlink(cr, uid, [line.move_line_id.move_id.id])
                
                bank_reconciliation_obj.refresh_record(cr,uid,[line.reconciliation_id.id])
bank_reconciliation_line()

class bank_reconciliation_mutation(osv.osv):
    _order = 'date'
    _name = 'bank.reconciliation.mutation'
    _columns = {
            'reconciliation_id'     : fields.many2one('bank.reconciliation', 'Reconciliation'),
            'type'                  : fields.selection([('dr','Debit'),('cr','Credit')], 'Cr/Dr'),
            'date'                  : fields.date("Date",),
            'name'                  : fields.char('Description', size=264),
            'reference'             : fields.char('Reference', size=264),
            'partner_id'            : fields.many2one('res.partner', 'Partner'),
            'debit'                 : fields.float('Debit'),
            'credit'                : fields.float('Credit'),
            'balance'               : fields.float('Balance'),
            'currency_id'           : fields.many2one('res.currency', 'Currency'),
            'research_required'     : fields.boolean('Research Required ?'),
            'move_line_id'          : fields.many2one('account.move.line', 'Journal Item'),
            'bank_recon_id'         : fields.boolean('Bank Recon Id'),
                }
bank_reconciliation_mutation()

class account_move_line(osv.osv):
    _inherit = 'account.move.line'
    
    _columns = {
            'bank_recon_id' : fields.boolean('Bank Recon Id'),
                }
    
account_move_line()

             
            
                
                
            
    
    
    
