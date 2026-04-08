import { useState, useRef, useEffect, KeyboardEvent } from 'react';
import { createPortal } from 'react-dom';

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
  const inputRef = useRef<HTMLInputElement>(null);

  const filtered = value.length >= minChars
    ? suggestions
        .filter(item =>
          getItemValue(item).toLowerCase().includes(value.toLowerCase())
        )
        .slice(0, maxSuggestions)
    : [];

  const isOpen = focused && filtered.length > 0;

  // DEBUG - remover depois
  useEffect(() => {
    console.log('[Autocomplete]', { value, focused, filteredLen: filtered.length, isOpen, suggestionsLen: suggestions.length, dropdownRect: !!dropdownRect });
  });

  useEffect(() => {
    if (isOpen && containerRef.current) {
      setDropdownRect(containerRef.current.getBoundingClientRect());
    }
  }, [isOpen, value]);

  useEffect(() => {
    function handleMouseDown(e: MouseEvent) {
      if (
        containerRef.current &&
        !containerRef.current.contains(e.target as Node)
      ) {
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
          <ul
            role="listbox"
            style={{
              position: 'fixed',
              top: dropdownRect.bottom + 8,
              left: dropdownRect.left,
              width: dropdownRect.width,
              zIndex: 9999,
            }}
            className="bg-white border border-gray-200 rounded-2xl shadow-xl overflow-hidden"
          >
            {filtered.map((item, i) => (
              <li
                key={i}
                id={`autocomplete-item-${i}`}
                role="option"
                aria-selected={i === activeIndex}
                onMouseDown={e => {
                  e.preventDefault();
                  handleSelect(item);
                }}
                onMouseEnter={() => setActiveIndex(i)}
              >
                {renderSuggestion(item, i === activeIndex)}
              </li>
            ))}
          </ul>,
          document.body
        )
      : null;

  return (
    <div ref={containerRef} className={`relative flex items-center w-full ${className}`}>
      {icon && <span className="mr-3 shrink-0">{icon}</span>}
      <input
        ref={inputRef}
        type="text"
        value={value}
        placeholder={placeholder}
        className="w-full py-3 outline-none text-brand-navy placeholder:text-text-body/50 bg-transparent"
        onChange={e => {
          onChange(e.target.value);
          setFocused(true);
          setActiveIndex(-1);
        }}
        onFocus={() => setFocused(true)}
        onBlur={() => {
          // small delay so mousedown on list item fires first
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
