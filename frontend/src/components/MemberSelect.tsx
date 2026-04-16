'use client'

import { useMembers } from '@/hooks/useMembers'
import { getMemberColor } from '@/lib/memberColors'
import type { Member } from '@/lib/types'

interface Props {
  groupSlug?: string
  selectedMember: string
  onChange: (memberName: string) => void
}

export function MemberSelect({ groupSlug, selectedMember, onChange }: Props) {
  const { data: members } = useMembers(groupSlug)

  if (!members || members.length === 0) return null

  // グループ別にまとめる
  const byGroup: Record<string, Member[]> = {}
  for (const m of members) {
    if (!byGroup[m.group_name]) byGroup[m.group_name] = []
    byGroup[m.group_name].push(m)
  }

  return (
    <div className="flex items-center gap-2">
      <label className="text-sm font-medium text-gray-700 whitespace-nowrap">
        メンバー
      </label>

      {/* カラードット付きカスタムセレクト */}
      <div className="relative">
        <div className="pointer-events-none absolute inset-y-0 left-2.5 flex items-center">
          {selectedMember ? (
            <span
              className="h-2.5 w-2.5 rounded-full"
              style={{ backgroundColor: getMemberColor(selectedMember) }}
            />
          ) : (
            <span className="h-2.5 w-2.5 rounded-full bg-gray-300" />
          )}
        </div>
        <select
          value={selectedMember}
          onChange={(e) => onChange(e.target.value)}
          className="appearance-none rounded-md border border-gray-300 bg-white py-1.5 pl-7 pr-7 text-sm text-gray-900 shadow-sm focus:border-purple-500 focus:outline-none focus:ring-1 focus:ring-purple-500"
        >
          <option value="">全員</option>
          {Object.entries(byGroup).map(([groupName, groupMembers]) => (
            <optgroup key={groupName} label={groupName}>
              {groupMembers.map((m) => (
                <option key={m.id} value={m.name}>
                  {m.name}
                </option>
              ))}
            </optgroup>
          ))}
        </select>
        <div className="pointer-events-none absolute inset-y-0 right-2 flex items-center">
          <svg className="h-4 w-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </div>
      </div>
    </div>
  )
}
