import { useState, useCallback } from 'react'
import { motion } from 'framer-motion'
import { Upload, X, Loader2, FileImage } from 'lucide-react'
import toast from 'react-hot-toast'

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001'

interface InvoiceUploadProps {
  onUploadSuccess: (result: any) => void
  onRemove?: () => void
  maxSize?: number // MB
}

export default function InvoiceUpload({
  onUploadSuccess,
  onRemove,
  maxSize = 10
}: InvoiceUploadProps) {
  const [isDragging, setIsDragging] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [preview, setPreview] = useState<string | null>(null)
  const [fileName, setFileName] = useState<string>('')

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
  }, [])

  const validateFile = (file: File): boolean => {
    // 检查文件类型
    const validTypes = ['image/jpeg', 'image/jpg', 'image/png', 'application/pdf']
    if (!validTypes.includes(file.type)) {
      toast.error('仅支持 JPG、PNG、PDF 格式')
      return false
    }

    // 检查文件大小
    const maxSizeBytes = maxSize * 1024 * 1024
    if (file.size > maxSizeBytes) {
      toast.error(`文件大小不能超过 ${maxSize}MB`)
      return false
    }

    return true
  }

  const uploadFile = async (file: File) => {
    if (!validateFile(file)) return

    setUploading(true)
    setFileName(file.name)

    // 生成预览图
    if (file.type.startsWith('image/')) {
      const reader = new FileReader()
      reader.onload = (e) => {
        setPreview(e.target?.result as string)
      }
      reader.readAsDataURL(file)
    }

    const formData = new FormData()
    formData.append('file', file)

    try {
      const token = localStorage.getItem('access_token')
      const response = await fetch(`${API_BASE}/api/reimbursement/upload-invoice`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
        },
        body: formData,
      })

      if (response.ok) {
        const result = await response.json()

        if (result.success) {
          toast.success('发票识别成功！')
          onUploadSuccess(result)
        } else {
          toast.error(result.error || '发票识别失败')
          resetUpload()
        }
      } else if (response.status === 401) {
        toast.error('登录已过期，请重新登录')
        resetUpload()
      } else {
        const errorData = await response.json().catch(() => ({}))
        toast.error(errorData.error || '上传失败，请重试')
        resetUpload()
      }
    } catch (error) {
      console.error('上传错误:', error)
      toast.error('网络连接失败')
      resetUpload()
    } finally {
      setUploading(false)
    }
  }

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)

    const files = Array.from(e.dataTransfer.files)
    if (files.length > 0) {
      uploadFile(files[0])
    }
  }, [])

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (files && files.length > 0) {
      uploadFile(files[0])
    }
  }

  const resetUpload = () => {
    setPreview(null)
    setFileName('')
    if (onRemove) {
      onRemove()
    }
  }

  return (
    <div className="w-full">
      {!preview ? (
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-all
            ${isDragging
              ? 'border-[var(--color-amber)] bg-[var(--color-amber)]/10 scale-105'
              : 'border-[var(--color-navy-lighter)] hover:border-[var(--color-amber)] hover:bg-[var(--color-paper-dark)]'
            }
            ${uploading ? 'pointer-events-none opacity-50' : ''}`}
        >
          <input
            type="file"
            id="invoice-upload"
            className="hidden"
            accept="image/jpeg,image/jpg,image/png,application/pdf"
            onChange={handleFileSelect}
            disabled={uploading}
          />

          <label htmlFor="invoice-upload" className="cursor-pointer block">
            {uploading ? (
              <div className="flex flex-col items-center gap-3">
                <Loader2 className="animate-spin text-[var(--color-amber)]" size={48} />
                <p className="text-lg font-medium text-[var(--color-navy)]">正在识别发票...</p>
                <p className="text-sm text-[var(--color-navy-lighter)]">请稍候，AI 正在分析发票信息</p>
              </div>
            ) : (
              <div className="flex flex-col items-center gap-3">
                <motion.div
                  whileHover={{ scale: 1.1, rotate: 5 }}
                  transition={{ type: 'spring', stiffness: 300 }}
                >
                  <Upload className="text-[var(--color-amber)]" size={48} />
                </motion.div>
                <div>
                  <p className="text-lg font-medium text-[var(--color-navy)] mb-1">
                    拖拽发票图片到此处
                  </p>
                  <p className="text-sm text-[var(--color-navy-lighter)]">
                    或点击选择文件
                  </p>
                </div>
                <div className="mt-2 text-xs text-[var(--color-navy-lighter)] space-y-1">
                  <p>支持格式：JPG、PNG、PDF</p>
                  <p>文件大小：最大 {maxSize}MB</p>
                </div>
              </div>
            )}
          </label>
        </div>
      ) : (
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="relative border-2 border-[var(--color-navy)] rounded-lg overflow-hidden"
        >
          {/* 预览图 */}
          <div className="relative bg-[var(--color-paper-dark)] p-4">
            <img
              src={preview}
              alt="发票预览"
              className="w-full h-64 object-contain rounded"
            />

            {/* 删除按钮 */}
            <button
              onClick={resetUpload}
              className="absolute top-6 right-6 p-2 bg-red-500 text-white rounded-full
                       hover:bg-red-600 transition-colors shadow-lg"
              title="删除"
            >
              <X size={20} />
            </button>
          </div>

          {/* 文件信息 */}
          <div className="p-3 bg-white border-t border-[var(--color-navy-lighter)] flex items-center gap-2">
            <FileImage size={20} className="text-[var(--color-amber)]" />
            <span className="text-sm text-[var(--color-navy)] flex-1 truncate">
              {fileName}
            </span>
            {uploading && (
              <Loader2 className="animate-spin text-[var(--color-amber)]" size={16} />
            )}
          </div>
        </motion.div>
      )}
    </div>
  )
}
