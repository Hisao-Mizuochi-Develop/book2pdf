/**
 * =============================================================================
 * Button コンポーネント
 * =============================================================================
 * shadcn/ui の Button コンポーネント。
 * @base-ui/react/button をベースに、Tailwind CSS v4 でスタイルを定義している。
 *
 * 【このコンポーネントの役割】
 * アプリケーション全体で一貫したボタンスタイルを提供する。
 * variant（見た目の種類）と size（大きさ）の組み合わせで、様々な用途に対応する。
 *
 * 【使い方（例）】
 *   <Button>保存する</Button>                  // デフォルト（primary）
 *   <Button variant="outline">キャンセル</Button>  // 枠線のみのボタン
 *   <Button size="sm">小さいボタン</Button>    // 小サイズ
 * =============================================================================
 */

/* @base-ui/react/button: アクセシビリティ対応済みの低レベル Button プリミティブ
   ARIA 対応・キーボードナビゲーション・フォーカス管理が組み込まれている */
import { Button as ButtonPrimitive } from "@base-ui/react/button"

/* class-variance-authority (cva): 同じコンポーネントで複数のバリエーションを
   型安全に管理するライブラリ。variant と size の組み合わせを定義する */
import { cva, type VariantProps } from "class-variance-authority"

/* cn(): Tailwind CSS のクラス名をマージするユーティリティ。
   競合するクラス（例: px-2 と px-4）を自動的に解決し、後勝ちにする */
import { cn } from "@/lib/utils"

/* =============================================================================
 * ボタンのスタイルバリエーション定義（cva）
 * =============================================================================
 * cva（class-variance-authority）は「基本クラス + variant 別クラス + size 別クラス」を
 * 組み合わせて、1つのクラス文字列を生成する。
 *
 * 1つ目の引数: 全バリエーション共通の基本クラス（レイアウト・トランジション等）
 * 2つ目の引数: variant と size の定義（variants + defaultVariants）
 * ============================================================================= */
const buttonVariants = cva(
  /*
   * 基本クラス: すべての Button に共通して適用される Tailwind クラス
   *
   * group/button        : 子要素で group-hover/button 等が使えるグループ名
   * inline-flex         : インラインフレックスコンテナ（横並び）
   * shrink-0            : 親要素が小さくなっても縮まない
   * items-center        : フレックスアイテムを垂直中央揃え
   * justify-center      : フレックスアイテムを水平中央揃え
   * rounded-lg          : 角丸（大）
   * border border-transparent : 透明なボーダー（ホバー時の枠線変化の土台）
   * bg-clip-padding     : 背景のクリップ領域を padding-box に
   * text-sm             : フォントサイズ 0.875rem（14px）
   * font-medium         : フォントウェイト 500（中くらいの太さ）
   * whitespace-nowrap   : テキストを折り返さない（1行表示を強制）
   * transition-all      : すべてのプロパティにトランジションアニメーション
   * outline-none        : デフォルトのアウトラインを削除（カスタムフォーカススタイルで代替）
   * select-none         : テキスト選択を無効化
   * disabled:pointer-events-none : disabled 時にクリックできない
   * disabled:opacity-50  : disabled 時に半透明に
   * aria-invalid:*       : バリデーションエラー時のスタイル
   * [&_svg]             : 子要素の SVG アイコンに適用するスタイル
   */
  "group/button inline-flex shrink-0 items-center justify-center rounded-lg border border-transparent bg-clip-padding text-sm font-medium whitespace-nowrap transition-all outline-none select-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50 active:not-aria-[haspopup]:translate-y-px disabled:pointer-events-none disabled:opacity-50 aria-invalid:border-destructive aria-invalid:ring-3 aria-invalid:ring-destructive/20 dark:aria-invalid:border-destructive/50 dark:aria-invalid:ring-destructive/40 [&_svg]:pointer-events-none [&_svg]:shrink-0 [&_svg:not([class*='size-'])]:size-4",
  {
    /* -------------------------------------------------------------------------
     * variant: ボタンの「見た目の種類」を定義
     * -------------------------------------------------------------------------
     * 【default】  主要アクションボタン（保存・確定・進むなど）
     * 【outline】  サブアクション（キャンセル・戻るなど）。枠線のみで背景は透明
     * 【secondary】補助的なボタン。控えめな背景色で目立たない
     * 【ghost】    最小限のボタン。ホバー時のみ背景が出る。アイコンボタン等に
     * 【destructive】削除・危険なアクション。赤系の色で注意を引く
     * 【link】     テキストリンク風。下線付きで、ボタン要素として使う場合に
     * ------------------------------------------------------------------------- */
    variants: {
      variant: {
        /**
         * default バリアント
         * 用途: 主要アクションボタン（保存・確定・実行など）
         * 見た目: primary（青）の背景に白文字。最も目立つボタン。
         */
        default: "bg-primary text-primary-foreground hover:bg-primary/80",

        /**
         * outline バリアント
         * 用途: サブアクション（キャンセル・戻る・中立的な選択肢）
         * 見た目: 枠線のみで背景は透明。ホバーで背景が薄く出る。
         */
        outline:
          "border-border bg-background hover:bg-muted hover:text-foreground aria-expanded:bg-muted aria-expanded:text-foreground dark:border-input dark:bg-input/30 dark:hover:bg-input/50",

        /**
         * secondary バリアント
         * 用途: 補助的なボタン（追加オプション・詳細設定など）
         * 見た目: 控えめなグレー背景。ページ内で目立ちすぎない。
         */
        secondary:
          "bg-secondary text-secondary-foreground hover:bg-[color-mix(in_oklch,var(--secondary),var(--foreground)_5%)] aria-expanded:bg-secondary aria-expanded:text-secondary-foreground",

        /**
         * ghost バリアント
         * 用途: 最小限の UI（アイコンボタン・ツールバーなど）
         * 見た目: 通常は背景なし。ホバー・展開時のみ薄い背景。
         */
        ghost:
          "hover:bg-muted hover:text-foreground aria-expanded:bg-muted aria-expanded:text-foreground dark:hover:bg-muted/50",

        /**
         * destructive バリアント
         * 用途: 削除・取り消し・危険なアクション（データ削除など）
         * 見た目: 赤系の背景。ユーザーに注意を促す。
         */
        destructive:
          "bg-destructive/10 text-destructive hover:bg-destructive/20 focus-visible:border-destructive/40 focus-visible:ring-destructive/20 dark:bg-destructive/20 dark:hover:bg-destructive/30 dark:focus-visible:ring-destructive/40",

        /**
         * link バリアント
         * 用途: テキストリンク風のボタン（詳細ページへ移動など）
         * 見た目: 下線付きテキスト。ホバーで下線が強調される。
         */
        link: "text-primary underline-offset-4 hover:underline",
      },

      /* -----------------------------------------------------------------------
       * size: ボタンの「大きさ」を定義
       * -----------------------------------------------------------------------
       * 【default】 標準サイズ。ほとんどの場面でこのサイズを使う
       * 【xs】     極小サイズ。タイトなスペースや補助ボタンに
       * 【sm】     小サイズ。フォーム内や並列配置で使う
       * 【lg】     大サイズ。他の要素と区別したい主要ボタンに
       * 【icon】   アイコンのみ。正方形で中央にアイコンを配置
       * 【icon-xs】極小のアイコンボタン
       * 【icon-sm】小さいアイコンボタン
       * 【icon-lg】大きいアイコンボタン
       * ----------------------------------------------------------------------- */
      size: {
        /**
         * default サイズ
         * 高さ: h-8（32px）
         * 適用場面: フォーム送信ボタン、ダイアログの確定ボタンなど
         */
        default:
          "h-8 gap-1.5 px-2.5 has-data-[icon=inline-end]:pr-2 has-data-[icon=inline-start]:pl-2",

        /**
         * xs サイズ（極小）
         * 高さ: h-6（24px）
         * 適用場面: タグ内の削除ボタン、補助リンクなど
         */
        xs: "h-6 gap-1 rounded-[min(var(--radius-md),10px)] px-2 text-xs in-data-[slot=button-group]:rounded-lg has-data-[icon=inline-end]:pr-1.5 has-data-[icon=inline-start]:pl-1.5 [&_svg:not([class*='size-'])]:size-3",

        /**
         * sm サイズ（小）
         * 高さ: h-7（28px）
         * 適用場面: フォーム内の補助ボタン、テーブル内のアクションなど
         */
        sm: "h-7 gap-1 rounded-[min(var(--radius-md),12px)] px-2.5 text-[0.8rem] in-data-[slot=button-group]:rounded-lg has-data-[icon=inline-end]:pr-1.5 has-data-[icon=inline-start]:pl-1.5 [&_svg:not([class*='size-'])]:size-3.5",

        /**
         * lg サイズ（大）
         * 高さ: h-9（36px）
         * 適用場面: ページの主要 CTA（Call To Action）、目立たせたいボタン
         */
        lg: "h-9 gap-1.5 px-2.5 has-data-[icon=inline-end]:pr-2 has-data-[icon=inline-start]:pl-2",

        /**
         * icon サイズ（アイコンのみ・標準）
         * サイズ: 32px × 32px の正方形
         * 適用場面: ツールバー、ヘッダーアクション、閉じるボタンなど
         */
        icon: "size-8",

        /**
         * icon-xs サイズ（アイコンのみ・極小）
         * サイズ: 24px × 24px
         */
        "icon-xs":
          "size-6 rounded-[min(var(--radius-md),10px)] in-data-[slot=button-group]:rounded-lg [&_svg:not([class*='size-'])]:size-3",

        /**
         * icon-sm サイズ（アイコンのみ・小）
         * サイズ: 28px × 28px
         */
        "icon-sm":
          "size-7 rounded-[min(var(--radius-md),12px)] in-data-[slot=button-group]:rounded-lg",

        /**
         * icon-lg サイズ（アイコンのみ・大）
         * サイズ: 36px × 36px
         */
        "icon-lg": "size-9",
      },
    },

    /* -------------------------------------------------------------------------
     * デフォルト値: variant と size を指定しなかった場合のデフォルト
     * ------------------------------------------------------------------------- */
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)

/* =============================================================================
 * Button コンポーネント本体
 * =============================================================================
 * @base-ui/react/button から継承した props に加え、variant と size を受け取る。
 * className で追加の Tailwind クラスを指定できる（cn() でマージされる）。
 *
 * @param props - ButtonPrimitive.Props（イベントハンドラ、disabled 等）に
 *                VariantProps<typeof buttonVariants>（variant, size）を合成
 * ============================================================================= */
function Button({
  className,
  variant = "default",
  size = "default",
  ...props
}: ButtonPrimitive.Props & VariantProps<typeof buttonVariants>) {
  return (
    /* data-slot="button": shadcn/ui のコンポーネント識別子（スタイリングやテスト用） */
    <ButtonPrimitive
      data-slot="button"
      /* cn() で基本スタイル + variant/size 別クラス + 追加 className をマージ */
      className={cn(buttonVariants({ variant, size, className }))}
      {...props}
    />
  )
}

/* buttonVariants: 単体でも使える（コンポーネント外でクラス文字列が必要な時に） */
export { Button, buttonVariants }
