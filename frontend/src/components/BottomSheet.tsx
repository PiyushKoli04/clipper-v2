import React from 'react';
import { motion, AnimatePresence, PanInfo } from 'framer-motion';

interface BottomSheetProps {
  isOpen: boolean;
  onClose: () => void;
  accentColor?: string;
  children: React.ReactNode;
  title?: string;
}

export const BottomSheet: React.FC<BottomSheetProps> = ({
  isOpen,
  onClose,
  accentColor,
  children,
  title,
}) => {
  const handleDragEnd = (_: any, info: PanInfo) => {
    if (info.offset.y > 100 || info.velocity.y > 300) {
      onClose();
    }
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-end justify-center pointer-events-auto">
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-black/60 backdrop-blur-sm"
          />

          {/* Draggable Sheet */}
          <motion.div
            initial={{ y: '100%' }}
            animate={{ y: 0 }}
            exit={{ y: '100%' }}
            transition={{ type: 'spring', damping: 28, stiffness: 300 }}
            drag="y"
            dragConstraints={{ top: 0 }}
            dragElastic={0.2}
            onDragEnd={handleDragEnd}
            style={{
              background: accentColor
                ? `linear-gradient(180deg, ${accentColor}18 0%, rgba(18, 22, 28, 0.95) 25%)`
                : 'rgba(18, 22, 28, 0.95)',
            }}
            className="relative w-full max-w-lg rounded-t-[32px] border-t border-white/10 backdrop-blur-2xl shadow-glass flex flex-col max-h-[85vh] overflow-hidden pb-[env(safe-area-inset-bottom,20px)]"
          >
            {/* Drag Handle */}
            <div className="w-full flex flex-col items-center pt-3 pb-2 cursor-grab active:cursor-grabbing">
              <div className="w-12 h-1.5 rounded-full bg-white/20" />
              {title && (
                <h3 className="mt-2 text-sm font-semibold tracking-wide text-white/90">
                  {title}
                </h3>
              )}
            </div>

            {/* Content Container */}
            <div className="flex-1 overflow-y-auto px-5 pb-6 no-scrollbar">
              {children}
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
};

