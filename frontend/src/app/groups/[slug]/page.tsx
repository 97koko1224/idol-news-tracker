// Server Component - searchParams をプロップで受け取る
import { GroupPageClient } from './GroupPageClient'

interface Props {
  params: { slug: string }
  searchParams: { member?: string }
}

export default function GroupPage({ params, searchParams }: Props) {
  return (
    <GroupPageClient
      slug={params.slug}
      initialMember={searchParams.member ?? ''}
    />
  )
}
