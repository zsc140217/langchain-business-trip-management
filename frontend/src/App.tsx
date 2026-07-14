import { useState } from 'react'
import { motion } from 'framer-motion'
import { Sparkles, Brain, Zap, BarChart3, MessageSquare, Plane, Hotel, Cloud } from 'lucide-react'
import ChatInterface from './components/ChatInterface'
import StatsCard from './components/StatsCard'
import FeatureCard from './components/FeatureCard'

function App() {
  const [activeView, setActiveView] = useState<'home' | 'chat'>('home')

  const stats = [
    { label: '成本降低', value: '50%', icon: BarChart3, color: 'cyan' },
    { label: '响应速度', value: '4.4x', icon: Zap, color: 'purple' },
    { label: '准确率', value: '90%', icon: Brain, color: 'blue' },
  ]

  const features = [
    {
      title: '智能对话助手',
      description: '基于 LangChain 的智能对话系统，支持流式响应和多轮对话',
      icon: MessageSquare,
      gradient: 'from-cyan-500 to-blue-600',
    },
    {
      title: '航班查询',
      description: '实时查询航班信息，智能推荐最优航班和价格对比',
      icon: Plane,
      gradient: 'from-blue-500 to-purple-600',
    },
    {
      title: '酒店预订',
      description: '按城市、价格、星级筛选酒店，提供详细的设施和评分信息',
      icon: Hotel,
      gradient: 'from-purple-500 to-pink-600',
    },
    {
      title: '天气查询',
      description: '多城市天气对比，辅助差旅决策，提供实时天气预报',
      icon: Cloud,
      gradient: 'from-pink-500 to-red-600',
    },
  ]

  return (
    <div className="min-h-screen relative overflow-hidden">
      {/* Animated Background Particles */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        {[...Array(20)].map((_, i) => (
          <motion.div
            key={i}
            className="absolute w-2 h-2 bg-cyan-400/30 rounded-full"
            initial={{
              x: Math.random() * window.innerWidth,
              y: Math.random() * window.innerHeight,
            }}
            animate={{
              x: Math.random() * window.innerWidth,
              y: Math.random() * window.innerHeight,
            }}
            transition={{
              duration: Math.random() * 10 + 20,
              repeat: Infinity,
              repeatType: 'reverse',
            }}
          />
        ))}
      </div>

      {/* Navigation */}
      <nav className="relative z-10 glass-card m-4 p-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className="flex items-center gap-3"
          >
            <div className="w-12 h-12 bg-gradient-to-br from-cyan-500 to-blue-600 rounded-xl flex items-center justify-center shadow-glow-md animate-glow">
              <Sparkles className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold gradient-text">智旅助手</h1>
              <p className="text-sm text-gray-400">AI 驱动的商务出差管理系统</p>
            </div>
          </motion.div>

          <div className="flex gap-4">
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => setActiveView('home')}
              className={`px-6 py-2 rounded-xl font-medium transition-all ${
                activeView === 'home'
                  ? 'bg-gradient-to-r from-cyan-500 to-blue-600 text-white shadow-glow-md'
                  : 'bg-white/5 text-gray-300 hover:bg-white/10'
              }`}
            >
              首页
            </motion.button>
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => setActiveView('chat')}
              className={`px-6 py-2 rounded-xl font-medium transition-all ${
                activeView === 'chat'
                  ? 'bg-gradient-to-r from-cyan-500 to-blue-600 text-white shadow-glow-md'
                  : 'bg-white/5 text-gray-300 hover:bg-white/10'
              }`}
            >
              智能对话
            </motion.button>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="relative z-10 max-w-7xl mx-auto px-4 py-8">
        {activeView === 'home' ? (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
          >
            {/* Hero Section */}
            <div className="text-center mb-16">
              <motion.div
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 }}
                className="inline-block mb-6"
              >
                <div className="relative">
                  <div className="absolute inset-0 bg-gradient-to-r from-cyan-500 via-blue-500 to-purple-600 rounded-2xl blur-2xl opacity-50 animate-pulse" />
                  <div className="relative glass-card px-8 py-4">
                    <p className="text-sm font-medium gradient-text flex items-center gap-2">
                      <Sparkles className="w-4 h-4" />
                      三层智能路由 · Self-RAG · GraphRAG · 多智能体协作
                    </p>
                  </div>
                </div>
              </motion.div>

              <motion.h2
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3 }}
                className="text-6xl font-bold mb-6 gradient-text"
              >
                智能商务出差管理
              </motion.h2>

              <motion.p
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.4 }}
                className="text-xl text-gray-300 mb-12 max-w-3xl mx-auto"
              >
                基于 LangChain / LangGraph 构建的下一代企业差旅助手
                <br />
                融合 RAG、知识图谱、多智能体协作，提供极致的智能化体验
              </motion.p>

              {/* Stats */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-16">
                {stats.map((stat, index) => (
                  <StatsCard key={index} {...stat} index={index} />
                ))}
              </div>
            </div>

            {/* Features */}
            <div className="mb-16">
              <motion.h3
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.5 }}
                className="text-3xl font-bold text-center mb-12 gradient-text"
              >
                核心功能
              </motion.h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                {features.map((feature, index) => (
                  <FeatureCard key={index} {...feature} index={index} />
                ))}
              </div>
            </div>

            {/* CTA */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.7 }}
              className="text-center"
            >
              <motion.button
                whileHover={{ scale: 1.05, boxShadow: '0 0 30px rgba(6, 182, 212, 0.8)' }}
                whileTap={{ scale: 0.95 }}
                onClick={() => setActiveView('chat')}
                className="px-12 py-4 bg-gradient-to-r from-cyan-500 via-blue-500 to-purple-600 rounded-2xl text-white font-bold text-lg shadow-3d-lg hover:shadow-glow-lg transition-all animate-gradient"
              >
                开始体验智能对话
              </motion.button>
            </motion.div>
          </motion.div>
        ) : (
          <ChatInterface />
        )}
      </main>

      {/* Footer Glow Effect */}
      <div className="fixed bottom-0 left-0 right-0 h-32 bg-gradient-to-t from-cyan-500/10 via-transparent to-transparent pointer-events-none" />
    </div>
  )
}

export default App
