import { useState } from 'react'
import Header from '../components/Header'
import WeatherPostcard from '../components/WeatherPostcard'
import RecommendationCard from '../components/RecommendationCard'
import HourlyForecast from '../components/HourlyForecast'
import WeatherGPTCard from '../components/WeatherGPTCard'
import FloatingChatButton from '../components/FloatingChatButton'
import BottomNav from '../components/BottomNav'
// Current conditions: a contract-faithful sample of the /weather record.
import homeWeather from '../mocks/homeWeather.json'
// Not-yet-contract-backed extras (hourly strip, recommendation) — clearly
// separated so the swap to real endpoints stays one-for-one. See the file.
import { hourlyForecast, recommendation } from '../data/homePlaceholders'

function Home() {
  const [chatOpen, setChatOpen] = useState(false)

  return (
    <main className="app-shell">
      <div className="home-page">
        <Header location={homeWeather.location} />

        <section className="home-content">
          <WeatherPostcard weather={homeWeather} />
          <RecommendationCard recommendation={recommendation} />
          <HourlyForecast forecast={hourlyForecast} />
          <WeatherGPTCard onOpenChat={() => setChatOpen(true)} />
        </section>
      </div>

      <BottomNav active="home" />

      <FloatingChatButton
        onClick={() => setChatOpen(true)}
        isOpen={chatOpen}
        onClose={() => setChatOpen(false)}
      />
    </main>
  )
}

export default Home
