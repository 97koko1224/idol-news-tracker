'use client'

import Image from 'next/image'
import { formatDistanceToNow } from 'date-fns'
import { ja } from 'date-fns/locale'
import { SourceBadge } from './SourceBadge'
import { getMemberColor, getTextColor } from '@/lib/memberColors'
import type { NewsItem } from '@/lib/types'

function timeAgo(dateStr: string | null): string {
  if (!dateStr) return ''
  try {
    const d = new Date(dateStr.endsWith('Z') ? dateStr : dateStr + 'Z')
    return formatDistanceToNow(d, { addSuffix: true, locale: ja })
  } catch {
    return ''
  }
}

const SOURCE_ICON_FALLBACK: Record<string, string> = {
  youtube: '▶',
  rss: '📰',
  web: '🌐',
}

export function NewsCard({ item }: { item: NewsItem }) {
  const timeStr = timeAgo(item.published_at ?? item.collected_at)

  return (
    <a
      href={item.url}
      target="_blank"
      rel="noopener noreferrer"
      className="flex gap-3 rounded-lg border border-gray-100 bg-white p-3 shadow-sm transition-shadow hover:shadow-md"
    >
      {/* サムネイル */}
      <div className="relative h-[72px] w-[108px] shrink-0 overflow-hidden rounded bg-gray-100">
        {item.thumbnail_url ? (
          <Image
            src={item.thumbnail_url}
            alt=""
            fill
            className="object-cover"
            unoptimized
          />
        ) : (
          <div className="flex h-full items-center justify-center text-2xl text-gray-400">
            {SOURCE_ICON_FALLBACK[item.source_type] ?? '📄'}
          </div>
        )}
      </div>

      {/* コンテンツ */}
      <div className="min-w-0 flex-1">
        <div className="mb-1 flex flex-wrap items-center gap-1">
          <span className="rounded bg-purple-100 px-1.5 py-0.5 text-[10px] font-semibold text-purple-700">
            {item.group_name}
          </span>
          <SourceBadge type={item.source_type} />
          {/* メンバータグ（メンバーカラー適用）*/}
          {item.member_tags && item.member_tags.length > 0 &&
            item.member_tags.map((tag) => {
              const bg = getMemberColor(tag)
              const fg = getTextColor(bg)
              return (
                <span
                  key={tag}
                  className="rounded px-1.5 py-0.5 text-[10px] font-semibold"
                  style={{ backgroundColor: bg, color: fg }}
                >
                  {tag}
                </span>
              )
            })}
        </div>
        <p className="line-clamp-2 text-sm font-medium leading-snug text-gray-900">
          {item.title}
        </p>
        <p className="mt-1 text-xs text-gray-400">
          {item.source_name}
          {timeStr && ` • ${timeStr}`}
        </p>
      </div>
    </a>
  )
}
