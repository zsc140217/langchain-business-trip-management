import { motion, AnimatePresence } from 'framer-motion'
import { Trash2, FileText, AlertCircle } from 'lucide-react'
import toast from 'react-hot-toast'

interface Invoice {
  invoice_id: string
  invoice_data: {
    invoice_code?: string
    invoice_number?: string
    date?: string
    total?: number
    confidence?: number
    need_manual_review?: boolean
  }
  warnings?: string[]
}

interface InvoiceListProps {
  invoices: Invoice[]
  onRemove: (invoiceId: string) => void
}

export default function InvoiceList({ invoices, onRemove }: InvoiceListProps) {
  const handleRemove = (invoiceId: string) => {
    if (window.confirm('确定要删除这张发票吗？')) {
      onRemove(invoiceId)
      toast.success('发票已删除')
    }
  }

  const getTotalAmount = () => {
    return invoices.reduce((sum, inv) => sum + (inv.invoice_data.total || 0), 0)
  }

  if (invoices.length === 0) {
    return (
      <div className="text-center p-8 bg-[var(--color-paper-dark)] rounded-lg border-2 border-dashed border-[var(--color-navy-lighter)]">
        <FileText size={48} className="text-[var(--color-navy-lighter)] mx-auto mb-3" />
        <p className="text-[var(--color-navy-lighter)]">暂无发票</p>
        <p className="text-xs text-[var(--color-navy-lighter)] mt-1">
          请上传发票图片进行识别
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* 汇总信息 */}
      <div className="bg-[var(--color-navy)] text-[var(--color-paper)] p-4 rounded-lg flex items-center justify-between">
        <div>
          <p className="text-sm opacity-80">已添加发票</p>
          <p className="text-2xl font-bold">{invoices.length} 张</p>
        </div>
        <div className="text-right">
          <p className="text-sm opacity-80">合计金额</p>
          <p className="text-2xl font-bold text-[var(--color-amber)]">
            ¥{getTotalAmount().toFixed(2)}
          </p>
        </div>
      </div>

      {/* 发票列表 */}
      <div className="space-y-3">
        <AnimatePresence mode="popLayout">
          {invoices.map((invoice, index) => (
            <motion.div
              key={invoice.invoice_id}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
              transition={{ delay: index * 0.05 }}
              className="travel-doc rounded-lg p-4 relative group"
            >
              {/* 删除按钮 */}
              <button
                onClick={() => handleRemove(invoice.invoice_id)}
                className="absolute top-3 right-3 p-2 bg-red-500 text-white rounded-full
                         opacity-0 group-hover:opacity-100 transition-opacity hover:bg-red-600"
                title="删除发票"
              >
                <Trash2 size={16} />
              </button>

              <div className="flex items-start gap-4">
                {/* 序号 */}
                <div className="flex-shrink-0 w-10 h-10 bg-[var(--color-amber)] text-[var(--color-navy)]
                              rounded-full flex items-center justify-center font-bold">
                  {index + 1}
                </div>

                {/* 发票信息 */}
                <div className="flex-1 space-y-2">
                  <div className="flex items-center gap-2">
                    <FileText size={18} className="text-[var(--color-amber)]" />
                    <span className="font-semibold text-[var(--color-navy)]">
                      {invoice.invoice_data.invoice_code || '未知代码'} -
                      {invoice.invoice_data.invoice_number || '未知号码'}
                    </span>
                    {invoice.invoice_data.need_manual_review && (
                      <span className="px-2 py-1 bg-orange-100 text-orange-700 text-xs rounded font-medium">
                        需复核
                      </span>
                    )}
                  </div>

                  <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-sm">
                    <div className="flex justify-between">
                      <span className="text-[var(--color-navy-lighter)]">日期:</span>
                      <span className="font-medium text-[var(--color-navy)]">
                        {invoice.invoice_data.date || '-'}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-[var(--color-navy-lighter)]">金额:</span>
                      <span className="font-bold text-[var(--color-amber)]">
                        ¥{invoice.invoice_data.total?.toFixed(2) || '0.00'}
                      </span>
                    </div>
                    <div className="flex justify-between col-span-2">
                      <span className="text-[var(--color-navy-lighter)]">置信度:</span>
                      <span className={`font-medium ${
                        (invoice.invoice_data.confidence || 0) >= 0.8
                          ? 'text-green-600'
                          : 'text-orange-600'
                      }`}>
                        {((invoice.invoice_data.confidence || 0) * 100).toFixed(1)}%
                      </span>
                    </div>
                  </div>

                  {/* 警告信息 */}
                  {invoice.warnings && invoice.warnings.length > 0 && (
                    <div className="mt-2 p-2 bg-yellow-50 border-l-2 border-yellow-400 rounded text-xs">
                      <div className="flex items-start gap-1">
                        <AlertCircle size={14} className="text-yellow-600 mt-0.5 flex-shrink-0" />
                        <span className="text-yellow-800">
                          {invoice.warnings.join('; ')}
                        </span>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </div>
  )
}
