const SOURCE_CONFIG = {
  rss: { label: 'RSS', bg: 'bg-orange-100', text: 'text-orange-700' },
  youtube: { label: 'YouTube', bg: 'bg-red-100', text: 'text-red-700' },
  web: { label: 'Web', bg: 'bg-green-100', text: 'text-green-700' },
} as const

type SourceType = keyof typeof SOURCE_CONFIG

export function SourceBadge({ type }: { type: string }) {
  const cfg = SOURCE_CONFIG[type as SourceType] ?? {
    label: type,
    bg: 'bg-gray-100',
    text: 'text-gray-600',
  }
  return (
    <span
      className={`inline-block rounded px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide ${cfg.bg} ${cfg.text}`}
    >
      {cfg.label}
    </span>
  )
}
