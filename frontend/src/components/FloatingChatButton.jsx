function FloatingChatButton({ onClick, isOpen, onClose }) {
  if (isOpen) {
    return (
      <div className="chat-placeholder">
        <div>
          <strong>WeatherGPT</strong>
          <p>Chat will be connected to the backend later.</p>
        </div>
        <button type="button" onClick={onClose} aria-label="Close chat">
          ×
        </button>
      </div>
    )
  }

  return (
    <button
      className="floating-chat-button"
      type="button"
      aria-label="Open WeatherGPT"
      title="Ask WeatherGPT"
      onClick={onClick}
    >
      ✦
    </button>
  )
}

export default FloatingChatButton
