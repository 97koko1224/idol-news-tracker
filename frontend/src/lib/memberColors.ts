// KAWAII LAB. 全メンバーカラー
export const MEMBER_COLORS: Record<string, string> = {
  // FRUITS ZIPPER
  "月足天音":   "#EF4444", // 赤
  "鎮西寿々歌": "#F97316", // オレンジ
  "早瀬ノエル": "#EAB308", // 黄色
  "櫻井優衣":   "#6EE7B7", // ミントグリーン
  "真中まな":   "#7DD3FC", // 水色
  "仲川瑠夏":   "#C4B5FD", // ラベンダー
  "松本かれん": "#F472B6", // ピンク

  // CANDY TUNE
  "宮野静":     "#A855F7", // 紫
  "福山梨乃":   "#93C5FD", // ライトブルー
  "桐原美月":   "#3B82F6", // ブルー
  "南なつ":     "#FB923C", // オレンジ
  "小川奈々子": "#34D399", // ミントグリーン
  "立花琴未":   "#F87171", // レッド
  "村川緋杏":   "#EC4899", // パッションピンク

  // SWEET STEADY
  "音井結衣":   "#7DD3FC", // 水色
  "奥田彩友":   "#60A5FA", // ブルー
  "栗田なつか": "#F9A8D4", // ピンク
  "塩川莉世":   "#DDD6FE", // 紫
  "庄司なぎさ": "#FDBA74", // オレンジ
  "白石まゆみ": "#FCA5A5", // 赤
  "山内咲奈":   "#FDE047", // 黄色

  // CUTIE STREET
  "古澤里紗":   "#FDE047", // 黄色
  "佐野愛花":   "#F87171", // 赤
  "板倉可奈":   "#6EE7B7", // ミントグリーン
  "増田彩乃":   "#60A5FA", // 青
  "川本笑瑠":   "#FB923C", // オレンジ
  "梅田みゆ":   "#93C5FD", // 水色
  "真鍋凪咲":   "#C084FC", // 紫
  "桜庭遥花":   "#F472B6", // ピンク

  // MORE STAR
  "新井心菜":   "#FB923C", // オレンジ
  "遠藤まりん": "#3B82F6", // 青
  "笹原なな花": "#FACC15", // 黄色
  "鈴木花梨":   "#34D399", // ミントグリーン
  "高梨ゆな":   "#7DD3FC", // 水色
  "中山こはく": "#9CA3AF", // シルバー
  "萩田そら":   "#EF4444", // 赤
  "森田あみ":   "#F9A8D4", // ピンク
  "山本るしあ": "#A78BFA", // パープル
}

export function getMemberColor(name: string): string {
  return MEMBER_COLORS[name] ?? "#9CA3AF"
}

// 背景色から読みやすいテキストカラーを返す
export function getTextColor(bgHex: string): string {
  const r = parseInt(bgHex.slice(1, 3), 16)
  const g = parseInt(bgHex.slice(3, 5), 16)
  const b = parseInt(bgHex.slice(5, 7), 16)
  const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
  return luminance > 0.65 ? "#1f2937" : "#ffffff"
}
