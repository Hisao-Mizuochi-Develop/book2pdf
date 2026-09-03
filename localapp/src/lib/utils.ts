// Tailwind CSS クラス名を条件付きで結合するライブラリを読み込み
// clsx: 条件に応じてクラス名を動的に組み立てる, ClassValue: 入力値の型
import { clsx, type ClassValue } from "clsx"
// Tailwind CSS のクラス名衝突を解決するライブラリを読み込み
// twMerge: 複数のユーティリティクラス間で重複・矛盾を解消する
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}
