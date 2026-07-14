 import { motion } from 'framer-motion'
 import type { FC, SVGProps } from 'react'
 
 type IconType = FC<SVGProps<SVGSVGElement>>
 
 interface FeatureCardProps {
   title: string
   description: string
   icon: IconType
   gradient: string
   index: number
 }

export default function FeatureCard({ title, description, icon: Icon, gradient, index }: FeatureCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 30 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.6 + index * 0.1 }}
      whileHover={{ scale: 1.05, rotate: 1 }}
      className="group glass-card-hover p-6 relative overflow-hidden"
    >
      <div className={`absolute inset-0 bg-gradient-to-br ${gradient} opacity-0 group-hover:opacity-10 transition-opacity duration-500`} />
      
      <div className="relative">
        <div className={`w-14 h-14 rounded-xl bg-gradient-to-br ${gradient} shadow-glow-md flex items-center justify-center mb-4 group-hover:shadow-glow-lg transition-all duration-300 animate-float`}>
          <Icon className="w-7 h-7 text-white" />
        </div>
        
        <h4 className="text-xl font-bold mb-2 text-white group-hover:gradient-text transition-all">{title}</h4>
        <p className="text-gray-400 text-sm leading-relaxed">{description}</p>
      </div>

      <div className="absolute -right-8 -bottom-8 w-32 h-32 bg-gradient-to-br from-white/5 to-transparent rounded-full blur-2xl group-hover:scale-150 transition-transform duration-500" />
    </motion.div>
  )
}
