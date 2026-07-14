 import { motion } from 'framer-motion'
 import type { FC, SVGProps } from 'react'
 
 type IconType = FC<SVGProps<SVGSVGElement>>
 
 interface StatsCardProps {
   label: string
   value: string
   icon: IconType
   color: 'cyan' | 'purple' | 'blue'
   index: number
 }

const colorClasses = {
  cyan: {
    gradient: 'from-cyan-500 to-cyan-600',
    shadow: 'shadow-glow-md',
    glow: 'group-hover:shadow-glow-lg',
  },
  purple: {
    gradient: 'from-purple-500 to-purple-600',
    shadow: 'shadow-glow-purple',
    glow: 'group-hover:shadow-glow-purple',
  },
  blue: {
    gradient: 'from-blue-500 to-blue-600',
    shadow: 'shadow-glow-blue',
    glow: 'group-hover:shadow-glow-blue',
  },
}

export default function StatsCard({ label, value, icon: Icon, color, index }: StatsCardProps) {
  const colors = colorClasses[color]

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.5 + index * 0.1 }}
      whileHover={{ y: -5 }}
      className="group glass-card-hover p-6 relative overflow-hidden"
    >
      <div className={`absolute inset-0 bg-gradient-to-br ${colors.gradient} opacity-0 group-hover:opacity-10 transition-opacity duration-300`} />
      <div className="relative mb-4">
        <div className={`w-16 h-16 rounded-2xl bg-gradient-to-br ${colors.gradient} ${colors.shadow} flex items-center justify-center animate-float`}>
          <Icon className="w-8 h-8 text-white" />
        </div>
      </div>
      <div className="relative">
        <p className="text-4xl font-bold mb-2 gradient-text">{value}</p>
        <p className="text-gray-400 text-sm">{label}</p>
      </div>
      <div className="absolute inset-0 overflow-hidden opacity-0 group-hover:opacity-100 transition-opacity">
        <div className={`absolute inset-0 bg-gradient-to-r ${colors.gradient} opacity-20 animate-shimmer`} />
      </div>
    </motion.div>
  )
}
