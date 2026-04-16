export const fetcher = (url: string) =>
  fetch(url).then((r) => {
    if (!r.ok) throw new Error(`API error ${r.status}`)
    return r.json()
  })

export async function triggerCollection(): Promise<void> {
  const res = await fetch('/api/collect', { method: 'POST' })
  if (!res.ok) throw new Error('Collection trigger failed')
}
