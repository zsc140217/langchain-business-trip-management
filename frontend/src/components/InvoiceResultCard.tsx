import { motion } from 'framer-motion'
import { FileText, Calendar, DollarSign, Building, AlertCircle, CheckCircle, XCircle, HelpCircle, Shield } from 'lucide-react'

interface InvoiceResultCardProps {
  invoiceData: {
    amount?: number
    date?: string
    invoice_number?: string
    seller_name?: string
    buyer_name?: string
    tax_amount?: number
    verification?: {
      success: boolean
      status: 'verified' | 'failed' | 'error' | 'skipped'
      message: string
      data?: any
    }
    [key: string]: any
  }
  warnings?: string[]
}

export default function InvoiceResultCard({ invoiceData, warnings = [] }: InvoiceResultCardProps) {
  const verification = invoiceData.verification

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="travel-doc rounded-lg p-4 space-y-3 max-w-md"
    >
      {/* 标题 */}
      <div className="flex items-center gap-2 pb-2 border-b border-[var(--color-navy-lighter)]">
        <FileText size={20} className="text-[var(--color-amber)]" />
        <h3 className="font-semibold text-[var(--color-navy)]">发票识别结果</h3>
        {warnings.length === 0 ? (
          <CheckCircle size={16} className="text-green-500 ml-auto" />
        ) : (
          <AlertCircle size={16} className="text-orange-500 ml-auto" />
        )}
      </div>

      {/* 发票验真状态 */}
      {verification && (
        <div className={`p-3 rounded-lg border ${
          verification.status === 'verified'
            ? 'bg-green-50 border-green-200'
            : verification.status === 'failed'
            ? 'bg-red-50 border-red-200'
            : verification.status === 'error'
            ? 'bg-orange-50 border-orange-200'
            : 'bg-gray-50 border-gray-200'
        }`}>
          <div className="flex items-center gap-2">
            <Shield size={16} className={
              verification.status === 'verified'
                ? 'text-green-600'
                : verification.status === 'failed'
                ? 'text-red-600'
                : verification.status === 'error'
                ? 'text-orange-600'
                : 'text-gray-500'
            } />
            <span className={`text-sm font-medium ${
              verification.status === 'verified'
                ? 'text-green-700'
                : verification.status === 'failed'
                ? 'text-red-700'
                : verification.status === 'error'
                ? 'text-orange-700'
                : 'text-gray-600'
            }`}>
              {verification.status === 'verified' && (
                <span className="flex items-center gap-1">
                  <CheckCircle size={14} />
                  发票验真通过
                </span>
              )}
              {verification.status === 'failed' && (
                <span className="flex items-center gap-1">
                  <XCircle size={14} />
                  发票验真失败
                </span>
              )}
              {verification.status === 'error' && (
                <span className="flex items-center gap-1">
                  <AlertCircle size={14} />
                  验真服务异常
                </span>
              )}
              {verification.status === 'skipped' && (
                <span className="flex items-center gap-1">
                  <HelpCircle size={14} />
                  未验真
                </span>
              )}
            </span>
          </div>
          <p className={`text-xs mt-1 ${
            verification.status === 'verified'
              ? 'text-green-600'
              : verification.status === 'failed'
              ? 'text-red-600'
              : verification.status === 'error'
              ? 'text-orange-600'
              : 'text-gray-500'
          }`}>
            {verification.message}
          </p>
        </div>
      )}

      {/* 发票信息 */}
      <div className="space-y-2 text-sm">
        {/* 金额 */}
        {invoiceData.amount !== undefined && (
          <div className="flex items-center gap-2">
            <DollarSign size={16} className="text-[var(--color-navy-lighter)]" />
            <span className="text-[var(--color-navy-lighter)]">金额:</span>
            <span className="font-semibold text-[var(--color-navy)] ml-auto">
              ¥{invoiceData.amount.toFixed(2)}
            </span>
          </div>
        )}

        {/* 日期 */}
        {invoiceData.date && (
          <div className="flex items-center gap-2">
            <Calendar size={16} className="text-[var(--color-navy-lighter)]" />
            <span className="text-[var(--color-navy-lighter)]">日期:</span>
            <span className="text-[var(--color-navy)] ml-auto">{invoiceData.date}</span>
          </div>
        )}

        {/* 发票号码 */}
        {invoiceData.invoice_number && (
          <div className="flex items-center gap-2">
            <FileText size={16} className="text-[var(--color-navy-lighter)]" />
            <span className="text-[var(--color-navy-lighter)]">发票号:</span>
            <span className="text-[var(--color-navy)] ml-auto font-mono text-xs">
              {invoiceData.invoice_number}
            </span>
          </div>
        )}

        {/* 销售方 */}
        {invoiceData.seller_name && (
          <div className="flex items-center gap-2">
            <Building size={16} className="text-[var(--color-navy-lighter)]" />
            <span className="text-[var(--color-navy-lighter)]">销售方:</span>
            <span className="text-[var(--color-navy)] ml-auto text-right max-w-[200px] truncate">
              {invoiceData.seller_name}
            </span>
          </div>
        )}
      </div>

      {/* 警告信息 */}
      {warnings.length > 0 && (
        <div className="mt-3 p-3 bg-orange-50 border border-orange-200 rounded space-y-1">
          <div className="flex items-center gap-2 text-orange-700 font-medium text-sm">
            <AlertCircle size={14} />
            <span>识别提示</span>
          </div>
          <ul className="text-xs text-orange-600 space-y-1 ml-5">
            {warnings.map((warning, index) => (
              <li key={index}>{warning}</li>
            ))}
          </ul>
        </div>
      )}
    </motion.div>
  )
}
