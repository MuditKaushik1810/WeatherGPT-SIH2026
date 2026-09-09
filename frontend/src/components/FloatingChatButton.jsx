import { useI18n } from '../i18n'

// Floating "Ask WeatherGPT" button — opens the Chat tab. (Previously a
// backend-less placeholder; now that POST /chat is live it navigates to the
// real Chat screen.)
function FloatingChatButton() {
  const { t } = useI18n()
  return (
    <button
      className="floating-chat-button"
      type="button"
      aria-label={t('float.aria')}
      title={t('float.title')}
      onClick={() => { window.location.hash = 'chat' }}
    >
      ✦
    </button>
  )
}

export default FloatingChatButton
