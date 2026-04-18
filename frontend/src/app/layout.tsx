import type { Metadata } from 'next'
import '@/styles/globals.css'
import { Sidebar } from '@/components/Sidebar'

export const metadata: Metadata = {
  title: 'KAWAII LAB. News Tracker',
  description: 'KAWAII LAB. 最新情報収集プラットフォーム',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ja">
      <body className="bg-gray-50 text-gray-900">
        <Sidebar />
        <main className="min-h-screen p-4 pt-20 md:ml-60 md:p-6 md:pt-6">{children}</main>
      </body>
    </html>
  )
}
