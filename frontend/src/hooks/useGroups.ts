import useSWR from 'swr'
import { fetcher } from '@/lib/api'
import type { Group } from '@/lib/types'

export function useGroups() {
  return useSWR<Group[]>('/api/groups', fetcher, {
    refreshInterval: 60_000,
  })
}
