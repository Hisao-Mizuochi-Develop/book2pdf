// React ライブラリ全体を名前空間として読み込み
// ComponentProps<"label"> 等の型を使用するために使用する
import * as React from "react"

// Tailwind CSS クラス名ユーティリティ関数を読み込み
// clsx + tailwind-merge で条件付きクラス結合を行う
import { cn } from "@/lib/utils"

function Label({ className, ...props }: React.ComponentProps<"label">) {
  return (
    <label
      data-slot="label"
      className={cn(
        "flex items-center gap-2 text-sm leading-none font-medium select-none group-data-[disabled=true]:pointer-events-none group-data-[disabled=true]:opacity-50 peer-disabled:cursor-not-allowed peer-disabled:opacity-50",
        className
      )}
      {...props}
    />
  )
}

export { Label }
