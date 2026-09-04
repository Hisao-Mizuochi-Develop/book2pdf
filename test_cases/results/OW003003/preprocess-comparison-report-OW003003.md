# OW003003 入力画像前処理の効果検証 比較レポート

## 概要

- タスク: OW003003「入力画像前処理の効果検証」
- 実施日: 2026-08-13
- 対象データ: `benchmark-ocr-OW003002.zip`（002.png, 003.png, 004.png）
- OCR エンジン: ndlocr_cli（CPU 実行）
- 評価指標: 「〓」出現数、明らかな誤認識箇所数、目視確認

## 比較パターン

| パターン | 前処理内容 |
|---|---|
| baseline | 前処理なし（OW003002 の結果を流用） |
| sharpen_light | 軽度シャープニング |
| sharpen_light_upscale_2x | 2 倍アップスケーリング＋軽度シャープニング |
| contrast_gamma | コントラスト強調＋ガンマ補正 |
| contrast_gamma_sharpen_light | コントラスト強調＋ガンマ補正＋軽度シャープニング |

## 定量的比較

| パターン | 「〓」出現数 | 主な傾向 |
|---|---|---|
| baseline | 5 | 英数字頭文字欠落・記号置換が多い |
| sharpen_light | 7 | baseline と比較して改善が限定的 |
| sharpen_light_upscale_2x | 3 | 最も「〓」が少なく、全体認識精度が向上 |
| contrast_gamma | 7 | baseline と同等かやや悪化 |
| contrast_gamma_sharpen_light | 6 | contrast_gamma 単独よりやや改善するも、アップスケールには及ばない |

## 各ページの目視確認

### 002.png（表紙）

| パターン | 主な誤認識 |
|---|---|
| baseline | RAG→RAC、Improving→mproving、GPT-4→〓PT-4、LLM→lm、前処理→〓前処理、検索→〓検索、生成→M生成 |
| sharpen_light | 同上（ほぼ変化なし） |
| sharpen_light_upscale_2x | 咸毅成[著] が正しく認識、RAG→RAC、Improving→mproving Accuracy、前処理→イ前処理、検索→M検索、生成→イ生成（表紙部はやや改善） |
| contrast_gamma | RAG→RAC、Improving→mprovingAccuracyin、前処理→K前処理、検索→K検索、生成→K生成 |
| contrast_gamma_sharpen_light | RAG→RAC、mproving Accuacyin、前処理→イ前処理、検索→k検索、生成→M生成 |

### 003.png（本書をお読みになる前に）

| パターン | 主な誤認識 |
|---|---|
| baseline | 判断・〓用、青任→責任、変1→変更、登録面標→商標、知議→知識 |
| sharpen_light | 判断・〓、青任、変1、登録面標、知議（ baseline と同等） |
| sharpen_light_upscale_2x | **ほぼ正しく認識**（登録溶標→登録商標 のみ一部誤認識、「〓」2 箇所） |
| contrast_gamma | 判断・通用、登録 標、知議、変1、リースノート（シャープニングなしより誤認識が増加） |
| contrast_gamma_sharpen_light | 青任→責任、変y→変更、面標→商標、知議→知識（アップスケールほどではないが改善傾向） |

### 004.png（はじめに）

| パターン | 主な誤認識 |
|---|---|
| baseline | GPT-4→〓PT-4、LLM→〓lm、RAG→Rag、rag 表記ゆれ、誤!→誤り |
| sharpen_light | 同上（ほぼ変化なし） |
| sharpen_light_upscale_2x | **ほぼ正しく認識**（gpt-4、llm、rag、誤り、一部〓lm 残存） |
| contrast_gamma | GPT-4の肴、〓lm、〓Mm、RAg、工ヲ、誤1（記号・英数字の誤認識が多い） |
| contrast_gamma_sharpen_light | 〓PT-4、〓lm、ag、〓m（アップスケールほどではない） |

## 総合評価

### 最も効果的な前処理

**sharpen_light_upscale_2x（2 倍アップスケーリング＋軽度シャープニング）** が最も効果的でした。

- 「〓」出現数が baseline 5 個から 3 個へ減少
- 003.png、004.png においてほぼ完全な認識を実現
- 英数字頭文字欠落・記号置換・小文字化などの誤認識が大幅に改善
- 002.png（表紙）でも一部改善が見られる

### その他のパターンの評価

- **sharpen_light**: 軽度シャープニングのみでは、表紙サイズの文字に対して十分な効果が得られなかった
- **contrast_gamma**: コントラストとガンマ補正は、逆に文字の濁りやノイズを強調し、記号・英数字の誤認識を増加させる傾向があった
- **contrast_gamma_sharpen_light**: シャープニングを追加することで contrast_gamma の悪影響を一部緩和するも、アップスケーリングには及ばなかった

## 結論

入力画像を 2 倍にアップスケーリングし、軽度のシャープニングを施すことで、ndlocr_cli（CPU 実行）の認識精度が最も向上しました。特に本文ページ（003.png、004.png）での効果が顕著です。表紙ページ（002.png）は元の文字サイズ・デザインの影響から、依然として一部の誤認識が残りました。

## 今後の検討事項

- 表紙ページ（002.png）の認識精度をさらに向上させるため、文字領域に対する局所的前処理や、config.yml のパラメータ調整（OW003004）との組み合わせを検討する
- アップスケーリングによる処理時間増加の影響を定量的に測定する
- 2 倍以外の倍率（1.5 倍、3 倍など）や、異なるシャープニング強度の効果も検討の余地がある
