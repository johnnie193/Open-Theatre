import React, { useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { cn } from '@/lib/utils';

interface MagicParticle {
  id: string;
  x: number;
  y: number;
  vx: number;
  vy: number;
  life: number;
  maxLife: number;
  size: number;
  color: string;
}

interface MagicEffectsProps {
  isActive: boolean;
  className?: string;
  particleCount?: number;
  colors?: string[];
}

export const MagicEffects: React.FC<MagicEffectsProps> = ({
  isActive,
  className,
  particleCount = 20,
  colors = ['#3B82F6', '#8B5CF6', '#EC4899', '#F59E0B']
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const particlesRef = useRef<MagicParticle[]>([]);
  const animationRef = useRef<number>();

  useEffect(() => {
    if (!isActive) return;

    const createParticle = (): MagicParticle => {
      const container = containerRef.current;
      if (!container) return {} as MagicParticle;

      const rect = container.getBoundingClientRect();
      return {
        id: Math.random().toString(36).substr(2, 9),
        x: Math.random() * rect.width,
        y: Math.random() * rect.height,
        vx: (Math.random() - 0.5) * 2,
        vy: (Math.random() - 0.5) * 2,
        life: 0,
        maxLife: Math.random() * 100 + 50,
        size: Math.random() * 4 + 2,
        color: colors[Math.floor(Math.random() * colors.length)]
      };
    };

    const updateParticles = () => {
      particlesRef.current = particlesRef.current
        .map(particle => ({
          ...particle,
          x: particle.x + particle.vx,
          y: particle.y + particle.vy,
          life: particle.life + 1
        }))
        .filter(particle => particle.life < particle.maxLife);

      // 添加新粒�?
      if (particlesRef.current.length < particleCount) {
        particlesRef.current.push(createParticle());
      }
    };

    const animate = () => {
      updateParticles();
      animationRef.current = requestAnimationFrame(animate);
    };

    // 初始化粒�?
    particlesRef.current = Array.from({ length: particleCount }, createParticle);
    animate();

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [isActive, particleCount, colors]);

  return (
    <AnimatePresence>
      {isActive && (
        <motion.div
          ref={containerRef}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className={cn("absolute inset-0 pointer-events-none overflow-hidden", className)}
        >
          {particlesRef.current.map(particle => (
            <motion.div
              key={particle.id}
              className="absolute rounded-full"
              style={{
                left: particle.x,
                top: particle.y,
                width: particle.size,
                height: particle.size,
                backgroundColor: particle.color,
                opacity: 1 - (particle.life / particle.maxLife)
              }}
              animate={{
                scale: [1, 1.5, 1],
                rotate: [0, 180, 360]
              }}
              transition={{
                duration: 2,
                repeat: Infinity,
                ease: "easeInOut"
              }}
            />
          ))}
        </motion.div>
      )}
    </AnimatePresence>
  );
};



