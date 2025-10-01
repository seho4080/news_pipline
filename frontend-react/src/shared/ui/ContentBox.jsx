import './ContentBox.scss'

const ContentBox = ({ children, className = '' }) => {
  return (
    <div className={`box ${className}`}>
      {children}
    </div>
  )
}

export default ContentBox