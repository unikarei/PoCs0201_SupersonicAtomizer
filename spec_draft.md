Spray Atomization Quasi-1D Simulator 仕様書（SDD用）
1. 目的

本システムは、一次元軸方向に変化する流路内を流れる作動流体（air または steam）と水滴の相互作用を簡易モデルで計算し、作動流体による液滴の加速・微細化を予測するシミュレータである。

対象は Quasi-1D とし、流路断面積分布 A(x) を与えたときに、軸方向 x に対する以下を計算・可視化する。

作動流体速度
作動流体圧力
作動流体温度
液滴速度
液滴代表粒径
液滴最大粒径
液滴ウェーバー数
液滴破砕発生位置
液滴質量流量や水分率の変化

本システムは研究用の初期評価ツールであり、3D CFD の代替ではなく、設計検討・感度解析・形状比較のための高速予測ツールとして用いる。

2. 適用範囲
2.1 対象
作動流体: air または steam
液相: 水滴
流れ: 定常
空間次元: Quasi-1D
流路: 軸方向断面積変化あり
相変化:
air の場合: 水滴蒸発はオプション
steam の場合: 平衡蒸気モデルを用いる簡易モデルを採用
液滴破砕: 一次簡易 breakup model を採用
2.2 対象外（MVPでは扱わない）
3D噴霧拡がり角
液滴同士の衝突・合体
壁面衝突後の液膜生成
非平衡凝縮
衝撃波を伴う厳密な2相圧縮性CFD
自由噴流外部場の2D/3D解
3. シミュレーション概要

シミュレーションは、入口から流入する作動流体と水滴を、流路軸方向に沿って逐次計算する。

3.1 作動流体側

作動流体は Quasi-1D の圧縮性流れとして計算する。

計算対象:

全圧 Pt_in
全温 Tt_in
出口静圧 Ps_out
流路断面積分布 A(x)
作動流体物性モデル

出力:

P(x), T(x), rho(x), u_g(x), M(x)
3.2 液滴側

液滴はラグランジュ的に、軸方向平均場の中を移動する代表粒子群として扱う。

計算対象:

初期液滴速度
初期粒径分布
液滴数密度または液滴質量流量
作動流体との相対速度
抗力
breakup 条件
必要に応じて蒸発

出力:

u_d(x)
d32(x) 代表粒径
d_max(x) 最大粒径
We(x) 液滴ウェーバー数
breakup 発生フラグ
m_d(x)
4. 入力仕様
4.1 必須入力
流体条件
working_fluid: "air" or "steam"
Pt_in: 入口全圧 [Pa]
Tt_in: 入口全温 [K]
Ps_out: 出口静圧 [Pa]
湿り条件
inlet_wetness: 入口湿り度 [-]
air の場合は省略可
steam の場合に使用
既定値: 0.0
幾何条件
x_start: 計算開始位置 [m]
x_end: 計算終了位置 [m]
n_cells: 軸方向分割数
area_distribution: x-A テーブル、または関数
液滴条件
water_mass_flow_rate: 水滴質量流量 [kg/s]
droplet_velocity_in: 入口液滴速度 [m/s]
droplet_diameter_mean_in: 初期平均粒径 [m]
droplet_diameter_max_in: 初期最大粒径 [m]
4.2 オプション入力
drag_model: "standard_sphere" など
breakup_model: "none", "weber_critical", "simple_tab"
evaporation_model: "none", "equilibrium_simple"
steam_property_model: "if97"
air_property_model: "ideal_gas"
surface_tension_model
water_density_model
critical_weber_number
time_scale_factor_breakup
5. 出力仕様
5.1 数値出力

各軸位置 x に対して以下を出力する:

x
A
P
T
rho
u_g
M
u_d
slip_velocity = u_g - u_d
d_mean
d_max
We
Re_d
breakup_flag
water_mass_fraction
evaporation_rate（有効時）

出力形式:

CSV
JSON
5.2 グラフ出力
u_g(x) 作動流体速度
u_d(x) 液滴速度
P(x) 静圧
T(x) 静温
M(x) マッハ数
d_mean(x) 平均粒径
d_max(x) 最大粒径
We(x) ウェーバー数
6. 物理モデル
6.1 作動流体モデル
air
理想気体モデル
状態方程式:
P = rho * R * T
必要に応じて比熱一定
steam
IF97 ベースの物性モデルを使用
平衡蒸気を仮定
入力された全圧・全温・湿り度から状態量を計算
6.2 流れモデル

Quasi-1D の圧縮性流れ式を解く。

保存式:

質量保存
運動量保存（簡易）
エネルギー保存
面積変化項を含む

必要に応じて以下を考慮:

チョーク判定
亜音速/超音速の分岐
面積変化による加減速
6.3 液滴運動モデル

液滴は代表粒子として扱い、軸方向について以下を解く。

抗力
慣性
相対速度減衰

液滴速度式:

抗力係数 Cd
粒子レイノルズ数 Re_d
気液相対速度による加速
6.4 液滴破砕モデル
MVPモデル

簡易 Weber 数閾値モデルを用いる。

We = rho_g * (u_g - u_d)^2 * d / sigma
We > We_crit で breakup 発生

breakup発生時:

平均粒径を減少
最大粒径も減少
減少率は経験式またはユーザー指定係数で与える

例:

d_new = d_old * f_breakup
d_max,new = d_max,old * f_max_breakup
将来拡張
TAB model
KH-RT model
breakup time scale model
6.5 蒸発モデル

MVPでは簡易平衡モデル。

air: 必要なら簡易蒸発
steam: 平衡蒸気条件に基づく簡易質量変化
初版では none をデフォルトにする
7. ソフトウェア構成
7.1 推奨ディレクトリ構成
project/
  ├─ src/
  │   ├─ main.py
  │   ├─ config/
  │   │   └─ schema.py
  │   ├─ core/
  │   │   ├─ grid.py
  │   │   ├─ solver_gas.py
  │   │   ├─ solver_droplet.py
  │   │   ├─ coupling.py
  │   │   └─ simulation.py
  │   ├─ physics/
  │   │   ├─ air.py
  │   │   ├─ steam_if97.py
  │   │   ├─ droplet_drag.py
  │   │   ├─ breakup.py
  │   │   └─ evaporation.py
  │   ├─ io/
  │   │   ├─ input_loader.py
  │   │   ├─ output_writer.py
  │   │   └─ plotting.py
  │   └─ utils/
  │       └─ units.py
  ├─ tests/
  ├─ examples/
  │   └─ sample_case.yaml
  ├─ docs/
  │   └─ specification.md
  └─ requirements.txt
8. 入力ファイル仕様

YAML 形式を標準とする。

working_fluid: steam
Pt_in: 600000.0
Tt_in: 500.0
Ps_out: 100000.0
inlet_wetness: 0.0

geometry:
  x_start: 0.0
  x_end: 0.1
  n_cells: 200
  area_distribution:
    type: table
    x: [0.0, 0.03, 0.06, 0.1]
    A: [1.2e-4, 1.0e-4, 0.8e-4, 1.0e-4]

droplet:
  water_mass_flow_rate: 0.001
  droplet_velocity_in: 10.0
  droplet_diameter_mean_in: 100e-6
  droplet_diameter_max_in: 300e-6

models:
  drag_model: standard_sphere
  breakup_model: weber_critical
  evaporation_model: none
  critical_weber_number: 12.0
9. 計算手順
入力読込
軸方向格子生成
流路断面積分布設定
作動流体物性初期化
Quasi-1D流れ場計算
液滴初期条件設定
軸方向に液滴速度・粒径を逐次更新
breakup判定
蒸発判定
出力保存
グラフ生成
10. 受け入れ基準
10.1 機能要件
air/steam の切替ができる
A(x) を任意入力できる
u_g(x), u_d(x), d_mean(x), d_max(x) を計算できる
結果を CSV 出力できる
グラフを自動生成できる
10.2 数値要件
入力異常時は明確にエラー表示
計算が発散した場合は位置と原因候補を表示
単位系は SI に統一
10.3 検証要件
面積一定・液滴なしの場合、基本的な Quasi-1D 結果が妥当
相対速度ゼロでは breakup しない
We 増加で粒径が減少する傾向を再現する
11. 将来拡張
ラバールノズル対応の厳密化
自由噴流領域の追加
平板衝突モデル
液滴粒径分布全体の輸送
非平衡湿り蒸気
GUI
最適化ループ連携
VSCode から複数ケース一括実行
12. SDD実装時の開発順序
Phase 1
air
面積分布
Quasi-1D gas solver
droplet motion
simple Weber breakup
CSV/plot
Phase 2
steam IF97
inlet wetness
equilibrium steam
simple evaporation
Phase 3
breakup model 切替
分布粒径対応
case sweep
validation utilities