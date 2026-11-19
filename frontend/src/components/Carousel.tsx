import React, { useEffect, useState, useCallback } from 'react';
import useEmblaCarousel from 'embla-carousel-react';
import { Clip } from '../types';
import { ClipCard } from './ClipCard';

interface CarouselProps {
  clips: Clip[];
  onSelectClip: (clip: Clip) => void;
}

export const Carousel: React.FC<CarouselProps> = ({ clips, onSelectClip }) => {
  const [emblaRef, emblaApi] = useEmblaCarousel({
    loop: false,
    align: 'center',
    skipSnaps: false,
    containScroll: false,
  });

  const [selectedIndex, setSelectedIndex] = useState(0);

  const onSelect = useCallback(() => {
    if (!emblaApi) return;
    setSelectedIndex(emblaApi.selectedScrollSnap());
  }, [emblaApi]);

  useEffect(() => {
    if (!emblaApi) return;
    emblaApi.on('select', onSelect);
    onSelect();
  }, [emblaApi, onSelect]);

  if (!clips || clips.length === 0) {
    return (
      <div className="w-full h-80 flex flex-col items-center justify-center text-center p-6 glass-panel rounded-[32px]">
        <p className="text-white/60 font-medium">No clips found matching this filter.</p>
        <p className="text-xs text-white/40 mt-1">Add a new video link using the '+' button below.</p>
      </div>
    );
  }

  return (
    <div className="relative w-full overflow-hidden py-4" ref={emblaRef}>
      <div className="flex touch-pan-y -ml-4">
        {clips.map((clip, index) => {
          const isActive = index === selectedIndex;
          return (
            <div
              key={clip.id}
              className="flex-[0_0_78%] sm:flex-[0_0_65%] min-w-0 pl-4"
            >
              <ClipCard
                clip={clip}
                isActive={isActive}
                onClick={() => onSelectClip(clip)}
              />
            </div>
          );
        })}
      </div>

      {/* Pagination indicators */}
      <div className="flex justify-center items-center gap-1.5 mt-4">
        {clips.slice(0, 8).map((_, i) => (
          <button
            key={i}
            onClick={() => emblaApi?.scrollTo(i)}
            className={`h-1.5 rounded-full transition-all ${
              i === selectedIndex
                ? 'w-6 bg-white shadow-glow'
                : 'w-1.5 bg-white/20 hover:bg-white/40'
            }`}
            aria-label={`Go to slide ${i + 1}`}
          />
        ))}
      </div>
    </div>
  );
};

