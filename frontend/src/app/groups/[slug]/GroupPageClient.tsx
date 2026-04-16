'use client'

import useSWR from 'swr'
import { fetcher } from '@/lib/api'
import { NewsFeed } from '@/components/NewsFeed'
import type { GroupDetail } from '@/lib/types'

const SOURCE_LABELS: Record<string, string> = {
  rss: 'RSS',
  youtube: 'YouTube',
  twitter: 'X',
  web: 'Web',
}

interface Props {
  slug: string
  initialMember: string
}

export function GroupPageClient({ slug, initialMember }: Props) {
  const { data: group } = useSWR<GroupDetail>(`/api/groups/${slug}`, fetcher)

  return (
    <div>
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900">{group?.name ?? slug}</h2>
        {group && (
          <div className="mt-2 flex flex-wrap gap-3">
            {Object.entries(group.stats_by_source).map(([src, cnt]) => (
              <span key={src} className="text-sm text-gray-500">
                {SOURCE_LABELS[src] ?? src}: <strong>{cnt}</strong>件
              </span>
            ))}
            <span className="text-sm font-semibold text-gray-700">
              合計 {group.item_count}件
            </span>
          </div>
        )}
      </div>

      <NewsFeed groupSlug={slug} initialMember={initialMember} />
    </div>
  )
}
