import useSWR from 'swr'
import { fetcher } from '@/lib/api'
import type { NewsList } from '@/lib/types'

interface NewsParams {
  group_slug?: string
  source_type?: string
  member_name?: string
  date_from?: string
  date_to?: string
  page?: number
  per_page?: number
}

export function useNews(params: NewsParams = {}) {
  const query = new URLSearchParams()
  if (params.group_slug) query.set('group_slug', params.group_slug)
  if (params.source_type) query.set('source_type', params.source_type)
  if (params.member_name) query.set('member_name', params.member_name)
  if (params.date_from) query.set('date_from', params.date_from)
  if (params.date_to) query.set('date_to', params.date_to)
  if (params.page) query.set('page', String(params.page))
  if (params.per_page) query.set('per_page', String(params.per_page))

  const url = `/api/news?${query.toString()}`
  return useSWR<NewsList>(url, fetcher, {
    refreshInterval: 5 * 60_000,
    revalidateOnFocus: true,
  })
}
