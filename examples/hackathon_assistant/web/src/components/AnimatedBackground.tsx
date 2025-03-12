
import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';

const AnimatedBackground = () => {
  const [mounted, setMounted] = useState(false);
  
  useEffect(() => {
    setMounted(true);
    return () => setMounted(false);
  }, []);
  
  if (!mounted) return null;
  
  return (
    <div className="fixed inset-0 -z-10 overflow-hidden">
      {/* Top gradient */}
      <div className="absolute top-0 left-0 right-0 h-[40vh] bg-gradient-to-b from-primary/5 to-transparent" />
      
      {/* Bottom gradient */}
      <div className="absolute bottom-0 left-0 right-0 h-[40vh] bg-gradient-to-t from-accent/5 to-transparent" />
      
      {/* Floating elements */}
      <FloatingElement 
        size={300}
        x={-150}
        y={100}
        duration={50}
        delay={0}
        color="primary"
        blur={70}
        opacity={0.07}
      />
      
      <FloatingElement 
        size={200}
        x={window.innerWidth - 100}
        y={200}
        duration={45}
        delay={5}
        color="accent"
        blur={60}
        opacity={0.05}
      />
      
      <FloatingElement 
        size={250}
        x={window.innerWidth / 2 - 200}
        y={window.innerHeight - 200}
        duration={60}
        delay={10}
        color="primary"
        blur={80}
        opacity={0.06}
      />
    </div>
  );
};

interface FloatingElementProps {
  size: number;
  x: number;
  y: number;
  duration: number;
  delay: number;
  color: 'primary' | 'accent';
  blur: number;
  opacity: number;
}

const FloatingElement = ({ 
  size, 
  x, 
  y, 
  duration, 
  delay, 
  color, 
  blur,
  opacity
}: FloatingElementProps) => {
  // Define the motion path
  const xVariance = 100;
  const yVariance = 80;
  
  return (
    <motion.div
      className="absolute rounded-full"
      style={{
        width: size,
        height: size,
        filter: `blur(${blur}px)`,
        background: color === 'primary' ? 'var(--primary)' : 'var(--accent)',
        opacity,
        x,
        y,
      }}
      animate={{
        x: [x, x + xVariance, x],
        y: [y, y + yVariance, y],
      }}
      transition={{
        duration,
        ease: "easeInOut",
        repeat: Infinity,
        delay,
      }}
    />
  );
};

export default AnimatedBackground;
