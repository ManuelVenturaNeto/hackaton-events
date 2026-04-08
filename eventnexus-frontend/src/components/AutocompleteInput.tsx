import { useState, useRef, useEffect, KeyboardEvent } from 'react';
import { createPortal } from 'react-dom';
import { motion, AnimatePresence } from 'motion/react';

interface AutocompleteInputProps<T> {
  value: string;
  onChange: (value: string) => void;
  onSelect: (item: T) => void;
  suggestions: T[];
  renderSuggestion: (item: T, isActive: boolean) => React.ReactNode;
  getItemValue: (item: T) => string;
  placeholder?: string;
  icon?: React.ReactNode;
  minChars?: number;
  maxSuggestions?: number;
  className?: string;
}

export function AutocompleteInput<T>({
  value,
  onChange,
  onSelect,
  suggestions,
  renderSuggestion,
  getItemValue,
  placeholder,
  icon,
  minChars = 2,
  maxSuggestions = 6,
  className = '',
}: AutocompleteInputProps<T>) {
  const [activeIndex, setActiveIndex] = useState(-1);
  const [focused, setFocused] = useState(false);
  const [dropdownRect, setDropdownRect] = useState<DOMRect | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  const filtered = value.length >= minChars
    ? suggestions
        .filter(item =>
          getItemValue(item).toLowerCase().includes(value.toLowerCase())
        )
        .slice(0, maxSuggestions)
    : [];

  const isOpen = focused && filtered.length > 0;

  useEffect(() => {
    if (isOpen && containerRef.current) {
      setDropdownRect(containerRef.current.getBoundingClientRect());
    }
  }, [isOpen, value]);

  useEffect(() => {
    function handleMouseDown(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setFocused(false);
        setActiveIndex(-1);
      }
    }
    document.addEventListener('mousedown', handleMouseDown);
    return () => document.removeEventListener('mousedown', handleMouseDown);
  }, []);

  function handleKeyDown(e: KeyboardEvent<HTMLInputElement>) {
    if (!isOpen) return;
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setActiveIndex(i => Math.min(i + 1, filtered.length - 1));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setActiveIndex(i => Math.max(i - 1, -1));
    } else if (e.key === 'Enter' && activeIndex >= 0) {
      e.preventDefault();
      handleSelect(filtered[activeIndex]);
    } else if (e.key === 'Escape') {
      setFocused(false);
      setActiveIndex(-1);
    }
  }

  function handleSelect(item: T) {
    onChange(getItemValue(item));
    onSelect(item);
    setFocused(false);
    setActiveIndex(-1);
  }

  const dropdown =
    isOpen && dropdownRect
      ? createPortal(
          <AnimatePresence>
            <motion.ul
              role="listbox"
              initial={{ opacity: 0, y: -4, scale: 0.98 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: -4, scale: 0.98 }}
              transition={{ duration: 0.15, ease: 'easeOut' }}
              style={{
                position: 'fixed',
                top: dropdownRect.bottom + 6,
                left: dropdownRect.left,
                width: Math.max(dropdownRect.width, 320),
                zIndex: 9999,
              }}
              className="bg-white/98 backdrop-blur-xl border border-border-gray/40 rounded-2xl shadow-[0_12px_48px_rgba(25,42,61,0.15),0_2px_8px_rgba(25,42,61,0.06)] overflow-hidden ring-1 ring-black/[0.02]"
            >
              <div className="py-1.5">
                {filtered.map((item, i) => (
                  <motion.li
                    key={i}
                    id={`autocomplete-item-${i}`}
                    role="option"
                    aria-selected={i === activeIndex}
                    initial={{ opacity: 0, x: -4 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: i * 0.03 }}
                    onMouseDown={e => {
                      e.preventDefault();
                      handleSelect(item);
                    }}
                    onMouseEnter={() => setActiveIndex(i)}
                    className="mx-1.5"
                  >
                    {renderSuggestion(item, i === activeIndex)}
                  </motion.li>
                ))}
              </div>
            </motion.ul>
          </AnimatePresence>,
          document.body
        )
      : null;

  return (
    <div ref={containerRef} className={`relative flex items-center w-full ${className}`}>
      {icon && <span className="mr-3 shrink-0">{icon}</span>}
      <input
        type="text"
        value={value}
        placeholder={placeholder}
        className="w-full py-3 outline-none text-brand-navy placeholder:text-text-body/40 bg-transparent text-[15px]"
        onChange={e => {
          onChange(e.target.value);
          setFocused(true);
          setActiveIndex(-1);
        }}
        onFocus={() => setFocused(true)}
        onBlur={() => {
          setTimeout(() => setFocused(false), 150);
        }}
        onKeyDown={handleKeyDown}
        role="combobox"
        aria-expanded={isOpen}
        aria-autocomplete="list"
        aria-activedescendant={activeIndex >= 0 ? `autocomplete-item-${activeIndex}` : undefined}
      />
      {dropdown}
    </div>
  );
}
