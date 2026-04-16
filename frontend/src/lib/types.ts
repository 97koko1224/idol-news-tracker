export interface Group {
  id: number
  slug: string
  name: string
  item_count: number
}

export interface GroupDetail extends Group {
  stats_by_source: Record<string, number>
}

export interface Member {
  id: number
  name: string
  group_slug: string
  group_name: string
  keywords: string[]
  twitter_account: string | null
}

export interface NewsItem {
  id: number
  group_id: number
  group_slug: string
  group_name: string
  source_type: 'rss' | 'youtube' | 'twitter' | 'web'
  source_name: string
  title: string
  url: string
  thumbnail_url: string | null
  summary: string | null
  published_at: string | null
  collected_at: string | null
  member_tags: string[] | null
}

export interface NewsList {
  items: NewsItem[]
  total: number
  page: number
  pages: number
}

export interface Stats {
  total_items: number
  items_today: number
  items_this_week: number
  by_group: Array<{ slug: string; name: string; count: number }>
  by_source: Record<string, number>
  last_collected_at: string | null
}
