import { useEffect, useRef, useState } from 'react'
import ProvenanceChip from '../components/ProvenanceChip'
import { fetchChatAnswer } from '../api/chat'
import { fetchHomeView } from '../api/home'
import { getSavedLocation } from '../lib/savedLocation'

// Suggestions are built fresh each open and are genuinely situational: they draw
// on the saved location, the current season (so prompts feel timely/national),
// and — once the location's live conditions load — the actual weather, AQI and
// any active warnings for that place.
const LOCATION_TEMPLATES = [
  (loc) => `Will it rain in ${loc} tomorrow?`,
  (loc) => `How's the air quality in ${loc} right now?`,
  (loc) => `Do I need an umbrella in ${loc} today?`,
  (loc) => `What's the weekend forecast for ${loc}?`,
  (loc) => `Is it a good day to be outdoors in ${loc}?`,
]

function seasonalPrompts(now = new Date()) {
  const m = now.getMonth()
  if (m >= 5 && m <= 8) return [ // Jun–Sep: monsoon
    'Monsoon outlook for the west coast this week?',
    'Any flood warnings across the country right now?',
    'Where is heavy rainfall expected this week?',
  ]
  if (m >= 2 && m <= 4) return [ // Mar–May: summer
    'Any heat wave warnings across north India?',
    'Which cities are hottest right now?',
    'How do I stay safe in the heat this week?',
  ]
  return [ // Oct–Feb: winter
    'Any cold wave alerts for north India?',
    'Where is dense fog expected this week?',
    'How cold will it get this weekend?',
  ]
}

// Prompts grounded in the location's ACTUAL current conditions.
function dataDrivenPrompts(loc, view) {
  const c = (view && view.current) || {}
  const out = []
  if (Array.isArray(c.warnings) && c.warnings.length) out.push(`What safety steps for the active alert in ${loc}?`)
  if (typeof c.aqi === 'number' && c.aqi > 100) out.push(`Why is the air quality poor in ${loc} today?`)
  if (typeof c.precipitation_chance === 'number' && c.precipitation_chance >= 0.4) out.push(`Will the rain in ${loc} continue tomorrow?`)
  if (typeof c.temp === 'number' && c.temp >= 38) out.push(`How can I stay safe in the heat in ${loc}?`)
  return out
}

function shuffle(list) {
  const a = [...list]
  for (let i = a.length - 1; i > 0; i -= 1) {
    const j = Math.floor(Math.random() * (i + 1))
    ;[a[i], a[j]] = [a[j], a[i]]
  }
  return a
}

function buildFallback(loc) {
  const season = seasonalPrompts()
  if (loc) {
    const locP = shuffle(LOCATION_TEMPLATES).slice(0, 2).map((fn) => fn(loc))
    return shuffle([...locP, shuffle(season)[0]])
  }
  return shuffle(season).slice(0, 3)
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

function Chat() {
  const savedLocation = getSavedLocation()
  const [messages, setMessages] = useState([]) // {id, role, text, source?, dataTier?}
  const [input, setInput] = useState('')
  const [status, setStatus] = useState('idle') // idle | loading
  const [listening, setListening] = useState(false)
  const [suggestions, setSuggestions] = useState(() => buildFallback(savedLocation))
  const endRef = useRef(null)
  const recognitionRef = useRef(null)

  useEffect(() => {
    endRef.current?.scrollIntoView?.({ behavior: 'smooth' })
  }, [messages, status])

  // Upgrade the fallback suggestions with prompts grounded in the saved
  // location's real current conditions. Fails soft — keeps the fallback.
  useEffect(() => {
    if (!savedLocation) return undefined
    let active = true
    fetchHomeView(savedLocation)
      .then((view) => {
        if (!active) return
        const dd = dataDrivenPrompts(savedLocation, view).slice(0, 2)
        if (!dd.length) return
        const pool = shuffle([...LOCATION_TEMPLATES.map((fn) => fn(savedLocation)), ...seasonalPrompts()])
        setSuggestions(shuffle([...dd, ...pool.slice(0, 3 - dd.length)]))
      })
      .catch(() => {})
    return () => { active = false }
  }, [savedLocation])

  const send = (text) => {
    const query = text.trim()
    if (!query || status === 'loading') return
    const userMsg = { id: Date.now(), role: 'user', text: query }
    setMessages((prev) => [...prev, userMsg])
    setInput('')
    setStatus('loading')

    fetchChatAnswer(query)
      .then((reply) => {
        setMessages((prev) => [...prev, {
          id: userMsg.id + 1, role: 'assistant', text: reply.answer,
          source: reply.source, dataTier: reply.data_tier,
        }])
      })
      .catch(() => {
        setMessages((prev) => [...prev, {
          id: userMsg.id + 1, role: 'assistant',
          text: "I couldn't reach the weather service just now — please try again in a moment.",
          error: true,
        }])
      })
      .finally(() => setStatus('idle'))
  }

  const onSubmit = (event) => {
    event.preventDefault()
    send(input)
  }

  const toggleVoice = () => {
    if (!SpeechRecognition || status === 'loading') return
    if (listening) {
      recognitionRef.current?.stop()
      return
    }
    const recognition = new SpeechRecognition()
    recognition.lang = 'en-IN'
    recognition.interimResults = false
    recognition.maxAlternatives = 1
    recognition.onresult = (event) => setInput(event.results[0][0].transcript)
    recognition.onend = () => setListening(false)
    recognition.onerror = () => setListening(false)
    recognitionRef.current = recognition
    setListening(true)
    recognition.start()
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
            aria-label="Back to home"
            title="Back"
            onClick={() => { window.location.hash = 'home' }}
          >
            ←
          </button>
          <h1 className="chat-title">WeatherGPT</h1>
          <span aria-hidden="true" />
        </header>

        <section className="chat-thread" aria-live="polite">
          {messages.length === 0 && (
            <div className="chat-empty">
              <p>Ask me about the weather. For example:</p>
              <div className="chat-suggestions">
                {suggestions.map((s) => (
                  <button key={s} type="button" className="chat-suggestion" onClick={() => send(s)}>
                    {s}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((msg) => (
            <div key={msg.id} className={`chat-bubble chat-${msg.role}${msg.error ? ' chat-error' : ''}`}>
              <div className="chat-bubble-text">
                {msg.role === 'assistant' ? renderAnswer(msg.text) : msg.text}
              </div>
              {msg.role === 'assistant' && !msg.error && msg.source && (
                <ProvenanceChip source={msg.source} dataTier={msg.dataTier} />
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
            placeholder={listening ? 'Listening…' : 'Ask about the weather…'}
            aria-label="Your question"
            disabled={status === 'loading'}
          />
          {SpeechRecognition && (
            <button
              type="button"
              className={`chat-mic${listening ? ' listening' : ''}`}
              onClick={toggleVoice}
              disabled={status === 'loading'}
              aria-label={listening ? 'Stop voice input' : 'Start voice input'}
              aria-pressed={listening}
              title="Voice input"
            >
              <MicIcon />
            </button>
          )}
          <button className="chat-send" type="submit" disabled={status === 'loading' || !input.trim()}>
            Send
          </button>
        </form>
      </div>
    </main>
  )
}

export default Chat
