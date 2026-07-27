import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { FileText, Calendar, DollarSign, Clock, CheckCircle, XCircle, ChevronDown, ChevronUp, MapPin, Download, Loader2 } from 'lucide-react'
import toast from 'react-hot-toast'

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001'

interface Approver {
  approver_name: string
  approver_id: string
  role: string
  approved_at?: string
  status: 'pending' | 'approved' | 'rejected'
}

interface ApplicationDetail {
  application_id: string
  title: string
  total_amount: number
  status: 'pending' | 'approved' | 'rejected'
  created_at: string
  destination?: string
  days?: number
  reason?: string
  current_approver?: Approver
  approval_chain?: Approver[]
  invoices?: Array<{
    invoice_id: string
    invoice_number: string
    amount: number
    date: string
    vendor: string
  }>
}

interface Application {
  application_id: string
  title: string
  total_amount: number
  status: 'pending' | 'approved' | 'rejected'
  created_at: string
  current_approver?: {
    approver_name: string
  }
}

export default function ReimbursementHistory() {
  const [applications, setApplications] = useState<Application[]>([])
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [selectedDetail, setSelectedDetail] = useState<ApplicationDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [detailLoading, setDetailLoading] = useState(false)
  const [downloadingId, setDownloadingId] = useState<string | null>(null)

  useEffect(() => {
    fetchApplications()
  }, [])

  const fetchApplications = async () => {
    try {
      const token = localStorage.getItem('access_token')
      const userInfoStr = localStorage.getItem('user_info')
      const userInfo = userInfoStr ? JSON.parse(userInfoStr) : null

      if (!userInfo?.user_id) {
        toast.error('用户信息缺失，请重新登录')
        return
      }

      const response = await fetch(
        `${API_BASE}/api/reimbursement/applications?user_id=${userInfo.user_id}`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      )

      if (response.ok) {
        const data = await response.json()
        setApplications(data.applications || [])
      } else if (response.status === 401) {
        toast.error('登录已过期，请重新登录')
      } else {
        toast.error('加载报销记录失败')
      }
    } catch (error) {
      toast.error('网络连接失败')
      console.error(error)
    } finally {
      setLoading(false)
    }
  }

  const fetchApplicationDetail = async (applicationId: string) => {
    setDetailLoading(true)
    try {
      const token = localStorage.getItem('access_token')

      const response = await fetch(
        `${API_BASE}/api/reimbursement/applications/${applicationId}`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      )

      if (response.ok) {
        const data = await response.json()
        setSelectedDetail(data)
      } else {
        toast.error('加载详情失败')
      }
    } catch (error) {
      toast.error('网络连接失败')
      console.error(error)
    } finally {
      setDetailLoading(false)
    }
  }

  const downloadPDF = async (applicationId: string, title: string) => {
    setDownloadingId(applicationId)
    try {
      const token = localStorage.getItem('access_token')
      const response = await fetch(
        `${API_BASE}/api/reimbursement/applications/${applicationId}/pdf`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      )

      if (response.ok) {
        const blob = await response.blob()
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `${title}-${applicationId}.pdf`
        document.body.appendChild(a)
        a.click()
        document.body.removeChild(a)
        window.URL.revokeObjectURL(url)
        toast.success('PDF下载成功')
      } else {
        toast.error('PDF下载失败')
      }
    } catch (error) {
      toast.error('网络连接失败')
      console.error(error)
    } finally {
      setDownloadingId(null)
    }
  }

  const toggleDetail = async (applicationId: string) => {
    if (selectedId === applicationId) {
      setSelectedId(null)
      setSelectedDetail(null)
    } else {
      setSelectedId(applicationId)
      await fetchApplicationDetail(applicationId)
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'approved':
        return <CheckCircle className="text-green-500" size={24} />
      case 'pending':
        return <Clock className="text-yellow-500" size={24} />
      case 'rejected':
        return <XCircle className="text-red-500" size={24} />
      default:
        return <Clock className="text-gray-400" size={24} />
    }
  }

  const getStatusText = (status: string) => {
    switch (status) {
      case 'approved':
        return '已通过'
      case 'pending':
        return '审批中'
      case 'rejected':
        return '已驳回'
      default:
        return '未知'
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'approved':
        return 'bg-green-100 text-green-800 border-green-300'
      case 'pending':
        return 'bg-yellow-100 text-yellow-800 border-yellow-300'
      case 'rejected':
        return 'bg-red-100 text-red-800 border-red-300'
      default:
        return 'bg-gray-100 text-gray-800 border-gray-300'
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="animate-spin text-[var(--color-amber)]" size={48} />
      </div>
    )
  }

  return (
    <div className="p-6 space-y-4 max-w-6xl mx-auto">
      <div className="travel-doc p-6 rounded-lg corner-fold">
        <h1 className="font-display text-3xl text-[var(--color-navy)] mb-2 flex items-center gap-3">
          <FileText size={32} />
          历史报销查询
        </h1>
        <p className="text-[var(--color-navy-lighter)]">
          查看您的所有报销记录和审批状态
        </p>
      </div>

      {applications.length === 0 ? (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="travel-doc p-12 rounded-lg text-center"
        >
          <FileText size={64} className="text-[var(--color-amber)] mx-auto mb-4 opacity-50" />
          <p className="text-[var(--color-navy-lighter)] text-lg">
            暂无报销记录
          </p>
        </motion.div>
      ) : (
        <div className="space-y-3">
          {applications.map((app) => (
            <motion.div
              key={app.application_id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="travel-doc rounded-lg overflow-hidden"
            >
              {/* Summary Row */}
              <div className="p-4">
                <div className="flex items-center justify-between gap-4">
                  <div className="flex items-center gap-4 flex-1">
                    {getStatusIcon(app.status)}

                    <div className="flex-1">
                      <h3 className="font-semibold text-[var(--color-navy)] text-lg">
                        {app.title}
                      </h3>
                      <div className="flex items-center gap-4 text-sm text-[var(--color-navy-lighter)] mt-1">
                        <span className="flex items-center gap-1">
                          <Calendar size={14} />
                          {new Date(app.created_at).toLocaleDateString('zh-CN', {
                            year: 'numeric',
                            month: '2-digit',
                            day: '2-digit',
                          })}
                        </span>
                        <span className="flex items-center gap-1">
                          <DollarSign size={14} />
                          {app.total_amount.toFixed(2)} 元
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-3">
                    <span
                      className={`px-3 py-1 rounded-full text-sm font-medium border ${getStatusColor(
                        app.status
                      )}`}
                    >
                      {getStatusText(app.status)}
                    </span>

                    <button
                      onClick={() => downloadPDF(app.application_id, app.title)}
                      disabled={downloadingId === app.application_id}
                      className="px-4 py-2 bg-[var(--color-navy)] text-[var(--color-amber)] rounded
                               hover:bg-[var(--color-navy-light)] transition-colors
                               disabled:opacity-50 disabled:cursor-not-allowed
                               flex items-center gap-2 text-sm font-medium"
                    >
                      {downloadingId === app.application_id ? (
                        <>
                          <Loader2 className="animate-spin" size={16} />
                          下载中...
                        </>
                      ) : (
                        <>
                          <Download size={16} />
                          下载PDF
                        </>
                      )}
                    </button>

                    <button
                      onClick={() => toggleDetail(app.application_id)}
                      className="p-2 hover:bg-[var(--color-paper-dark)] rounded transition-colors"
                    >
                      {selectedId === app.application_id ? (
                        <ChevronUp size={20} className="text-[var(--color-navy)]" />
                      ) : (
                        <ChevronDown size={20} className="text-[var(--color-navy)]" />
                      )}
                    </button>
                  </div>
                </div>

                {app.current_approver && app.status === 'pending' && (
                  <div className="mt-3 pt-3 border-t border-[var(--color-navy)]/10">
                    <p className="text-sm text-[var(--color-navy-lighter)]">
                      当前审批人：
                      <span className="font-medium text-[var(--color-navy)] ml-1">
                        {app.current_approver.approver_name}
                      </span>
                    </p>
                  </div>
                )}
              </div>

              {/* Detail Panel */}
              <AnimatePresence>
                {selectedId === app.application_id && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: 'auto', opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    transition={{ duration: 0.3 }}
                    className="border-t-2 border-[var(--color-navy)]/10 bg-[var(--color-paper-dark)]"
                  >
                    {detailLoading ? (
                      <div className="p-8 flex items-center justify-center">
                        <Loader2 className="animate-spin text-[var(--color-amber)]" size={32} />
                      </div>
                    ) : selectedDetail ? (
                      <div className="p-6 space-y-6">
                        {/* Trip Info */}
                        {(selectedDetail.destination || selectedDetail.days || selectedDetail.reason) && (
                          <div>
                            <h4 className="font-semibold text-[var(--color-navy)] mb-3 flex items-center gap-2">
                              <MapPin size={18} />
                              出差信息
                            </h4>
                            <div className="grid grid-cols-3 gap-4 bg-white p-4 rounded border border-[var(--color-navy)]/10">
                              {selectedDetail.destination && (
                                <div>
                                  <p className="text-xs text-[var(--color-navy-lighter)] mb-1">
                                    目的地
                                  </p>
                                  <p className="text-sm font-medium text-[var(--color-navy)]">
                                    {selectedDetail.destination}
                                  </p>
                                </div>
                              )}
                              {selectedDetail.days && (
                                <div>
                                  <p className="text-xs text-[var(--color-navy-lighter)] mb-1">
                                    天数
                                  </p>
                                  <p className="text-sm font-medium text-[var(--color-navy)]">
                                    {selectedDetail.days} 天
                                  </p>
                                </div>
                              )}
                              {selectedDetail.reason && (
                                <div className="col-span-3">
                                  <p className="text-xs text-[var(--color-navy-lighter)] mb-1">
                                    出差事由
                                  </p>
                                  <p className="text-sm text-[var(--color-navy)]">
                                    {selectedDetail.reason}
                                  </p>
                                </div>
                              )}
                            </div>
                          </div>
                        )}

                        {/* Invoices */}
                        {selectedDetail.invoices && selectedDetail.invoices.length > 0 && (
                          <div>
                            <h4 className="font-semibold text-[var(--color-navy)] mb-3 flex items-center gap-2">
                              <FileText size={18} />
                              发票列表 ({selectedDetail.invoices.length})
                            </h4>
                            <div className="space-y-2">
                              {selectedDetail.invoices.map((invoice) => (
                                <div
                                  key={invoice.invoice_id}
                                  className="bg-white p-3 rounded border border-[var(--color-navy)]/10
                                           flex items-center justify-between"
                                >
                                  <div className="flex-1 grid grid-cols-4 gap-4 text-sm">
                                    <div>
                                      <p className="text-xs text-[var(--color-navy-lighter)]">
                                        发票号
                                      </p>
                                      <p className="font-medium text-[var(--color-navy)]">
                                        {invoice.invoice_number}
                                      </p>
                                    </div>
                                    <div>
                                      <p className="text-xs text-[var(--color-navy-lighter)]">
                                        开票方
                                      </p>
                                      <p className="text-[var(--color-navy)]">{invoice.vendor}</p>
                                    </div>
                                    <div>
                                      <p className="text-xs text-[var(--color-navy-lighter)]">
                                        日期
                                      </p>
                                      <p className="text-[var(--color-navy)]">
                                        {new Date(invoice.date).toLocaleDateString('zh-CN')}
                                      </p>
                                    </div>
                                    <div>
                                      <p className="text-xs text-[var(--color-navy-lighter)]">
                                        金额
                                      </p>
                                      <p className="font-semibold text-[var(--color-navy)]">
                                        ¥{invoice.amount.toFixed(2)}
                                      </p>
                                    </div>
                                  </div>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* Approval Chain */}
                        {selectedDetail.approval_chain && selectedDetail.approval_chain.length > 0 && (
                          <div>
                            <h4 className="font-semibold text-[var(--color-navy)] mb-3">
                              审批流程
                            </h4>
                            <div className="space-y-2">
                              {selectedDetail.approval_chain.map((approver, index) => (
                                <div
                                  key={index}
                                  className="bg-white p-4 rounded border border-[var(--color-navy)]/10
                                           flex items-center justify-between"
                                >
                                  <div className="flex items-center gap-3">
                                    <div
                                      className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold
                                        ${
                                          approver.status === 'approved'
                                            ? 'bg-green-100 text-green-700'
                                            : approver.status === 'pending'
                                            ? 'bg-yellow-100 text-yellow-700'
                                            : 'bg-red-100 text-red-700'
                                        }`}
                                    >
                                      {index + 1}
                                    </div>
                                    <div>
                                      <p className="font-medium text-[var(--color-navy)]">
                                        {approver.approver_name}
                                      </p>
                                      <p className="text-xs text-[var(--color-navy-lighter)]">
                                        {approver.role}
                                      </p>
                                    </div>
                                  </div>
                                  <div className="flex items-center gap-3">
                                    {approver.approved_at && (
                                      <span className="text-xs text-[var(--color-navy-lighter)]">
                                        {new Date(approver.approved_at).toLocaleString('zh-CN')}
                                      </span>
                                    )}
                                    {getStatusIcon(approver.status)}
                                  </div>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    ) : (
                      <div className="p-8 text-center text-[var(--color-navy-lighter)]">
                        加载详情失败
                      </div>
                    )}
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
          ))}
        </div>
      )}
    </div>
  )
}
