import { motion } from 'framer-motion'
import { CheckCircle, AlertTriangle, FileText, Calendar, DollarSign } from 'lucide-react'

interface InvoiceData {
  invoice_code?: string
  invoice_number?: string
  date?: string
  total?: number
  tax?: number
  amount?: number
  seller_name?: string
  buyer_name?: string
  confidence?: number
  need_manual_review?: boolean
}

interface InvoiceOCRResultProps {
  invoiceId: string
  invoiceData: InvoiceData
  warnings?: string[]
}

export default function InvoiceOCRResult({
  invoiceId,
  invoiceData,
  warnings = []
}: InvoiceOCRResultProps) {
  const confidence = invoiceData.confidence || 0
  const needReview = invoiceData.need_manual_review || confidence < 0.8

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="travel-doc rounded-lg overflow-hidden"
    >
      {/* 头部 */}
      <div className="bg-[var(--color-navy)] text-[var(--color-paper)] p-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <FileText size={24} />
          <div>
            <h3 className="font-display text-lg">识别结果</h3>
            <p className="text-xs opacity-80">发票ID: {invoiceId}</p>
          </div>
        </div>

        {/* 置信度指示器 */}
        <div className="text-right">
          <div className="flex items-center gap-2 mb-1">
            {needReview ? (
              <AlertTriangle size={20} className="text-[var(--color-amber)]" />
            ) : (
              <CheckCircle size={20} className="text-green-400" />
            )}
            <span className="text-sm font-medium">
              {needReview ? '需要复核' : '识别成功'}
            </span>
          </div>
          <div className="text-xs opacity-80">
            置信度: {(confidence * 100).toFixed(1)}%
          </div>
        </div>
      </div>

      {/* 发票信息 */}
      <div className="p-6 space-y-4">
        <div className="grid grid-cols-2 gap-4">
          {/* 发票代码 */}
          <div className="space-y-1">
            <label className="text-xs font-medium text-[var(--color-navy-lighter)] uppercase">
              发票代码
            </label>
            <div className="text-base font-semibold text-[var(--color-navy)]">
              {invoiceData.invoice_code || '-'}
            </div>
          </div>

          {/* 发票号码 */}
          <div className="space-y-1">
            <label className="text-xs font-medium text-[var(--color-navy-lighter)] uppercase">
              发票号码
            </label>
            <div className="text-base font-semibold text-[var(--color-navy)]">
              {invoiceData.invoice_number || '-'}
            </div>
          </div>

          {/* 开票日期 */}
          <div className="space-y-1">
            <label className="text-xs font-medium text-[var(--color-navy-lighter)] uppercase flex items-center gap-1">
              <Calendar size={12} />
              开票日期
            </label>
            <div className="text-base font-semibold text-[var(--color-navy)]">
              {invoiceData.date || '-'}
            </div>
          </div>

          {/* 价税合计 */}
          <div className="space-y-1">
            <label className="text-xs font-medium text-[var(--color-navy-lighter)] uppercase flex items-center gap-1">
              <DollarSign size={12} />
              价税合计
            </label>
            <div className="text-xl font-bold text-[var(--color-amber)]">
              ¥{invoiceData.total?.toFixed(2) || '0.00'}
            </div>
          </div>
        </div>

        <div className="fold-line my-4" />

        {/* 详细信息 */}
        <div className="space-y-3 text-sm">
          <div className="flex justify-between">
            <span className="text-[var(--color-navy-lighter)]">金额:</span>
            <span className="font-medium text-[var(--color-navy)]">
              ¥{invoiceData.amount?.toFixed(2) || '0.00'}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-[var(--color-navy-lighter)]">税额:</span>
            <span className="font-medium text-[var(--color-navy)]">
              ¥{invoiceData.tax?.toFixed(2) || '0.00'}
            </span>
          </div>
          {invoiceData.seller_name && (
            <div className="flex justify-between">
              <span className="text-[var(--color-navy-lighter)]">销售方:</span>
              <span className="font-medium text-[var(--color-navy)] text-right max-w-xs truncate">
                {invoiceData.seller_name}
              </span>
            </div>
          )}
          {invoiceData.buyer_name && (
            <div className="flex justify-between">
              <span className="text-[var(--color-navy-lighter)]">购买方:</span>
              <span className="font-medium text-[var(--color-navy)] text-right max-w-xs truncate">
                {invoiceData.buyer_name}
              </span>
            </div>
          )}
        </div>

        {/* 警告信息 */}
        {warnings.length > 0 && (
          <div className="mt-4 p-3 bg-yellow-50 border-l-4 border-yellow-400 rounded">
            <div className="flex items-start gap-2">
              <AlertTriangle size={18} className="text-yellow-600 mt-0.5 flex-shrink-0" />
              <div className="flex-1">
                <p className="text-sm font-medium text-yellow-800 mb-1">提示信息</p>
                <ul className="text-xs text-yellow-700 space-y-1">
                  {warnings.map((warning, index) => (
                    <li key={index}>• {warning}</li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        )}

        {/* 需要复核提示 */}
        {needReview && (
          <div className="mt-4 p-3 bg-orange-50 border-l-4 border-orange-400 rounded">
            <div className="flex items-start gap-2">
              <AlertTriangle size={18} className="text-orange-600 mt-0.5" />
              <div className="flex-1">
                <p className="text-sm font-medium text-orange-800">需要人工复核</p>
                <p className="text-xs text-orange-700 mt-1">
                  识别置信度较低（{(confidence * 100).toFixed(1)}%），请仔细核对发票信息
                </p>
              </div>
            </div>
          </div>
        )}
      </div>
    </motion.div>
  )
}
