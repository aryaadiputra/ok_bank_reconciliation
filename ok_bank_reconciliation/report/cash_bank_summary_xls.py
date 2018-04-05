# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    Copyright (c) 2009 Zikzakmedia S.L. (http://zikzakmedia.com) All Rights Reserved.
#                       Jordi Esteve <jesteve@zikzakmedia.com>
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import xlwt
from datetime import datetime
from openerp.report import report_sxw
from openerp.addons.report_xls.report_xls import report_xls
from openerp.addons.report_xls.utils import rowcol_to_cell
#from openerp.addons.account_financial_report_webkit.report.general_ledger \
#    import GeneralLedgerWebkit
from openerp.tools.translate import _
from openerp import pooler
import time

class cash_bank_summary_xls_parser(report_sxw.rml_parse):
    
    def __init__(self, cr, uid, name, context):
        super(cash_bank_summary_xls_parser, self).__init__(cr, uid, name, context=context)
        recon_obj = self.pool.get('wizz.cash.bank.summary')
        
        self.localcontext.update({
            'get_data':self.get_data,
            'get_line':self.get_line,
            'datetime': datetime,
            '_': self._,
            })
        self.context = context
    
    def get_data(self,):        
        cr, uid = self.cr, self.uid
        db_pool = pooler.get_pool(self.cr.dbname)
        #budget_pool = db_pool.get('budget.item')
        #peri_pool = db_pool.get('account.period')
        
        recon = self.pool.get('wizz.cash.bank.summary').browse(self.cr, self.uid, self.ids)
        return recon
    
    def get_line(self,start_year,start_date,end_date):
        print "get_line>>>>>>>>>>>>>>",start_year,start_date,end_date
        cr, uid = self.cr, self.uid
        db_pool = pooler.get_pool(self.cr.dbname)
        account_pool = db_pool.get('account.account')
        #peri_pool = db_pool.get('account.period')
        list = []
        data = {}
        account_search = account_pool.search(cr,uid,[('type','=','liquidity')])
        
        print "account_search>>>>>>>>>>>>>>>", account_search
        
        for account in account_pool.browse(cr,uid,account_search):
            cr.execute("select sum(debit),sum(credit) from account_move_line where account_id = %s and date >= %s and date <= %s", (account.id,start_date,end_date)), 
            print "RRRRRRRRRRRRRRRRRRRR", cr.fetchall()
        
        #recon = self.pool.get('wizz.cash.bank.summary').browse(self.cr, self.uid, self.ids)
        return list
        
        
    def _(self, src):
        lang = self.context.get('lang', 'en_US')
        
        print "translate(self.cr, _ir_translation_name, 'report', lang, src) or src", translate(self.cr, _ir_translation_name, 'report', lang, src) or src
        return translate(self.cr, _ir_translation_name, 'report', lang, src) or src

class cash_bank_summary_xls(report_xls):
    def generate_xls_report(self, _p, _xs, data, objects, wb):
        data = _p.get_data()[0]
        
        #line = _p.get_line(data['fiscalyear_id']['date_start'], data['start_date'], data['end_date'])
        
        cr, uid = self.cr, self.uid
        db_pool = pooler.get_pool(self.cr.dbname)
        account_pool = db_pool.get('account.account')
        period_pool  = db_pool.get('account.period')
        company_currency_id = data['company_id']['currency_id']['id']
        print "company_currency_id>>>>>>>>>>>>>>", company_currency_id
        
        
        report_name = _("Summary Cash & Bank")
        
        ws = wb.add_sheet(report_name[:31])
        ws.panes_frozen = True
        ws.remove_splits = True
        ws.portrait = 0  # Landscape
        ws.fit_width_to_pages = 1
        row_pos = 0
        
        ##########
        ws.col(0).width = len("ABCD")*100
        ws.col(1).width = len("ABCD")*100
        ws.col(4).width = len("ABCDEF")*1000
        ws.col(5).width = len("ABCD")*1000
        ws.col(6).width = len("ABCD")*1000
        ws.col(7).width = len("ABCDEF")*1000
        ws.col(8).width = len("ABCD")*100
        ##########
        ##Style
        title           = xlwt.easyxf('font: height 200, name Arial, colour_index black, bold on; align: horiz left;')
        title2          = xlwt.easyxf('font: height 200, name Arial, colour_index black, bold on; align: horiz centre;')
        header_tbl      = xlwt.easyxf('font: height 200, name Arial, colour_index black; align: horiz centre, vert centre; pattern: pattern solid, fore_color gray25;')
        number          = xlwt.easyxf(num_format_str='#,##0.00;(#,##0.00)')
        
        
        borderkiri      = xlwt.easyxf('borders: left thin')
        borderkanan     = xlwt.easyxf('borders: right thin')
        borderatas      = xlwt.easyxf('borders: top thin')
        borderbawah      = xlwt.easyxf('borders: bottom thin')
        ##########
        
        ws.write(2,3, data['company_id']['name'], title)
        ws.write(3,4, ": ", title)
        
        print "Filter>>>>>>>>>>",data.filter, data['period_from'], data['period_to']
        if data.filter=='date':
            ws.write(4,3, "Tanggal", title)
            ws.write(4,4, ": "+data['start_date']+" s/d "+data['end_date'], title)
        else:
            ws.write(4,3, "Periode", title)
            ws.write(4,4, ": "+data['period_from']['name']+" s/d "+data['period_to']['name'], title)
            
            #period_search period_pool.search(cr,uid,[('date_start','>=',data['period_from']['date_start']),('date_stop','>=',data['period_to']['date_stop']),(['special','=',False])])
            print "$$$$$$$$$$$$",data['fiscalyear_id']['id'], data['period_from']['id'], data['period_from']['date_start']
            cr.execute("""select id from account_period where fiscalyear_id = %s AND id != %s AND date_start <= %s""",
                       (data['fiscalyear_id']['id'],data['period_from']['id'],data['period_from']['date_start']))
            period_begining_range = tuple(map(lambda x: x[0], self.cr.fetchall()))
            
            cr.execute("""select id from account_period where special=False AND date_start >= %s AND date_stop <= %s""",
                       (data['period_from']['date_start'],data['period_to']['date_stop']))
            period_mutation_range = tuple(map(lambda x: x[0], self.cr.fetchall()))
            
            print "period_range>>>>>>>>>>", period_begining_range, period_mutation_range
        
        ws.write_merge(6,6,2,7, "Cash/ BANK Summary", title2)
        
        ws.write_merge(8,9,2,3, "Account Code", header_tbl)
        ws.write_merge(8,9,4,4, "Begining Balance", header_tbl)
        ws.write_merge(8,8,5,6, "Mutation", header_tbl)
        ws.write(9,5, "Debit", header_tbl)
        ws.write(9,6, "Credit", header_tbl)
        ws.write_merge(8,9,7,7, "Ending Balance", header_tbl)
        
        ##########
        row = 10
        account_search = account_pool.search(cr,uid,[('type','=','liquidity')], order='currency_id DESC')
        #print "OOOOOOOOOOOOOO", len(account_search)
        formula_idr_sum    = xlwt.Utils.rowcol_to_cell(0,0)
        formula_usd_sum    = xlwt.Utils.rowcol_to_cell(0,0)
        for account in account_pool.browse(cr,uid,account_search):
            
            if account.currency_id.id and account.currency_id.id <> company_currency_id:
                formula_usd_sum  = formula_usd_sum +"+"+ xlwt.Utils.rowcol_to_cell(row+1,7)
                
                ###Saldo Awal###
                    #Filter Date
                if data.filter=='date':
                    initial = 0.0
                    cr.execute("select sum(amount_currency) from account_move_line where account_id = %s and date >= %s and date < %s", (account.id,data['fiscalyear_id']['date_start'],data['start_date'])), 
                    initial = cr.fetchone()[0] or 0.0
                    
                    ###Mutasi###
                    cr.execute("""select abs(sum(case when amount_currency>0.0 then amount_currency else 0.0 end)) as debit,
                                    abs(sum(case when amount_currency<0.0 then amount_currency else 0.0 end)) as credit
                                    from account_move_line 
                                where account_id = %s and date >= %s and date <= %s
                                """, (account.id,data['start_date'],data['end_date'])), 
                    line = cr.fetchall()[0]
                    
                else:
                    #Filter Period
                    initial = 0.0
                    cr.execute("select sum(amount_currency) from account_move_line where account_id = %s and period_id in %s", (account.id,period_begining_range)), 
                    initial = cr.fetchone()[0] or 0.0
                
                    ###Mutasi###
                    cr.execute("""select abs(sum(case when amount_currency>0.0 then amount_currency else 0.0 end)) as debit,
                                    abs(sum(case when amount_currency<0.0 then amount_currency else 0.0 end)) as credit
                                    from account_move_line 
                                where account_id = %s and period_id in %s
                                """, (account.id,period_mutation_range)), 
                    line = cr.fetchall()[0]
            else:
                formula_idr_sum  = formula_idr_sum +"+"+ xlwt.Utils.rowcol_to_cell(row+1,7)
                ###Saldo Awal###
                    #Filter Date
                if data.filter=='date':
                    initial = 0.0
                    cr.execute("select sum(debit-credit) from account_move_line where account_id = %s and date >= %s and date < %s", (account.id,data['fiscalyear_id']['date_start'],data['start_date'])), 
                    initial = cr.fetchone()[0] or 0.0
                
                    ###Mutasi###
                    cr.execute("select sum(debit),sum(credit) from account_move_line where account_id = %s and date >= %s and date <= %s", (account.id,data['start_date'],data['end_date'])), 
                    line = cr.fetchall()[0]
                
                else:
                    #Filter Period
                    initial = 0.0
                    cr.execute("select sum(debit-credit) from account_move_line where account_id = %s and period_id in %s", (account.id,period_begining_range)), 
                    initial = cr.fetchone()[0] or 0.0
                
                    ###Mutasi###
                    cr.execute("select sum(debit),sum(credit) from account_move_line where account_id = %s and period_id in %s", (account.id,period_mutation_range)), 
                    line = cr.fetchall()[0]
                    
            
            ws.write_merge(row,row,2,3, account.name, )
            ws.write_merge(row+1,row+1,2,3, "Acc No. "+account.code, )
            ws.write(row+1,4, initial, number)
            ws.write(row+1,5, line[0], number)
            ws.write(row+1,6, line[1], number)
            
            cell_initial = xlwt.Utils.rowcol_to_cell(row+1,4)
            cell_debit   = xlwt.Utils.rowcol_to_cell(row+1,5)
            cell_credit  = xlwt.Utils.rowcol_to_cell(row+1,6)
            
            formula_sum  = "(%s+%s-%s)"%(cell_initial,cell_debit,cell_credit)
            ws.write(row+1,7, xlwt.Formula(formula_sum), number)
            
            row+=3
        ####Total Inactived
#         ws.write_merge(row,row+1,2,6, "TOTAL SALDO IN IDR", )
#         ws.write_merge(row,row+1,7,7, xlwt.Formula(formula_idr_sum), number)
#         row+=2
#         ws.write_merge(row,row+1,2,6, "TOTAL SALDO IN USD", )
#         ws.write_merge(row,row+1,7,7, xlwt.Formula(formula_usd_sum), number)
        ##########
        row+=2
        ws.write(row,7, (data['company_id']['city'] or "")+", "+time.strftime('%Y-%m-%d'), )
        row+=1
        #ws.write(row,2, "Mengetahui,", )
        ws.write(row,5, "Checked by,", )
        ws.write(row,7, "Created by,", )
        row+=5
        #ws.write(row,2, "Treasury Dept. Head", )
        ws.write(row,5, "Treasury Sect. Head", )
        ws.write(row,7, "Cashier", )
        
        
        #####Border###### 
        #ws.write_merge(1,row+1,0,0, "", borderkanan)
        ws.write_merge(0,0,1,8, "", borderbawah)
        ws.write_merge(row+2,row+2,1,8, "", borderatas)
        ws.write_merge(1,row+1,9,9, "", borderkiri)
        #################
        
        pass

cash_bank_summary_xls('report.cash.bank.summary.xls',
                   'wizz.cash.bank.summary',
                   parser=cash_bank_summary_xls_parser)
