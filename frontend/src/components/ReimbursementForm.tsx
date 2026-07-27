import { useState } from 'react'
import { motion } from 'framer-motion'
import { Send, Loader2, Plus, MapPin, Calendar, FileText } from 'lucide-react'
import toast from 'react-hot-toast'
import InvoiceUpload from './InvoiceUpload'
import InvoiceOCRResult from './InvoiceOCRResult'
import InvoiceList from './InvoiceList'

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001'

interface Invoice {
  invoice_id: string
  invoice_data: any
  warnings?: string[]
}

interface ReimbursementFormProps {
  onSuccess?: () => void
  onCancel?: () => void
}

export default function ReimbursementForm({
  onSuccess,
  onCancel
}: ReimbursementFormProps) {
  const [invoices, setInvoices] = useState<Invoice[]>([])
  const [currentOCRResult, setCurrentOCRResult] = useState<any>(null)
  const [showUpload, setShowUpload] = useState(true)

  // 表单字段
  const [title, setTitle] = useState('')
  const [tripDestination, setTripDestination] = useState('')
  const [tripDays, setTripDays] = useState('')
  const [tripPurpose, setTripPurpose] = useState('')
  const [remarks, setRemarks] = useState('')

  const [isSubmitting, setIsSubmitting] = useState(false)

  // 处理发票上传成功
  const handleUploadSuccess = (result: any) => {
    if (result.success) {
      const newInvoice: Invoice = {
        invoice_id: result.invoice_id,
        invoice_data: result.invoice_data,
        warnings: result.warnings || []
      }

      setInvoices((prev) => [...prev, newInvoice])
      setCurrentOCRResult(result)
      setShowUpload(false)

      // 自动填充表单标题（如果为空）
      if (!title && result.invoice_data.date) {
        const date = new Date(result.invoice_data.date)
        const month = date.getMonth() + 1
        setTitle(`${date.getFullYear()}年${month}月差旅报销`)
      }
    }
  }

  // 继续添加发票
  const handleAddMore = () => {
    setCurrentOCRResult(null)
    setShowUpload(true)
  }

  // 删除发票
  const handleRemoveInvoice = (invoiceId: string) => {
    setInvoices((prev) => prev.filter((inv) => inv.invoice_id !== invoiceId))
  }

  // 提交报销申请
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (invoices.length === 0) {
      toast.error('请至少上传一张发票')
      return
    }

    if (!title.trim()) {
      toast.error('请填写报销标题')
      return
    }

    setIsSubmitting(true)

    try {
      const token = localStorage.getItem('access_token')
      const userInfoStr = localStorage.getItem('user_info')
      const userInfo = userInfoStr ? JSON.parse(userInfoStr) : null

      // 1. 创建报销申请
      const createResponse = await fetch(`${API_BASE}/api/reimbursement/applications`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          user_id: userInfo?.user_id || 'employee',
          title: title.trim(),
          trip_destination: tripDestination.trim() || null,
          trip_days: tripDays ? parseInt(tripDays) : null,
          trip_purpose: tripPurpose.trim() || null,
          invoice_ids: invoices.map((inv) => inv.invoice_id),
          remarks: remarks.trim() || null
        }),
      })

      if (createResponse.ok) {
        const createData = await createResponse.json()

        if (createData.success) {
          // 2. 提交审批
          const submitResponse = await fetch(
            `${API_BASE}/api/reimbursement/applications/${createData.application_id}/submit?user_id=${userInfo?.user_id || 'employee'}&department=${userInfo?.department || '技术部'}`,
            {
              method: 'POST',
              headers: {
                Authorization: `Bearer ${token}`,
              },
            }
          )

          if (submitResponse.ok) {
            const submitData = await submitResponse.json()

            if (submitData.success) {
              toast.success('报销申请已提交！')

              // 显示审批信息
              if (submitData.current_approver) {
                toast.success(
                  `当前审批人: ${submitData.current_approver.approver_name}`,
                  { duration: 4000 }
                )
              }

              // 清空表单
              resetForm()

              if (onSuccess) {
                onSuccess()
              }
            } else {
              toast.error(submitData.error || '提交审批失败')
            }
          } else {
            toast.error('提交审批失败')
          }
        } else {
          toast.error(createData.error || '创建申请失败')
        }
      } else if (createResponse.status === 401) {
        toast.error('登录已过期，请重新登录')
      } else {
        toast.error('创建申请失败')
      }
    } catch (error) {
      console.error('提交错误:', error)
      toast.error('网络连接失败')
    } finally {
      setIsSubmitting(false)
    }
  }

  const resetForm = () => {
    setInvoices([])
    setCurrentOCRResult(null)
    setShowUpload(true)
    setTitle('')
    setTripDestination('')
    setTripDays('')
    setTripPurpose('')
    setRemarks('')
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="max-w-4xl mx-auto p-6 space-y-6"
    >
      {/* 页面标题 */}
      <div className="travel-doc rounded-lg p-6">
        <div className="flex items-center gap-3 mb-2">
          <FileText size={32} className="text-[var(--color-amber)]" />
          <h1 className="font-display text-3xl text-[var(--color-navy)]">发票报销申请</h1>
        </div>
        <p className="text-[var(--color-navy-lighter)]">
          上传发票图片，AI 自动识别并填充报销信息
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* 发票上传区域 */}
        <div className="travel-doc rounded-lg p-6 space-y-4">
          <h2 className="font-display text-xl text-[var(--color-navy)] flex items-center gap-2">
            <FileText size={20} />
            发票信息
          </h2>

          {/* 显示已上传的发票列表 */}
          {invoices.length > 0 && (
            <InvoiceList invoices={invoices} onRemove={handleRemoveInvoice} />
          )}

          {/* 显示当前识别结果 */}
          {currentOCRResult && (
            <div className="space-y-3">
              <InvoiceOCRResult
                invoiceId={currentOCRResult.invoice_id}
                invoiceData={currentOCRResult.invoice_data}
                warnings={currentOCRResult.warnings}
              />
              <button
                type="button"
                onClick={handleAddMore}
                className="w-full py-3 border-2 border-dashed border-[var(--color-navy-lighter)]
                         text-[var(--color-navy)] rounded-lg hover:border-[var(--color-amber)]
                         hover:bg-[var(--color-paper-dark)] transition-colors flex items-center
                         justify-center gap-2 font-medium"
              >
                <Plus size={20} />
                继续添加发票
              </button>
            </div>
          )}

          {/* 上传组件 */}
          {showUpload && (
            <InvoiceUpload
              onUploadSuccess={handleUploadSuccess}
              onRemove={() => setShowUpload(false)}
            />
          )}
        </div>

        {/* 报销信息表单 */}
        <div className="travel-doc rounded-lg p-6 space-y-4">
          <h2 className="font-display text-xl text-[var(--color-navy)] flex items-center gap-2">
            <MapPin size={20} />
            报销信息
          </h2>

          {/* 报销标题 */}
          <div>
            <label className="block text-sm font-medium text-[var(--color-navy)] mb-2">
              报销标题 <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="例如: 2026年7月北京差旅报销"
              className="w-full px-4 py-3 border-2 border-[var(--color-navy-lighter)] rounded
                       focus:outline-none focus:border-[var(--color-amber)] transition-colors
                       text-[var(--color-navy)]"
              required
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            {/* 出差目的地 */}
            <div>
              <label className="block text-sm font-medium text-[var(--color-navy)] mb-2">
                出差目的地
              </label>
              <input
                type="text"
                value={tripDestination}
                onChange={(e) => setTripDestination(e.target.value)}
                placeholder="例如: 北京市"
                className="w-full px-4 py-3 border-2 border-[var(--color-navy-lighter)] rounded
                         focus:outline-none focus:border-[var(--color-amber)] transition-colors
                         text-[var(--color-navy)]"
              />
            </div>

            {/* 出差天数 */}
            <div>
              <label className="block text-sm font-medium text-[var(--color-navy)] mb-2 flex items-center gap-1">
                <Calendar size={14} />
                出差天数
              </label>
              <input
                type="number"
                value={tripDays}
                onChange={(e) => setTripDays(e.target.value)}
                placeholder="例如: 3"
                min="1"
                className="w-full px-4 py-3 border-2 border-[var(--color-navy-lighter)] rounded
                         focus:outline-none focus:border-[var(--color-amber)] transition-colors
                         text-[var(--color-navy)]"
              />
            </div>
          </div>

          {/* 出差事由 */}
          <div>
            <label className="block text-sm font-medium text-[var(--color-navy)] mb-2">
              出差事由
            </label>
            <textarea
              value={tripPurpose}
              onChange={(e) => setTripPurpose(e.target.value)}
              placeholder="例如: 参加技术交流会"
              rows={3}
              className="w-full px-4 py-3 border-2 border-[var(--color-navy-lighter)] rounded
                       focus:outline-none focus:border-[var(--color-amber)] transition-colors
                       text-[var(--color-navy)] resize-none"
            />
          </div>

          {/* 备注 */}
          <div>
            <label className="block text-sm font-medium text-[var(--color-navy)] mb-2">
              备注
            </label>
            <textarea
              value={remarks}
              onChange={(e) => setRemarks(e.target.value)}
              placeholder="其他需要说明的信息"
              rows={2}
              className="w-full px-4 py-3 border-2 border-[var(--color-navy-lighter)] rounded
                       focus:outline-none focus:border-[var(--color-amber)] transition-colors
                       text-[var(--color-navy)] resize-none"
            />
          </div>
        </div>

        {/* 操作按钮 */}
        <div className="flex gap-4">
          {onCancel && (
            <button
              type="button"
              onClick={onCancel}
              className="flex-1 py-4 border-2 border-[var(--color-navy)] text-[var(--color-navy)]
                       rounded-lg font-semibold hover:bg-[var(--color-paper-dark)] transition-colors"
            >
              取消
            </button>
          )}
          <motion.button
            type="submit"
            disabled={isSubmitting || invoices.length === 0}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            className="flex-1 py-4 bg-[var(--color-navy)] text-[var(--color-amber)] rounded-lg
                     font-semibold hover:bg-[var(--color-navy-light)] transition-colors
                     disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            {isSubmitting ? (
              <>
                <Loader2 className="animate-spin" size={20} />
                提交中...
              </>
            ) : (
              <>
                <Send size={20} />
                提交报销申请
              </>
            )}
          </motion.button>
        </div>
      </form>
    </motion.div>
  )
}
