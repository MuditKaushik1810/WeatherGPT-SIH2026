import { useEffect, useRef, useState } from 'react'
import ProvenanceChip from '../components/ProvenanceChip'
import { fetchChatAnswer } from '../api/chat'
import { fetchHomeView } from '../api/home'
import { getSavedLocation } from '../lib/savedLocation'
import { getDefaultLocation } from '../lib/preferences'
import { loadSession, saveSession, clearSession } from '../lib/chatSession'
import { useI18n, translate, LANGUAGES } from '../i18n'

// Starter suggestions. Each is a catalog key rendered two ways: the LABEL in the
// user's language (what they see and what appears in the chat bubble) and the
// English QUERY sent to the backend — so the backend's location parser always
// sees a name it knows, while the UI stays fully localized. The location is the
// saved/default place (or Delhi as a neutral example when none is set yet), and
// the set upgrades to conditions-aware prompts once the location's data loads.
const BASE_SUGGESTIONS = ['suggest.rainTomorrow', 'suggest.airQuality', 'suggest.weekend']

function dataDrivenKeys(view) {
  const c = (view && view.current) || {}
  const keys = []
  if (typeof c.aqi === 'number' && c.aqi > 100) keys.push('suggest.aqiWhy')
  if (typeof c.temp === 'number' && c.temp >= 38) keys.push('suggest.heatSafety')
  if (typeof c.precipitation_chance === 'number' && c.precipitation_chance >= 0.4) keys.push('suggest.rainContinue')
  return keys
}

function buildSuggestions(loc, view) {
  const keys = [...dataDrivenKeys(view).slice(0, 2)]
  for (const key of BASE_SUGGESTIONS) {
    if (keys.length >= 3) break
    if (!keys.includes(key)) keys.push(key)
  }
  return keys.slice(0, 3).map((key) => ({ key, loc }))
}

// Render the answer text safely: preserve line breaks and turn **bold** markers
// into <strong> (the LLM often replies in light markdown). No HTML is injected.
function renderAnswer(text) {
  return text.split('\n').map((line, i) => {
    if (line.trim() === '') return <span key={i} className="chat-break" />
    const parts = line.split(/(\*\*[^*]+\*\*)/g).map((part, j) =>
      part.startsWith('**') && part.endsWith('**')
        ? <strong key={j}>{part.slice(2, -2)}</strong>
        : part,
    )
    return <p key={i} className="chat-line">{parts}</p>
  })
}

const MicIcon = () => (
  <svg viewBox="0 0 24 24" width="19" height="19" fill="none" stroke="currentColor"
       strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <rect x="9" y="2.5" width="6" height="11" rx="3" />
    <path d="M5 11a7 7 0 0 0 14 0" />
    <line x1="12" y1="18" x2="12" y2="21.5" />
  </svg>
)

const SpeechRecognition =
  typeof window !== 'undefined' && (window.SpeechRecognition || window.webkitSpeechRecognition)
const speechSynthesisSupported = typeof window !== 'undefined' && 'speechSynthesis' in window

// The selected language drives the whole app (i18n store), the LLM answer
// language, and browser voice in/out — bcp47 tag from the shared LANGUAGES list.
function bcp47For(code) {
  return (LANGUAGES.find((l) => l.code === code) || {}).bcp47 || 'en-IN'
}

const SpeakerIcon = () => (
  <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor"
       strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <path d="M11 5 6 9H3v6h3l5 4z" />
    <path d="M15.5 8.5a5 5 0 0 1 0 7" />
    <path d="M18.5 5.5a9 9 0 0 1 0 13" />
  </svg>
)

function Chat() {
  const { t, lang: language, setLang } = useI18n()
  // Resume the last conversation (persisted ~1 day) so leaving and returning to
  // chat continues where the user left off instead of starting cold.
  const [restored] = useState(loadSession)
  const [messages, setMessages] = useState(() => (restored ? restored.messages : [])) // {id, role, text, source?, dataTier?}
  const [lastLocation, setLastLocation] = useState(() => (restored ? restored.lastLocation : null))
  const [input, setInput] = useState('')
  const [status, setStatus] = useState('idle') // idle | loading
  const [listening, setListening] = useState(false)
  const [speakingId, setSpeakingId] = useState(null)

  const realLoc = getSavedLocation() || getDefaultLocation() || null
  const suggestionLoc = realLoc || 'Delhi'
  const [suggestions, setSuggestions] = useState(() => buildSuggestions(suggestionLoc, null))
  const endRef = useRef(null)
  const recognitionRef = useRef(null)

  useEffect(() => {
    endRef.current?.scrollIntoView?.({ behavior: 'smooth' })
  }, [messages, status])

  // Persist the conversation as it grows so it survives navigation / a short break.
  useEffect(() => {
    if (messages.length) saveSession({ messages, lastLocation })
  }, [messages, lastLocation])

  // Upgrade the starter suggestions with prompts grounded in the location's real
  // current conditions — only when there's an actual saved/default place (not the
  // neutral example). Fails soft, keeping the base set.
  useEffect(() => {
    if (!realLoc) return undefined
    let active = true
    fetchHomeView(realLoc)
      .then((view) => { if (active) setSuggestions(buildSuggestions(realLoc, view)) })
      .catch(() => {})
    return () => { active = false }
  }, [realLoc])

  const send = (rawQuery, display) => {
    const query = (rawQuery || '').trim()
    if (!query || status === 'loading') return
    const shown = (display ?? rawQuery).trim()
    const userMsg = { id: Date.now(), role: 'user', text: shown }
    // Carry recent turns + the conversation/default location so a bare follow-up
    // ("what about tomorrow?") resolves against the last place, not a dead-end.
    const history = messages.map((m) => ({ role: m.role, content: m.text }))
    const contextLocation = lastLocation || getDefaultLocation() || getSavedLocation() || null

    setMessages((prev) => [...prev, userMsg])
    setInput('')
    setStatus('loading')

    fetchChatAnswer(query, language, { contextLocation, history })
      .then((reply) => {
        setMessages((prev) => [...prev, {
          id: userMsg.id + 1, role: 'assistant', text: reply.answer,
          source: reply.source, dataTier: reply.data_tier,
        }])
        if (reply.location) setLastLocation(reply.location) // remember for follow-ups
      })
      .catch(() => {
        setMessages((prev) => [...prev, {
          id: userMsg.id + 1, role: 'assistant', text: t('chat.error'), error: true,
        }])
      })
      .finally(() => setStatus('idle'))
  }

  const onSubmit = (event) => {
    event.preventDefault()
    send(input)
  }

  const newChat = () => {
    if (speechSynthesisSupported) window.speechSynthesis.cancel()
    clearSession()
    setMessages([])
    setLastLocation(null)
    setSpeakingId(null)
    setSuggestions(buildSuggestions(suggestionLoc, null))
  }

  const toggleVoice = () => {
    if (!SpeechRecognition || status === 'loading') return
    if (listening) {
      recognitionRef.current?.stop()
      return
    }
    const recognition = new SpeechRecognition()
    recognition.lang = bcp47For(language)
    recognition.interimResults = false
    recognition.maxAlternatives = 1
    recognition.onresult = (event) => setInput(event.results[0][0].transcript)
    recognition.onend = () => setListening(false)
    recognition.onerror = () => setListening(false)
    recognitionRef.current = recognition
    setListening(true)
    recognition.start()
  }

  // Voice output — read an answer aloud in the selected language (toggles off if
  // the same message is tapped again). Browsers without speechSynthesis just
  // don't get the button.
  const speak = (id, text) => {
    if (!speechSynthesisSupported) return
    window.speechSynthesis.cancel()
    if (speakingId === id) {
      setSpeakingId(null)
      return
    }
    const utterance = new SpeechSynthesisUtterance(text)
    utterance.lang = bcp47For(language)
    utterance.onend = () => setSpeakingId(null)
    setSpeakingId(id)
    window.speechSynthesis.speak(utterance)
  }

  return (
    <main className="app-shell chat-shell">
      <div className="chat-page">
        <div className="chat-backdrop" aria-hidden="true">
          <span className="chat-sun" />
          <span className="chat-hill chat-hill-back" />
          <span className="chat-hill chat-hill-front" />
        </div>

        <header className="chat-header">
          <button
            className="icon-button chat-back"
            type="button"
            aria-label={t('chat.back')}
            title={t('chat.backShort')}
            onClick={() => { window.location.hash = 'home' }}
          >
            ←
          </button>
          <h1 className="chat-title">WeatherGPT</h1>
          <div className="chat-head-actions">
            {messages.length > 0 && (
              <button
                type="button"
                className="chat-newchat"
                onClick={newChat}
                aria-label={t('chat.newChat')}
                title={t('chat.newChat')}
              >
                {t('chat.newChat')}
              </button>
            )}
            <select
              className="chat-lang"
              value={language}
              onChange={(event) => setLang(event.target.value)}
              aria-label={t('chat.langLabel')}
            >
              {LANGUAGES.map((l) => <option key={l.code} value={l.code}>{l.label}</option>)}
            </select>
          </div>
        </header>

        <section className="chat-thread" aria-live="polite">
          {messages.length === 0 && (
            <div className="chat-empty">
              <p>{t('chat.emptyPrompt')}</p>
              <div className="chat-suggestions">
                {suggestions.map((s) => {
                  const label = t(s.key, { loc: s.loc })
                  const query = translate('en', s.key, { loc: s.loc })
                  return (
                    <button key={s.key} type="button" className="chat-suggestion" onClick={() => send(query, label)}>
                      {label}
                    </button>
                  )
                })}
              </div>
            </div>
          )}

          {messages.map((msg) => (
            <div key={msg.id} className={`chat-bubble chat-${msg.role}${msg.error ? ' chat-error' : ''}`}>
              <div className="chat-bubble-text">
                {msg.role === 'assistant' ? renderAnswer(msg.text) : msg.text}
              </div>
              {msg.role === 'assistant' && !msg.error && (
                <div className="chat-answer-actions">
                  {msg.source && <ProvenanceChip source={msg.source} dataTier={msg.dataTier} />}
                  {speechSynthesisSupported && (
                    <button
                      type="button"
                      className={`chat-speak${speakingId === msg.id ? ' speaking' : ''}`}
                      onClick={() => speak(msg.id, msg.text)}
                      aria-label={speakingId === msg.id ? t('chat.speakStop') : t('chat.speakRead')}
                      title={t('chat.speakTitle')}
                    >
                      <SpeakerIcon />
                    </button>
                  )}
                </div>
              )}
            </div>
          ))}

          {status === 'loading' && (
            <div className="chat-bubble chat-assistant chat-typing" role="status">
              <span className="chat-dot" /><span className="chat-dot" /><span className="chat-dot" />
            </div>
          )}

          <div ref={endRef} />
        </section>

        <form className="chat-input-bar" onSubmit={onSubmit}>
          <input
            className="chat-input"
            type="text"
            value={input}
            onChange={(event) => setInput(event.target.value)}
            placeholder={listening ? t('chat.listening') : t('chat.inputPlaceholder')}
            aria-label={t('chat.inputLabel')}
            disabled={status === 'loading'}
          />
          {SpeechRecognition && (
            <button
              type="button"
              className={`chat-mic${listening ? ' listening' : ''}`}
              onClick={toggleVoice}
              disabled={status === 'loading'}
              aria-label={listening ? t('chat.micStop') : t('chat.micStart')}
              aria-pressed={listening}
              title={t('chat.micTitle')}
            >
              <MicIcon />
            </button>
          )}
          <button className="chat-send" type="submit" disabled={status === 'loading' || !input.trim()}>
            {t('chat.send')}
          </button>
        </form>
      </div>
    </main>
  )
}

export default Chat
