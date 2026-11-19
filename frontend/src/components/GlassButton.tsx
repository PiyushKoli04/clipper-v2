import React from 'react';

interface GlassButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'glass' | 'danger';
  size?: 'sm' | 'md' | 'lg' | 'icon';
  children?: React.ReactNode;
}

export const GlassButton: React.FC<GlassButtonProps> = ({
  variant = 'primary',
  size = 'md',
  className = '',
  children,
  ...props
}) => {
  const baseStyles = 'inline-flex items-center justify-center font-semibold transition-all duration-200 active:scale-95 disabled:opacity-40 disabled:pointer-events-none select-none';

  const variants = {
    // Primary: solid white pill with black bold text
    primary: 'bg-white text-black rounded-full hover:bg-white/90 shadow-glow font-bold',
    // Secondary: circular glass icon buttons or pill
    secondary: 'glass-panel rounded-full text-white hover:bg-white/10 active:bg-white/15',
    // Glass pill
    glass: 'glass-pill text-white hover:bg-white/10',
    // Danger
    danger: 'bg-red-500/20 text-red-400 border border-red-500/30 rounded-full hover:bg-red-500/30',
  };

  const sizes = {
    sm: 'text-xs px-3.5 py-1.5 min-h-[36px]',
    md: 'text-sm px-5 py-2.5 min-h-[44px]',
    lg: 'text-base px-6 py-3 min-h-[50px]',
    icon: 'w-11 h-11 min-h-[44px] min-w-[44px] p-0 rounded-full',
  };

  return (
    <button
      className={`${baseStyles} ${variants[variant]} ${sizes[size]} ${className}`}
      {...props}
    >
      {children}
    </button>
  );
};

