---
type: plans
title: "Instant Prime"
slug: "instant-prime"
firm: "top-one-trader"
---

## 断面① Drawdown

各プランは計算基準として固定型（Static）またはTrailing型のいずれかを採用している。1-StepプランおよびInstantプランはTrailing型を適用する一方、2-StepプランはStatic型を採用する構成である。

| プラン名 | フェーズ | 日次損失上限 | 計算基準（日次） | 最大損失上限 | 計算基準（最大） |
| --- | --- | --- | --- | --- | --- |
| 1-Step FLASH | ー | 4% | Trailing（Higher B or E EOD） | 7% | Trailing（Balance HWM） |
| 1-Step NOVA | Challenge | 3% | Trailing（Higher B or E EOD） | 6% | Trailing（Balance HWM） |
| 1-Step NOVA | Funded | 3% | Trailing（Higher B or E EOD） | 5% | Trailing（Balance HWM） |
| 2-Step PLUS | ー | 4% | Trailing（Higher B or E EOD） | 8% | Static |
| 2-Step PRO | ー | 4% | Trailing（Higher B or E EOD） | 9% | Static |
| Instant Funding | Funded | 3% | Trailing（Higher B or E EOD） | 6% | Trailing（Balance HWM） |
| Instant Prime | Funded | 2.5% | Trailing（Higher B or E EOD） | 5% | Trailing（Balance HWM） |

日次損失は毎日午後5時（EST）時点の最高残高または最高純資産のいずれか高い方を基準に再計算される。Trailing型の最大損失は最高純資産に伴って上限が引き上げられるが、Funded口座からの出金申請時に初期残高でロックされるLUP（Locked Upon Payout）仕様が適用される。

Trailing（Higher B or E EOD）は未確定の含み益も日次損失の計算基準に含めるため、相場反転時の含み益減少が日次損失違反として判定される仕様である。

Trailing型の最大損失を採用するプランでは、初回出金時にLUPが発動し、以降の損失許容下限が初期残高に固定される仕様である。

Equity Shield機能により、単一シンボルの含み損が初期残高の2.0%、または全体の含み損が2.5%に達した場合は強制決済される。

---

## 断面② 取引ルール

Top One Traderでは全プラン共通の厳格な基本ルールが存在する一方、プランごとに一貫性ルールの有無やニュース・週末の保有条件が異なる。

| プラン | Challenge | Funded | 備考 |
| --- | --- | --- | --- |
| 1-Step FLASH | 無 | 無 | ー |
| 1-Step NOVA | 無 | 有（20% ESS） | ESSは最大利益日と最大損失日の合算を累積利益で割った値 |
| 2-Step PLUS | 無 | 無 | ー |
| 2-Step PRO | 無 | 無 | ー |
| Instant Funding | ー | 有（15%） | 単一日の利益が累積利益の15%以下 |
| Instant Prime | ー | 有（20% ESS） | ESSは最大利益日と最大損失日の合算を累積利益で割った値 |

全注文においてストップロスの設定が義務付けられ、未設定時はソフトブリーチとなる。ポジション保有時間が5分未満となる超短時間売買（Tick Scalping）は禁止されている。また、他口座・他者からのコピートレードはFunded口座において厳禁である。禁止行為として、HFT、Latency Arbitrage、マーチンゲール、グリッドトレード等が指定されている。

| ルール項目 | プラン別の違い |
| --- | --- |
| ニュース取引制限 | 1/2-Step: C許容、F重要指標前後5分間禁止 / Instant Funding: 全期禁止 / Instant Prime: 禁止（※アドオン購入時許容） |
| 週末保有制限 | 1/2-Step: 許容 / Instant: 禁止（金曜午後4時30分EST決済義務、※アドオン購入時許容） |
| EA制限 | 1/2-Step: C独自EA許容、F不可 / Instant: 全面不可 |
| 利益・出金上限 | 全プラン共通で30日あたり最大$25,000 |

1-Stepや2-StepプランのChallengeでは独自のEA使用やニュース発表時の取引が許容されており、制限の少ない条件で取引が可能な仕様である。

Funded口座ではEAの使用やコピートレードが完全に禁止されるほか、ニュース発表前後5分間の取引が禁止されるなど、評価時よりも制約が強化される仕様である。

---

## 断面③ 出金までの流れ

初回出金までの期間はプランにより異なり、1-Stepや2-Stepプランは14日ベースであるのに対し、Instant Fundingは30日の運用期間を要する設計である。

| プラン名 | 頻度 | 最低取引日数（出金） | 一貫性ルール | 最低利益 | 利益分配 | 備考 |
| --- | --- | --- | --- | --- | --- | --- |
| 1-Step FLASH | 隔週 | 3日 | 無 | 2% | 80% | 処理24〜48営業時間 |
| 1-Step NOVA | 隔週 | なし（明示） | 有（20% ESS） | 2% | 90% | 処理24〜48営業時間 |
| 2-Step PLUS | 隔週 | 5日 | 無 | 2% | 80% | 処理24〜48営業時間 |
| 2-Step PRO | 隔週 | 3日 | 無 | 3% | 85% | 処理24〜48営業時間 |
| Instant Funding | 月次 | なし（明示） | 有（15%） | 2% | 60% | 初回30日、処理24〜48営業時間 |
| Instant Prime | 隔週 | なし（明示） | 有（20% ESS） | 2% | 80% | 処理24〜48営業時間 |

| プラン名 | Steps | 最短合格 | 最速出金 | トータル日数 | 着金目安 | 備考 |
| --- | --- | --- | --- | --- | --- | --- |
| 1-Step FLASH | 1 | 3日 | 14日 | 17日 | 19日 | 着金目安は処理2営業日を加算 |
| 1-Step NOVA | 1 | 1日 | 14日 | 15日 | 17日 | 最短合格はフォールバック1日を適用 |
| 2-Step PLUS | 2 | 10日 | 14日 | 24日 | 26日 | ー |
| 2-Step PRO | 2 | 6日 | 14日 | 20日 | 22日 | ー |
| Instant Funding | 0 | 0日 | 30日 | 30日 | 32日 | Instantは即時運用のための0日換算 |
| Instant Prime | 0 | 0日 | 14日 | 14日 | 16日 | Instantは即時運用のための0日換算 |

出金申請はRiseWorksを経由して処理され、銀行送金または暗号通貨での受け取りとなる。すべての利益分配金の送金処理にはファームにより2%の処理手数料が課される仕様である。着金目安は出金処理期間の最大48営業時間（2営業日）を最速出金日数に加算して算出している。