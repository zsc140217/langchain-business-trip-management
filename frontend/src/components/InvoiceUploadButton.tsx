import { useState, useRef } from 'react'
import { Upload, Loader2, X } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import toast from 'react-hot-toast'

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001'

interface InvoiceUploadButtonProps {
  onUploadSuccess: (result: any) => void
  disabled?: boolean
}

export default function InvoiceUploadButton({
  onUploadSuccess,
  disabled = false
}: InvoiceUploadButtonProps) {
  const [isUploading, setIsUploading] = useState(false)
  const [preview, setPreview] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleClick = () => {
    fileInputRef.current?.click()
  }

  const handleBatchUpload = async (files: File[]) => {
    setIsUploading(true)
    const toastId = toast.loading(`批量上传中... (0/${files.length})`)

    try {
      const token = localStorage.getItem('access_token')
      const userInfoStr = localStorage.getItem('user_info')
      const userInfo = userInfoStr ? JSON.parse(userInfoStr) : null

      const results = []
      for (let i = 0; i < files.length; i++) {
        const file = files[i]
        toast.loading(`批量上传中... (${i + 1}/${files.length})`, { id: toastId })

        const formData = new FormData()
        formData.append('file', file)
        formData.append('user_id', userInfo?.user_id || 'employee')

        const response = await fetch(`${API_BASE}/api/reimbursement/upload-invoice`, {
          method: 'POST',
          headers: { Authorization: `Bearer ${token}` },
          body: formData,
        })

        if (response.ok) {
          const data = await response.json()
          if (data.success) {
            results.push(data)
          }
        }
      }

      toast.success(`成功识别 ${results.length}/${files.length} 张发票`, { id: toastId })

      // 合并所有结果
      if (results.length > 0) {
        onUploadSuccess({
          success: true,
          invoice_data: results.map(r => r.invoice_data),
          invoice_id: results.map(r => r.invoice_id).join(','),
          batch: true,
          count: results.length
        })
      }
    } catch (error) {
      console.error('批量上传错误:', error)
      toast.error('批量上传失败', { id: toastId })
    } finally {
      setIsUploading(false)
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    }
  }

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (!files || files.length === 0) return

    // 支持批量上传
    const fileArray = Array.from(files)

    // 验证文件类型（支持图片和PDF）
    const invalidFiles = fileArray.filter(f =>
      !f.type.startsWith('image/') && f.type !== 'application/pdf'
    )
    if (invalidFiles.length > 0) {
      toast.error('请上传图片或PDF文件（JPG/PNG/PDF）')
      return
    }

    // 验证文件大小 (每个文件10MB)
    const oversizedFiles = fileArray.filter(f => f.size > 10 * 1024 * 1024)
    if (oversizedFiles.length > 0) {
      toast.error('文件大小不能超过10MB')
      return
    }

    // 批量上传
    if (fileArray.length > 1) {
      await handleBatchUpload(fileArray)
      return
    }

    // 单文件上传
    const file = fileArray[0]

    // 显示预览
    const reader = new FileReader()
    reader.onload = (e) => {
      setPreview(e.target?.result as string)
    }
    reader.readAsDataURL(file)

    // 上传文件
    setIsUploading(true)

    try {
      const token = localStorage.getItem('access_token')
      const userInfoStr = localStorage.getItem('user_info')
      const userInfo = userInfoStr ? JSON.parse(userInfoStr) : null

      const formData = new FormData()
      formData.append('file', file)
      formData.append('user_id', userInfo?.user_id || 'employee')

      const response = await fetch(`${API_BASE}/api/reimbursement/upload-invoice`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
        },
        body: formData,
      })

      if (response.ok) {
        const data = await response.json()

        if (data.success) {
          toast.success('发票识别成功！')
          onUploadSuccess(data)
          setPreview(null)
        } else {
          toast.error(data.error || '发票识别失败')
        }
      } else if (response.status === 401) {
        toast.error('登录已过期，请重新登录')
      } else {
        toast.error('上传失败')
      }
    } catch (error) {
      console.error('上传错误:', error)
      toast.error('网络连接失败')
    } finally {
      setIsUploading(false)
      // 清空文件输入
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    }
  }

  const handleCancelPreview = () => {
    setPreview(null)
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  return (
    <>
      <input
        ref={fileInputRef}
        type="file"
        accept="image/*,application/pdf"
        multiple
        onChange={handleFileChange}
        className="hidden"
      />

      <motion.button
        type="button"
        onClick={handleClick}
        disabled={disabled || isUploading}
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        className="p-3 bg-[var(--color-amber)] text-[var(--color-navy)] rounded-lg
                   hover:bg-[var(--color-amber-dark)] transition-colors
                   disabled:opacity-50 disabled:cursor-not-allowed
                   flex items-center justify-center"
        title="上传发票"
      >
        {isUploading ? (
          <Loader2 className="animate-spin" size={20} />
        ) : (
          <Upload size={20} />
        )}
      </motion.button>

      {/* 预览弹窗 */}
      <AnimatePresence>
        {preview && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
            onClick={handleCancelPreview}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="relative max-w-2xl w-full bg-white rounded-lg p-4"
              onClick={(e) => e.stopPropagation()}
            >
              <button
                onClick={handleCancelPreview}
                className="absolute top-2 right-2 p-2 bg-red-500 text-white rounded-full
                         hover:bg-red-600 transition-colors"
              >
                <X size={20} />
              </button>
              <img
                src={preview}
                alt="发票预览"
                className="w-full h-auto rounded"
              />
              <div className="mt-4 text-center text-[var(--color-navy)]">
                <Loader2 className="animate-spin inline-block mr-2" size={20} />
                正在识别发票...
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  )
}
