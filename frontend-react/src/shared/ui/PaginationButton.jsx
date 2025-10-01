import './PaginationButton.scss'

const PaginationButton = ({ currentPage, totalPages, onPageChange }) => {
  const goToPage = (page) => {
    if (page >= 1 && page <= totalPages) {
      onPageChange(page)
    }
  }

  if (totalPages <= 1) return null

  return (
    <div className="pagination">
      <button 
        onClick={() => goToPage(currentPage - 1)} 
        disabled={currentPage === 1}
      >
        이전
      </button>
      <span> {currentPage} / {totalPages}</span>
      <button
        onClick={() => goToPage(currentPage + 1)}
        disabled={currentPage === totalPages}
      >
        다음
      </button>
    </div>
  )
}

export default PaginationButton