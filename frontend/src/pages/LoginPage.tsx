import { motion } from 'framer-motion'
import { Plane, Stamp, MapPin, Compass } from 'lucide-react'
import { useState } from 'react'
import toast from 'react-hot-toast'

export default function LoginPage() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [isLoading, setIsLoading] = useState(false)

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)

    try {
      const response = await fetch('http://localhost:8002/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      })

      if (response.ok) {
        const data = await response.json()
        localStorage.setItem('access_token', data.access_token)
        toast.success('登录成功！欢迎回来')
        // Navigate to chat
        window.location.href = '/chat'
      } else {
        toast.error('用户名或密码错误')
      }
    } catch (error) {
      toast.error('网络连接失败，请稍后重试')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-4 relative overflow-hidden">
      {/* Animated Background Elements - Floating Planes */}
      <motion.div
        className="absolute top-20 left-10 text-[var(--color-amber)] opacity-10"
        animate={{
          x: [0, 100, 0],
          y: [0, -50, 0],
          rotate: [0, 10, 0],
        }}
        transition={{ duration: 20, repeat: Infinity, ease: 'easeInOut' }}
      >
        <Plane size={120} />
      </motion.div>
      <motion.div
        className="absolute bottom-20 right-10 text-[var(--color-navy)] opacity-5"
        animate={{
          x: [0, -80, 0],
          y: [0, 60, 0],
          rotate: [0, -15, 0],
        }}
        transition={{ duration: 25, repeat: Infinity, ease: 'easeInOut' }}
      >
        <Compass size={150} />
      </motion.div>

      {/* Main Login Card - Passport Style */}
      <motion.div
        initial={{ opacity: 0, y: 50, rotate: -2 }}
        animate={{ opacity: 1, y: 0, rotate: 0 }}
        transition={{ duration: 0.8, type: 'spring' }}
        className="relative max-w-md w-full"
      >
        {/* Passport Document */}
        <div className="travel-doc rounded-lg overflow-hidden ticket-edge-left ticket-edge-right">
          {/* Header - Passport Style */}
          <div className="passport-header text-center relative">
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ delay: 0.3, type: 'spring' }}
              className="inline-block"
            >
              <Plane className="inline-block mr-2" size={24} />
            </motion.div>
            <h1 className="inline-block text-xl">智旅助手 · Travel Assistant</h1>
          </div>

          {/* Barcode Decoration */}
          <div className="barcode" />

          {/* Form Content */}
          <div className="p-8 diagonal-stripes">
            {/* Stamp Badge */}
            <motion.div
              initial={{ scale: 0, rotate: -15 }}
              animate={{ scale: 1, rotate: -5 }}
              transition={{ delay: 0.5, type: 'spring' }}
              className="absolute top-24 right-8 stamp bg-white text-[var(--color-stamp-red)] text-xs font-bold z-10"
            >
              AUTHORIZED
              <br />
              <span className="text-[10px]">2026.07.15</span>
            </motion.div>

            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.6 }}
            >
              <h2 className="font-display text-3xl text-[var(--color-navy)] mb-2">
                欢迎回来
              </h2>
              <p className="text-[var(--color-navy-lighter)] mb-8 font-light">
                请登录您的出差管理账户
              </p>

              <form onSubmit={handleLogin} className="space-y-6">
                {/* Username Field */}
                <div className="relative">
                  <label className="block text-sm font-medium text-[var(--color-navy)] mb-2 uppercase tracking-wide">
                    <MapPin size={14} className="inline mr-1" />
                    用户名 / Username
                  </label>
                  <input
                    type="text"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    className="w-full px-4 py-3 bg-white border-2 border-[var(--color-navy)] rounded
                             focus:outline-none focus:border-[var(--color-amber)] transition-colors
                             font-body text-[var(--color-navy)]"
                    placeholder="employee"
                    required
                  />
                </div>

                {/* Password Field */}
                <div className="relative">
                  <label className="block text-sm font-medium text-[var(--color-navy)] mb-2 uppercase tracking-wide">
                    <Stamp size={14} className="inline mr-1" />
                    密码 / Password
                  </label>
                  <input
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full px-4 py-3 bg-white border-2 border-[var(--color-navy)] rounded
                             focus:outline-none focus:border-[var(--color-amber)] transition-colors
                             font-body text-[var(--color-navy)]"
                    placeholder="••••••••"
                    required
                  />
                </div>

                {/* Divider */}
                <div className="fold-line my-8" />

                {/* Submit Button */}
                <motion.button
                  type="submit"
                  disabled={isLoading}
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  className="w-full bg-[var(--color-navy)] text-[var(--color-amber)] py-4 rounded
                           font-display text-lg font-semibold uppercase tracking-widest
                           border-2 border-[var(--color-navy)]
                           hover:bg-[var(--color-navy-light)] transition-all
                           disabled:opacity-50 disabled:cursor-not-allowed
                           relative overflow-hidden group"
                >
                  <span className="relative z-10">
                    {isLoading ? '验证中...' : '登机 / Board'}
                  </span>
                  <motion.div
                    className="absolute inset-0 bg-[var(--color-amber)] opacity-0 group-hover:opacity-10"
                    initial={false}
                    transition={{ duration: 0.3 }}
                  />
                </motion.button>

                {/* Test Accounts Info */}
                <div className="mt-6 p-4 bg-[var(--color-paper-dark)] border border-dashed border-[var(--color-amber-dark)] rounded">
                  <p className="text-xs text-[var(--color-navy)] font-medium mb-2">
                    测试账户 / Test Accounts:
                  </p>
                  <div className="space-y-1 text-xs text-[var(--color-navy-lighter)]">
                    <p>👤 员工: employee / test123456</p>
                    <p>👔 经理: manager / test123456</p>
                    <p>💼 高管: executive / test123456</p>
                  </div>
                </div>
              </form>
            </motion.div>
          </div>

          {/* Bottom Border Decoration */}
          <div className="h-3 bg-gradient-to-r from-[var(--color-navy)] via-[var(--color-amber)] to-[var(--color-navy)]" />
        </div>

        {/* Corner Fold Effect */}
        <div className="absolute -top-2 -right-2 w-16 h-16 bg-[var(--color-paper-dark)] transform rotate-45 -z-10" />
      </motion.div>

      {/* Footer Info */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 1 }}
        className="absolute bottom-8 text-center w-full"
      >
        <p className="text-sm text-[var(--color-navy-lighter)] font-light">
          基于 LangChain 构建的智能差旅管理系统
        </p>
        <p className="text-xs text-[var(--color-amber-dark)] mt-1">
          Powered by AI · Secured by Design
        </p>
      </motion.div>
    </div>
  )
}
