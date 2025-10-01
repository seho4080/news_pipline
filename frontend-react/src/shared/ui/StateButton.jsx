import { useNavigate } from 'react-router-dom'
import './StateButton.scss'

const StateButton = ({ 
  type = 'button', 
  size = 'md',
  variant = 'default',
  isActive = false, 
  to, 
  className = '', 
  disabled = false,
  loading = false,
  onClick,
  children,
  ...props 
}) => {
  const navigate = useNavigate()

  const handleClick = (e) => {
    if (disabled || loading) return
    
    if (to) {
      navigate(to)
    }
    if (onClick) {
      onClick(e)
    }
  }

  const getClasses = () => {
    const classes = ['modern-state-button']
    
    // Size classes
    classes.push(`btn-${size}`)
    
    // Type classes (backward compatibility)
    if (type === 'state') classes.push('btn-state')
    if (type === 'tag') classes.push('btn-tag')
    if (type === 'primary') classes.push('btn-primary')
    
    // Variant classes
    if (variant !== 'default') classes.push(`btn-${variant}`)
    
    // State classes
    if (isActive) classes.push('active')
    if (disabled) classes.push('disabled')
    if (loading) classes.push('loading')
    
    // Custom classes
    if (className) classes.push(className)
    
    return classes.join(' ')
  }

  return (
    <button
      className={getClasses()}
      disabled={disabled || loading}
      onClick={handleClick}
      {...props}
    >
      {loading && <span className="btn-spinner" />}
      <span className={`btn-content ${loading ? 'loading' : ''}`}>
        {children}
      </span>
    </button>
  )
}

export default StateButton