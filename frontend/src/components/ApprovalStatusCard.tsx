import { motion } from 'framer-motion'
import { CheckCircle, Clock, XCircle, User, Calendar } from 'lucide-react'

interface ApprovalStatusCardProps {
  status: 'pending' | 'approved' | 'rejected' | 'in_progress'
  currentApprover?: {
    approver_name: string
    approver_role?: string
  }
  applicationId?: string
  submittedAt?: string
}

export default function ApprovalStatusCard({
  status,
  currentApprover,
  applicationId,
  submittedAt
}: ApprovalStatusCardProps) {
  // 状态配置
  const statusConfig = {
    pending: {
      icon: Clock,
      color: 'text-yellow-600',
      bgColor: 'bg-yellow-50',
      borderColor: 'border-yellow-200',
      label: '待审批',
      description: '您的报销申请已提交，等待审批'
    },
    in_progress: {
      icon: Clock,
      color: 'text-blue-600',
      bgColor: 'bg-blue-50',
      borderColor: 'border-blue-200',
      label: '审批中',
      description: '报销申请正在审批中'
    },
    approved: {
      icon: CheckCircle,
      color: 'text-green-600',
      bgColor: 'bg-green-50',
      borderColor: 'border-green-200',
      label: '已通过',
      description: '您的报销申请已通过审批'
    },
    rejected: {
      icon: XCircle,
      color: 'text-red-600',
      bgColor: 'bg-red-50',
      borderColor: 'border-red-200',
      label: '已驳回',
      description: '您的报销申请被驳回'
    }
  }

  const config = statusConfig[status]
  const Icon = config.icon

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className={`travel-doc rounded-lg p-4 space-y-3 max-w-md border-2 ${config.borderColor} ${config.bgColor}`}
    >
      {/* 状态标题 */}
      <div className="flex items-center gap-2 pb-2 border-b border-[var(--color-navy-lighter)]">
        <Icon size={20} className={config.color} />
        <h3 className={`font-semibold ${config.color}`}>{config.label}</h3>
      </div>

      {/* 描述 */}
      <p className="text-sm text-[var(--color-navy)]">{config.description}</p>

      {/* 当前审批人 */}
      {currentApprover && (status === 'pending' || status === 'in_progress') && (
        <div className="flex items-start gap-2 p-3 bg-white rounded border border-[var(--color-navy-lighter)]">
          <User size={16} className="text-[var(--color-navy-lighter)} mt-0.5" />
          <div className="flex-1 text-sm">
            <div className="text-[var(--color-navy-lighter)]">当前审批人</div>
            <div className="font-semibold text-[var(--color-navy)] mt-1">
              {currentApprover.approver_name}
              {currentApprover.approver_role && (
                <span className="ml-2 text-xs text-[var(--color-navy-lighter)} font-normal">
                  ({currentApprover.approver_role})
                </span>
              )}
            </div>
          </div>
        </div>
      )}

      {/* 申请信息 */}
      <div className="space-y-1 text-xs text-[var(--color-navy-lighter)]">
        {applicationId && (
          <div className="flex items-center gap-2">
            <span>申请编号:</span>
            <span className="font-mono">{applicationId.substring(0, 12)}...</span>
          </div>
        )}
        {submittedAt && (
          <div className="flex items-center gap-2">
            <Calendar size={12} />
            <span>提交时间:</span>
            <span>{new Date(submittedAt).toLocaleString('zh-CN')}</span>
          </div>
        )}
      </div>
    </motion.div>
  )
}
