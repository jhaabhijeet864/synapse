export function Button({
  children,
  variant = 'primary',
  size = 'md',
  className = '',
  ...props
}: React.ButtonHTMLAttributes<HTMLButtonElement> & { variant?: 'primary' | 'ghost'; size?: 'sm' | 'md' }) {
  const baseClass = variant === 'primary' ? 'btn-primary' : 'btn-ghost'
  const sizeClass = size === 'sm' ? 'btn-sm' : ''
  return (
    <button className={`${baseClass} ${sizeClass} ${className}`} {...props}>
      {children}
    </button>
  )
}