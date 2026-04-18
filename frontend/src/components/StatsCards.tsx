'use client'

import useSWR from 'swr'
import { fetcher } from '@/lib/api'
import type { Stats } from '@/lib/types'

function StatCard({ label, value }: { label: string; value: number | string }) {
  return (
    <div className="rounded-lg border border-gray-100 bg-white p-4 shadow-sm">
      <p className="text-xs font-medium text-gray-400">{label}</p>
      <p className="mt-1 text-2xl font-bold text-gray-900">{value}</p>
    </div>
  )
}

export function StatsCards() {
  const { data } = useSWR<Stats>('/api/stats', fetcher, { refreshInterval: 60_000 })

  if (!data) return null

  const topGroup = data.by_group[0]

  return (
    <div className="mb-6 grid grid-cols-1 sm:grid-cols-3 gap-3">
      <StatCard label="今日のニュース" value={data.items_today} />
      <StatCard label="今週のニュース" value={data.items_this_week} />
      <StatCard label="最も活発なグループ" value={topGroup?.name ?? '-'} />
    </div>
  )
}
