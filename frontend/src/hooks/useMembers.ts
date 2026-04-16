import useSWR from 'swr'
import { fetcher } from '@/lib/api'
import type { Member } from '@/lib/types'

export function useMembers(groupSlug?: string) {
  const url = groupSlug
    ? `/api/members?group_slug=${groupSlug}`
    : '/api/members'
  return useSWR<Member[]>(url, fetcher)
}
