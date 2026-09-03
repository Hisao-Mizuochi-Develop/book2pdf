// React ライブラリ全体を名前空間として読み込み
// ComponentProps<"input"> 等の型を使用するために使用する
import * as React from "react"
// Base UI ライブラリからアクセシビリティ対応の入力フィールドプリミティブを読み込み
// ARIA 対応・キーボードナビゲーション・フォーカス管理が組み込まれている
import { Input as InputPrimitive } from "@base-ui/react/input"

// Tailwind CSS クラス名ユーティリティ関数を読み込み
// clsx + tailwind-merge で条件付きクラス結合を行う
import { cn } from "@/lib/utils"

function Input({ className, type, ...props }: React.ComponentProps<"input">) {
  return (
    <InputPrimitive
      type={type}
      data-slot="input"
      className={cn(
        "h-8 w-full min-w-0 rounded-lg border border-input bg-transparent px-2.5 py-1 text-base transition-colors outline-none file:inline-flex file:h-6 file:border-0 file:bg-transparent file:text-sm file:font-medium file:text-foreground placeholder:text-muted-foreground focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50 disabled:pointer-events-none disabled:cursor-not-allowed disabled:bg-input/50 disabled:opacity-50 aria-invalid:border-destructive aria-invalid:ring-3 aria-invalid:ring-destructive/20 md:text-sm dark:bg-input/30 dark:disabled:bg-input/80 dark:aria-invalid:border-destructive/50 dark:aria-invalid:ring-destructive/40",
        className
      )}
      {...props}
    />
  )
}

export { Input }
