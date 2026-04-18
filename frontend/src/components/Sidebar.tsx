'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { useState } from 'react'
import { useGroups } from '@/hooks/useGroups'
import { triggerCollection } from '@/lib/api'
import useSWR from 'swr'
import { fetcher } from '@/lib/api'
import { getMemberColor, getTextColor } from '@/lib/memberColors'
import type { Stats } from '@/lib/types'

export function Sidebar() {
  const pathname = usePathname()
  const { data: groups } = useGroups()
  const { data: stats } = useSWR<Stats>('/api/stats', fetcher, { refreshInterval: 60_000 })
  const [collecting, setCollecting] = useState(false)
  const [expandedGroup, setExpandedGroup] = useState<string | null>(null)
  const [mobileOpen, setMobileOpen] = useState(false)

  async function handleCollect() {
    setCollecting(true)
    setMobileOpen(false)
    try {
      await triggerCollection()
      alert('収集を開始しました。完了までしばらくお待ちください。')
    } catch {
      alert('収集の開始に失敗しました。')
    } finally {
      setCollecting(false)
    }
  }

  const navContent = (
    <>
      <nav className="space-y-1">
        <Link
          href="/"
          onClick={() => setMobileOpen(false)}
          className={`flex items-center justify-between rounded-md px-3 py-2 text-sm font-medium transition-colors ${
            pathname === '/'
              ? 'bg-purple-50 text-purple-700'
              : 'text-gray-600 hover:bg-gray-50'
          }`}
        >
          <span>すべてのニュース</span>
          {stats && (
            <span className="rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-500">
              {stats.items_today}
            </span>
          )}
        </Link>
      </nav>

      {groups && groups.length > 0 && (
        <div className="mt-4">
          <p className="mb-2 px-3 text-[10px] font-semibold uppercase tracking-wider text-gray-400">
            グループ
          </p>
          <nav className="space-y-0.5">
            {groups.map((g) => (
              <div key={g.slug}>
                <button
                  onClick={() =>
                    setExpandedGroup(expandedGroup === g.slug ? null : g.slug)
                  }
                  className={`flex w-full items-center justify-between rounded-md px-3 py-2 text-sm transition-colors ${
                    pathname === `/groups/${g.slug}`
                      ? 'bg-purple-50 font-medium text-purple-700'
                      : 'text-gray-600 hover:bg-gray-50'
                  }`}
                >
                  <span className="truncate text-left">{g.name}</span>
                  <div className="flex items-center gap-1 shrink-0 ml-1">
                    <span className="text-xs text-gray-400">{g.item_count}</span>
                    <span className="text-[10px] text-gray-300">
                      {expandedGroup === g.slug ? '▲' : '▼'}
                    </span>
                  </div>
                </button>

                {expandedGroup === g.slug && (
                  <GroupMemberLinks groupSlug={g.slug} onSelect={() => setMobileOpen(false)} />
                )}
              </div>
            ))}
          </nav>
        </div>
      )}

      <div className="mt-auto pt-6">
        {stats?.last_collected_at && (
          <p className="mb-2 px-1 text-[10px] text-gray-400">
            最終収集:{' '}
            {new Date(stats.last_collected_at + 'Z').toLocaleString('ja-JP', {
              month: 'short',
              day: 'numeric',
              hour: '2-digit',
              minute: '2-digit',
            })}
          </p>
        )}
        <button
          onClick={handleCollect}
          disabled={collecting}
          className="w-full rounded-md bg-purple-600 px-3 py-2 text-sm font-medium text-white transition-colors hover:bg-purple-700 disabled:opacity-50"
        >
          {collecting ? '収集中...' : '今すぐ収集'}
        </button>
      </div>
    </>
  )

  return (
    <>
      {/* モバイル用トップヘッダー */}
      <header className="md:hidden fixed top-0 left-0 right-0 z-40 flex items-center justify-between bg-white border-b border-gray-200 px-4 py-3">
        <div className="flex items-center gap-2">
          <span className="text-base">✦</span>
          <div>
            <p className="text-sm font-bold text-gray-900 leading-tight">KAWAII LAB.</p>
            <p className="text-[10px] text-gray-400">News Tracker</p>
          </div>
        </div>
        <button
          onClick={() => setMobileOpen(true)}
          className="flex flex-col gap-1.5 p-2 rounded-md hover:bg-gray-100"
          aria-label="メニューを開く"
        >
          <span className="block h-0.5 w-5 bg-gray-600" />
          <span className="block h-0.5 w-5 bg-gray-600" />
          <span className="block h-0.5 w-5 bg-gray-600" />
        </button>
      </header>

      {/* モバイル用オーバーレイ */}
      {mobileOpen && (
        <div
          className="md:hidden fixed inset-0 z-40 bg-black/40"
          onClick={() => setMobileOpen(false)}
        />
      )}

      {/* サイドバー本体 */}
      <aside
        className={`
          fixed left-0 top-0 h-screen w-64 overflow-y-auto border-r border-gray-200 bg-white px-4 py-6 flex flex-col z-50
          transition-transform duration-200 ease-in-out
          ${mobileOpen ? 'translate-x-0' : '-translate-x-full'}
          md:translate-x-0 md:w-60
        `}
      >
        {/* デスクトップ用ヘッダー */}
        <div className="mb-6 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-lg">✦</span>
            <div>
              <h1 className="text-sm font-bold text-gray-900 leading-tight">KAWAII LAB.</h1>
              <p className="text-[10px] text-gray-400">News Tracker</p>
            </div>
          </div>
          {/* モバイル用閉じるボタン */}
          <button
            onClick={() => setMobileOpen(false)}
            className="md:hidden text-gray-400 hover:text-gray-600 text-xl leading-none"
            aria-label="閉じる"
          >
            ×
          </button>
        </div>

        {navContent}
      </aside>
    </>
  )
}

function GroupMemberLinks({ groupSlug, onSelect }: { groupSlug: string; onSelect: () => void }) {
  const { data: members } = useSWR(
    `/api/members?group_slug=${groupSlug}`,
    fetcher
  )

  if (!members) return null

  return (
    <div className="ml-3 mb-1 border-l border-gray-100 pl-3 space-y-0.5">
      <Link
        href={`/groups/${groupSlug}`}
        onClick={onSelect}
        className="block rounded px-2 py-1.5 text-xs text-gray-500 hover:bg-gray-50"
      >
        全員
      </Link>
      {members.map((m: { id: number; name: string }) => {
        const bg = getMemberColor(m.name)
        return (
          <Link
            key={m.id}
            href={`/groups/${groupSlug}?member=${encodeURIComponent(m.name)}`}
            onClick={onSelect}
            className="flex items-center gap-1.5 rounded px-2 py-1.5 text-xs text-gray-600 hover:bg-gray-50"
          >
            <span
              className="inline-block h-2.5 w-2.5 shrink-0 rounded-full"
              style={{ backgroundColor: bg }}
            />
            {m.name}
          </Link>
        )
      })}
    </div>
  )
}
