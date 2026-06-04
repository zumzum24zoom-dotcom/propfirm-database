---
type: firm
title: "The5ers"
slug: "the5ers"
firm: "the5ers"
---

## 断面① Drawdown

The5ersの各プランにおけるドローダウンは、日次損失と最大損失で構成される。Bootcampプランのみ、ChallengeとFundedで日次および最大損失の設定が異なる仕様である。

### DD比較テーブル
| プラン名 | 日次損失上限 | 計算基準（日次） | 最大損失上限 | 計算基準（最大） |
|---|---|---|---|---|
| High Stakes | 5% | Trailing（Higher B or E EOD） | 10% | Static |
| Hyper-Growth | 3% | Trailing（Higher B or E EOD） | 6% | Static |
| Bootcamp (Challenge) | ー | ー | 5% | Static |
| Bootcamp (Funded) | 3% | Trailing（Higher B or E EOD） | 4% | Static |
| Pro-Growth | 3% | Trailing（Higher B or E EOD） | 6% | Static |

日次損失の計算基準となるリセット時刻は、全プラン共通で00:00 MT5 Server Time（日本時間換算: 冬11:00 / 夏06:00）である。Trailing（Higher B or E EOD）は、前日のサーバー時間0時時点の残高または有効証拠金の高い方を基準として算出される仕様である。

### 合格に向けての注意点
日次損失は残高または有効証拠金の高い方を基準とするため、日を跨いで含み益がある場合は翌日の許容損失額が変動する仕様である。BootcampのChallengeでは日次損失上限が設定されていない。

### 出金に向けての注意点
Funded口座到達後もDD計算基準はChallengeと同様の仕様が適用される（Bootcampを除く）。日々の残高と有効証拠金の推移に基づく資金管理となる。

### 特殊ルール
Hyper-GrowthおよびBootcamp（Funded）の日次損失制限は、失格ではなく当日の取引が一時停止（Daily Pause）される保護仕様である。

---

## 断面② 取引ルール

取引における一貫性ルールの設定は存在せず、プランごとにニュース時の取引制限やEA制限などの仕様が分かれている。

### Consistency Rule プラン別適用状況
| プラン | Challenge | Funded | 備考 |
|---|---|---|---|
| High Stakes | なし（明示） | なし（明示） | ー |
| Hyper-Growth | なし（明示） | なし（明示） | ー |
| Bootcamp | 記載なし | 記載なし | ー |
| Pro-Growth | 記載なし | 記載なし | ー |

### 第1部. 全プラン共通の取引制限
週末およびオーバーナイトのポジション持ち越しは全プランで許可されている。自動売買（EA）の使用は可能であるが、プラットフォーム上でストップロスが可視化されない「ステルスモード」の使用は全プランで禁止されている。アービトラージや高頻度取引（HFT）、他者と同じ取引になるサードパーティ製EAの使用等は禁止行為である。

### 第2部. プラン間で差分のあるルール
| ルール項目 | プラン別の違い |
|---|---|
| ニュース取引制限 | High Stakes: 発表前後2分間新規注文禁止 / Hyper-Growth・Bootcamp: ブラケット戦略禁止 / Pro-Growth: 記載なし |
| コピートレード | High Stakes・Bootcamp: 他者コピー禁止 / Hyper-Growth: 自己口座間のみ総資金$500Kまで許可 / Pro-Growth: 記載なし |
| ストップロス | High Stakes・Hyper-Growth・Pro-Growth: 任意（推奨） / Bootcamp: 必須（リスク2%以下） |
| 最低取引日数（合格） | High Stakes: 3日 / Hyper-Growth: 0日 / Bootcamp: 記載なし / Pro-Growth: 3日 |

### 合格に向けての注意点
Bootcampでは全ポジションに対するストップロスの設定が必須要件である。High Stakesでは重要指標発表時の前後2分間の新規注文が禁止されているため、経済指標カレンダーの確認を伴う仕様である。

### 出金に向けての注意点
Funded口座においても、Challengeと同様の取引ルールおよび禁止行為の制約が適用される仕様である。各プラン特有のコピートレード制限やニュース時の注文制約への準拠が求められる。

---

## 断面③ 出金までの流れ

出金は隔週の頻度で実施され、暗号通貨や銀行送金等の受取手段が提供される。プランにより最低出金額の有無や初期の利益分配率が異なる仕様である。

### 出金条件テーブル
| プラン名 | 頻度 | 最低取引日数（出金） | 一貫性ルール | 最低利益 | 利益分配 | 備考 |
|---|---|---|---|---|---|---|
| High Stakes | 隔週 | 記載なし | なし（明示） | $150 | 80% | 出金手段: Crypto, Rise, Bank Transfer等 |
| Hyper-Growth | 隔週 | 記載なし | なし（明示） | ー | 75% | 出金手段: Crypto, Rise, Bank Transfer等 |
| Bootcamp | 隔週 | 記載なし | 記載なし | ー | 50% | 出金手段: Crypto, Rise, Bank Transfer等 |
| Pro-Growth | 隔週 | 記載なし | 記載なし | ー | 75% | 出金手段: Crypto, Rise, Bank Transfer等 |

### 最速出金スケジュール（理論値）
| プラン名 | Steps | 最短合格 | 最速出金 | トータル日数 | 着金目安 | 備考 |
|---|---|---|---|---|---|---|
| High Stakes | 2 | 6日 | 14日 | 20日 | 記載なし | 最短合格は各Step3日で算出 |
| Hyper-Growth | 1 | 1日 | 14日 | 15日 | 記載なし | 合格条件0日は1日で算出 |
| Bootcamp | 3 | 3日 | 14日 | 17日 | 記載なし | 合格条件なしは1日×3Stepで算出 |
| Pro-Growth | 1 | 3日 | 14日 | 17日 | 記載なし | 最短合格は3日で算出 |

### 補足事項
最速出金はFunded口座受領から14日目に可能となり、以降は2週間ごと（隔週）のサイクルで出金申請が可能である。スケールアップに伴い、利益分配率は全プランで最大100%まで上昇する仕様である。