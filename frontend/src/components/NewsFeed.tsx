'use client'

import { useState, useEffect } from 'react'
import { useNews } from '@/hooks/useNews'
import { useGroups } from '@/hooks/useGroups'
import { NewsCard } from './NewsCard'
import { MemberSelect } from './MemberSelect'
import { getMemberColor, getTextColor } from '@/lib/memberColors'

const SOURCE_TABS = [
  { label: 'すべて', value: '' },
  { label: 'RSS', value: 'rss' },
  { label: 'YouTube', value: 'youtube' },
  { label: 'Web', value: 'web' },
]

interface Props {
  groupSlug?: string
  initialMember?: string
}

export function NewsFeed({ groupSlug, initialMember = '' }: Props) {
  const [sourceFilter, setSourceFilter] = useState('')
  const [groupFilter, setGroupFilter] = useState('')
  const [memberFilter, setMemberFilter] = useState(initialMember)
  const [page, setPage] = useState(1)

  const { data: groups } = useGroups()

  // URLパラメータからのメンバー初期値を反映
  useEffect(() => {
    setMemberFilter(initialMember)
    setPage(1)
  }, [initialMember])

  // グループページの場合はprop優先、トップページはドロップダウン選択
  const effectiveGroupSlug = groupSlug || groupFilter || undefined

  const { data, isLoading } = useNews({
    group_slug: effectiveGroupSlug,
    source_type: sourceFilter || undefined,
    member_name: memberFilter || undefined,
    page,
    per_page: 20,
  })

  function handleGroupChange(slug: string) {
    setGroupFilter(slug)
    setMemberFilter('')
    setPage(1)
  }

  function handleMemberChange(name: string) {
    setMemberFilter(name)
    setPage(1)
  }

  function handleSourceChange(val: string) {
    setSourceFilter(val)
    setPage(1)
  }

  return (
    <div>
      {/* フィルターバー */}
      <div className="mb-4 space-y-2">
        {/* ソースタブ */}
        <div className="flex flex-wrap gap-1">
          {SOURCE_TABS.map((tab) => (
            <button
              key={tab.value}
              onClick={() => handleSourceChange(tab.value)}
              className={`rounded-full px-3 py-1 text-sm transition-colors ${
                sourceFilter === tab.value
                  ? 'bg-purple-600 text-white'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* グループ・メンバー選択 */}
        <div className="flex flex-wrap items-center gap-2">
          {/* グループ選択（グループページ以外で表示） */}
          {!groupSlug && groups && groups.length > 0 && (
            <select
              value={groupFilter}
              onChange={(e) => handleGroupChange(e.target.value)}
              className="rounded-md border border-gray-300 bg-white py-1.5 px-3 text-sm text-gray-900 shadow-sm focus:border-purple-500 focus:outline-none focus:ring-1 focus:ring-purple-500"
            >
              <option value="">全グループ</option>
              {groups.map((g) => (
                <option key={g.slug} value={g.slug}>
                  {g.name}
                </option>
              ))}
            </select>
          )}

          {/* メンバー選択 */}
          <MemberSelect
            groupSlug={effectiveGroupSlug}
            selectedMember={memberFilter}
            onChange={handleMemberChange}
          />

          {/* アクティブフィルターバッジ */}
          {memberFilter && (() => {
            const bg = getMemberColor(memberFilter)
            const fg = getTextColor(bg)
            return (
              <span
                className="flex items-center gap-1 rounded-full px-3 py-1 text-sm font-medium"
                style={{ backgroundColor: bg, color: fg }}
              >
                {memberFilter}
                <button onClick={() => handleMemberChange('')} className="ml-1 opacity-70 hover:opacity-100">
                  ×
                </button>
              </span>
            )
          })()}
        </div>
      </div>

      {/* 件数 */}
      {data && (
        <p className="mb-3 text-sm text-gray-400">
          {data.total.toLocaleString()}件
          {memberFilter && ` — 「${memberFilter}」のニュース`}
        </p>
      )}

      {isLoading && (
        <div className="py-12 text-center text-sm text-gray-400">読み込み中...</div>
      )}

      {!isLoading && data?.items.length === 0 && (
        <div className="py-12 text-center">
          <p className="text-sm text-gray-400">ニュースがありません</p>
          <p className="mt-1 text-xs text-gray-300">
            サイドバーの「今すぐ収集」で情報を取得してください
          </p>
        </div>
      )}

      <div className="space-y-3">
        {data?.items.map((item) => (
          <NewsCard key={item.id} item={item} />
        ))}
      </div>

      {data && data.pages > 1 && (
        <div className="mt-6 flex items-center justify-center gap-2">
          <button
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page === 1}
            className="rounded-md border px-3 py-1.5 text-sm disabled:opacity-40"
          >
            前へ
          </button>
          <span className="text-sm text-gray-500">
            {page} / {data.pages}
          </span>
          <button
            onClick={() => setPage((p) => Math.min(data.pages, p + 1))}
            disabled={page === data.pages}
            className="rounded-md border px-3 py-1.5 text-sm disabled:opacity-40"
          >
            次へ
          </button>
        </div>
      )}
    </div>
  )
}
