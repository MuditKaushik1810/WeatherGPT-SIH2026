import { useState } from 'react'
import Header from '../components/Header'
import WeatherPostcard from '../components/WeatherPostcard'
import RecommendationCard from '../components/RecommendationCard'
import HourlyForecast from '../components/HourlyForecast'
import WeatherGPTCard from '../components/WeatherGPTCard'
import FloatingChatButton from '../components/FloatingChatButton'
import { homeWeather } from '../data/homeWeather'

function Home() {
  const [chatOpen, setChatOpen] = useState(false)

  return (
    <main className="app-shell">
      <div className="home-page">
        <Header location={homeWeather.location} />

        <section className="home-content">
          <WeatherPostcard weather={homeWeather} />
          <RecommendationCard recommendation={homeWeather.recommendation} />
          <HourlyForecast forecast={homeWeather.hourlyForecast} />
          <WeatherGPTCard onOpenChat={() => setChatOpen(true)} />
        </section>
      </div>

      <FloatingChatButton
        onClick={() => setChatOpen(true)}
        isOpen={chatOpen}
        onClose={() => setChatOpen(false)}
      />
    </main>
  )
}

export default Home
