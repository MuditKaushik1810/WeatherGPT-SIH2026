// Floating "Ask WeatherGPT" button — opens the Chat tab. (Previously a
// backend-less placeholder; now that POST /chat is live it navigates to the
// real Chat screen.)
function FloatingChatButton() {
  return (
    <button
      className="floating-chat-button"
      type="button"
      aria-label="Open WeatherGPT chat"
      title="Ask WeatherGPT"
      onClick={() => { window.location.hash = 'chat' }}
    >
      ✦
    </button>
  )
}

export default FloatingChatButton
