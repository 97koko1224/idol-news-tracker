import { StatsCards } from '@/components/StatsCards'
import { NewsFeed } from '@/components/NewsFeed'

export default function HomePage() {
  return (
    <div>
      <h2 className="mb-4 text-xl font-bold text-gray-900">最新ニュース</h2>
      <StatsCards />
      <NewsFeed />
    </div>
  )
}
