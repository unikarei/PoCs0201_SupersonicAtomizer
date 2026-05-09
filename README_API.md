# Supersonic Atomizer GUI API ドキュメント

## 📋 概要

Supersonic Atomizer の FastAPI ベース GUI は、6 つのルーター から構成される **37+ エンドポイント** を提供します。

| ルーター | エンドポイント数 | 用途 |
|---------|-----------------|------|
| **Index Router** | 2 | HTML ページ配信、favicon |
| **Cases Router** | 19 | プロジェクト・ケース管理 |
| **Simulation Router** | 3 | バックグラウンドジョブ実行・管理 |
| **Chat Router** | 12 | チャットスレッド、AI 提案 |
| **Units Router** | 3 | 単位設定管理 |
| **Debug Router** | 1 | クライアント側ログ |
| **合計** | **40** | - |

---

## 🔧 基本設定

- **ベース URL**: `http://localhost:8000`
- **デフォルトポート**: `8000`
- **実行コマンド**: `uv run uvicorn supersonic_atomizer.gui.fastapi_app:app --reload`

### 起動確認

```bash
# FastAPI GUI の起動
uv run uvicorn supersonic_atomizer.gui.fastapi_app:app --reload

# ブラウザでアクセス
# http://localhost:8000
```

---

# 🏠 1. Index Router

**用途**: シングルページアプリケーション (SPA) の HTML シェル配信

## 1.1 GET `/`

| 項目 | 値 |
|------|-----|
| **説明** | メイン HTML ページを配信（Jinja2 テンプレート）|
| **リクエスト本体** | なし |
| **レスポンス** | HTML ドキュメント |
| **ステータスコード** | `200 OK` |
| **副作用** | セッションクッキーを設定 |

### レスポンス例

```html
<!DOCTYPE html>
<html>
  <head>
    <title>Supersonic Atomizer GUI</title>
    ...
  </head>
  <body>...</body>
</html>
```

---

## 1.2 GET `/favicon.ico`

| 項目 | 値 |
|------|-----|
| **説明** | ファビコンリクエストを処理（404 を抑止）|
| **リクエスト本体** | なし |
| **レスポンス本体** | なし |
| **ステータスコード** | `204 No Content` |

---

---

# 📁 2. Cases Router

**用途**: プロジェクト・ケース CRUD 操作

**プレフィックス**: `/api/cases`

**機能**:
- プロジェクト管理（作成、削除、リネーム、エクスポート）
- ケース管理（作成、取得、保存、削除、複製、リネーム）
- レガシー（フラット）ケース互換性

---

## 📦 2.1 プロジェクト管理

### 2.1.1 GET `/projects/`

全プロジェクト一覧を取得

| 項目 | 値 |
|------|-----|
| **説明** | 全プロジェクト名とデフォルトプロジェクト名を返す |
| **メソッド** | `GET` |
| **リクエスト本体** | なし |
| **ステータスコード** | `200 OK` |

**レスポンス本体**:

```json
{
  "projects": ["default", "project1", "project2"],
  "default_project": "default"
}
```

---

### 2.1.2 POST `/projects/`

新しいプロジェクトを作成

| 項目 | 値 |
|------|-----|
| **説明** | 空のプロジェクトディレクトリを作成 |
| **メソッド** | `POST` |
| **ステータスコード** | `201 Created` \| `400 Bad Request` \| `409 Conflict` |

**リクエスト本体**:

```json
{
  "name": "my_project"
}
```

**レスポンス本体**:

```json
{
  "name": "my_project"
}
```

**エラー例**:

```json
{
  "detail": "Invalid project name"
}
```

---

### 2.1.3 DELETE `/projects/{project}`

プロジェクトとその内部の全ケースを削除

| 項目 | 値 |
|------|-----|
| **説明** | プロジェクト全体を削除 |
| **メソッド** | `DELETE` |
| **パスパラメータ** | `project` (str) |
| **ステータスコード** | `204 No Content` \| `404 Not Found` |

**実行例**:

```bash
curl -X DELETE http://localhost:8000/api/cases/projects/my_project
```

---

### 2.1.4 POST `/projects/{project}/rename`

プロジェクトをリネーム（内部ケース保持）

| 項目 | 値 |
|------|-----|
| **説明** | プロジェクト名変更（ケース保持）|
| **メソッド** | `POST` |
| **パスパラメータ** | `project` (str) |
| **ステータスコード** | `200 OK` \| `400 Bad Request` \| `409 Conflict` |

**リクエスト本体**:

```json
{
  "new_name": "renamed_project"
}
```

**レスポンス本体**:

```json
{
  "name": "renamed_project"
}
```

---

### 2.1.5 GET `/projects/{project}/export`

プロジェクト内全ケースを ZIP アーカイブでエクスポート

| 項目 | 値 |
|------|-----|
| **説明** | プロジェクトを ZIP ファイルとしてダウンロード |
| **メソッド** | `GET` |
| **パスパラメータ** | `project` (str) |
| **レスポンス** | Binary ZIP file |
| **ステータスコード** | `200 OK` \| `404 Not Found` |

**実行例**:

```bash
curl -X GET http://localhost:8000/api/cases/projects/my_project/export \
  -o my_project.zip
```

---

## 📄 2.2 ケース管理（プロジェクトスコープ）

### 2.2.1 GET `/projects/{project}/cases/`

プロジェクト内の全ケース一覧を取得

| 項目 | 値 |
|------|-----|
| **説明** | プロジェクト内のケース名一覧を返す |
| **メソッド** | `GET` |
| **パスパラメータ** | `project` (str) |
| **ステータスコード** | `200 OK` \| `400 Bad Request` |

**レスポンス本体**:

```json
{
  "project": "my_project",
  "cases": ["case1", "case2", "case3"]
}
```

---

### 2.2.2 POST `/projects/{project}/cases/`

新しいケースをプロジェクト内に作成

| 項目 | 値 |
|------|-----|
| **説明** | 空のスケルトンケースを作成 |
| **メソッド** | `POST` |
| **パスパラメータ** | `project` (str) |
| **ステータスコード** | `201 Created` \| `400 Bad Request` \| `409 Conflict` |

**リクエスト本体**:

```json
{
  "name": "new_case"
}
```

**レスポンス本体**:

```json
{
  "project": "my_project",
  "name": "new_case"
}
```

---

### 2.2.3 GET `/projects/{project}/cases/{name}`

ケースの設定を取得

| 項目 | 値 |
|------|-----|
| **説明** | ケース設定と메타데이터를 返す |
| **メソッド** | `GET` |
| **パスパラメータ** | `project` (str), `name` (str) |
| **ステータスコード** | `200 OK` \| `404 Not Found` |

**レスポンス本体**:

```json
{
  "config": {
    "fluid": { "working_fluid": "air" },
    "boundary_conditions": {
      "Pt_in": 200000.0,
      "Tt_in": 300.0,
      "Ps_out": 101325.0
    },
    "geometry": {
      "x_start": 0.0,
      "x_end": 0.5,
      "num_cells": 100,
      "area_table": [
        { "x": 0.0, "A": 0.01 },
        { "x": 0.25, "A": 0.005 },
        { "x": 0.5, "A": 0.01 }
      ]
    },
    "model_selection": {
      "breakup_model": "weber_critical",
      "critical_weber_number": 12.0
    }
  },
  "has_result": true,
  "last_modified": "2026-05-09T10:30:00Z"
}
```

---

### 2.2.4 PUT `/projects/{project}/cases/{name}`

ケースの設定を保存（上書き）

| 項目 | 値 |
|------|-----|
| **説明** | ケース設定を更新・保存 |
| **メソッド** | `PUT` |
| **パスパラメータ** | `project` (str), `name` (str) |
| **ステータスコード** | `200 OK` \| `400 Bad Request` \| `404 Not Found` |

**リクエスト本体**:

```json
{
  "fluid": { "working_fluid": "steam" },
  "boundary_conditions": {
    "Pt_in": 250000.0,
    "Tt_in": 350.0,
    "Ps_out": 101325.0
  }
}
```

**レスポンス本体**: GET と同じ形式

---

### 2.2.5 DELETE `/projects/{project}/cases/{name}`

ケースを削除（出力アーティファクトを含む）

| 項目 | 値 |
|------|-----|
| **説明** | ケースと関連出力を削除 |
| **メソッド** | `DELETE` |
| **パスパラメータ** | `project` (str), `name` (str) |
| **ステータスコード** | `204 No Content` \| `404 Not Found` |

---

### 2.2.6 POST `/projects/{project}/cases/{name}/duplicate`

既存ケースを複製

| 項目 | 値 |
|------|-----|
| **説明** | ケースのコピーを作成 |
| **メソッド** | `POST` |
| **パスパラメータ** | `project` (str), `name` (str) |
| **ステータスコード** | `201 Created` \| `409 Conflict` |

**リクエスト本体**:

```json
{
  "new_name": "case_copy"
}
```

**レスポンス本体**:

```json
{
  "project": "my_project",
  "name": "case_copy"
}
```

---

### 2.2.7 POST `/projects/{project}/cases/{name}/rename`

ケースをリネーム（出力アーティファクト保持）

| 項目 | 値 |
|------|-----|
| **説明** | ケース名変更（出力保持）|
| **メソッド** | `POST` |
| **パスパラメータ** | `project` (str), `name` (str) |
| **ステータスコード** | `200 OK` \| `409 Conflict` |

**リクエスト本体**:

```json
{
  "new_name": "renamed_case"
}
```

---

### 2.2.8 GET `/projects/{project}/cases/{name}/export`

ケース（YAML + 出力アーティファクト）を ZIP でエクスポート

| 項目 | 値 |
|------|-----|
| **説明** | ケースを ZIP ファイルとしてダウンロード |
| **メソッド** | `GET` |
| **パスパラメータ** | `project` (str), `name` (str) |
| **レスポンス** | Binary ZIP file |
| **ステータスコード** | `200 OK` \| `404 Not Found` |

---

### 2.2.9 GET `/projects/{project}/cases/{name}/last_result`

ケースの最新シミュレーション結果を取得（再実行不要）

| 項目 | 値 |
|------|-----|
| **説明** | 最新の結果を返す（プロット、テーブル、CSV）|
| **メソッド** | `GET` |
| **パスパラメータ** | `project` (str), `name` (str) |
| **ステータスコード** | `200 OK` \| `404 Not Found` \| `409 Conflict` |

**レスポンス本体**:

```json
{
  "plots": {
    "pressure_profile": "base64-encoded-png",
    "velocity_profile": "base64-encoded-png"
  },
  "table_rows": [
    { "x": 0.0, "P": 200000, "V": 10.5 },
    { "x": 0.1, "P": 195000, "V": 12.3 }
  ],
  "csv_content": "x,P,V\n0.0,200000,10.5\n0.1,195000,12.3\n",
  "run_count": 1
}
```

---

## 📄 2.3 ケース管理（レガシー・フラット互換）

ルートレベルケース（レガシーモード）のための後方互換 API

### 2.3.1 GET `/`

ルートレベルケース一覧を取得

| 項目 | 値 |
|------|-----|
| **説明** | ルートレベルの全ケース名を返す |
| **メソッド** | `GET` |
| **ステータスコード** | `200 OK` |

**レスポンス本体**:

```json
{
  "cases": ["legacy_case1", "legacy_case2"]
}
```

---

### 2.3.2 POST `/`

ルートレベルに新しいケースを作成

| 項目 | 値 |
|------|-----|
| **説明** | ルートレベルのスケルトンケースを作成 |
| **メソッド** | `POST` |
| **ステータスコード** | `201 Created` \| `409 Conflict` |

**リクエスト本体**:

```json
{
  "name": "new_legacy_case"
}
```

---

### 2.3.3 GET `/{name}`

ルートレベルケースの設定を取得

| 項目 | 値 |
|------|-----|
| **メソッド** | `GET` |
| **パスパラメータ** | `name` (str) |
| **ステータスコード** | `200 OK` \| `404 Not Found` |

---

### 2.3.4 PUT `/{name}`

ルートレベルケースの設定を保存

| 項目 | 値 |
|------|-----|
| **メソッド** | `PUT` |
| **パスパラメータ** | `name` (str) |
| **ステータスコード** | `200 OK` \| `404 Not Found` |

---

### 2.3.5 DELETE `/{name}`

ルートレベルケースを削除

| 項目 | 値 |
|------|-----|
| **メソッド** | `DELETE` |
| **パスパラメータ** | `name` (str) |
| **ステータスコード** | `204 No Content` \| `404 Not Found` |

---

### 2.3.6 GET `/{name}/last_result`

ルートレベルケースの最新結果を取得

| 項目 | 値 |
|------|-----|
| **メソッド** | `GET` |
| **パスパラメータ** | `name` (str) |
| **ステータスコード** | `200 OK` \| `404 Not Found` \| `409 Conflict` |

---

---

# ⚙️ 3. Simulation Router

**用途**: バックグラウンドシミュレーション実行・管理

**プレフィックス**: `/api/simulation`

**デザイン**: ノンブロッキング（非同期）
1. `POST /run` でバックグラウンド実行開始
2. `GET /status/{job_id}` でポーリング
3. `GET /result/{job_id}` で結果取得

---

## 3.1 POST `/run`

シミュレーション実行をバックグラウンドで開始

| 項目 | 値 |
|------|-----|
| **説明** | バックグラウンドスレッドでソルバーを実行 |
| **メソッド** | `POST` |
| **ステータスコード** | `200 OK` \| `400 Bad Request` \| `404 Not Found` |

**リクエスト本体**:

```json
{
  "project_name": "my_project",
  "case_name": "my_case",
  "config": null
}
```

または、複数値スイープの場合：

```json
{
  "project_name": "my_project",
  "case_name": "my_case",
  "config": {
    "boundary_conditions.Pt_in": [200000, 250000, 300000],
    "boundary_conditions.Tt_in": [300, 350]
  }
}
```

**レスポンス本体**:

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**副作用**: デーモンスレッド生成、ジョブストアに登録

---

## 3.2 GET `/status/{job_id}`

バックグラウンドジョブの状態をポーリング

| 項目 | 値 |
|------|-----|
| **説明** | ジョブの実行状態を返す |
| **メソッド** | `GET` |
| **パスパラメータ** | `job_id` (str) |
| **ステータスコード** | `200 OK` \| `404 Not Found` |

**レスポンス本体**:

```json
{
  "status": "running",
  "error": null
}
```

**ステータス値**:

| 値 | 意味 |
|---|-----|
| `"running"` | 実行中 |
| `"completed"` | 完了（成功） |
| `"failed"` | 失敗 |

**完了時の例**:

```json
{
  "status": "completed",
  "error": null
}
```

**失敗時の例**:

```json
{
  "status": "failed",
  "error": "Thermodynamic state error at cell 50: negative pressure"
}
```

---

## 3.3 GET `/result/{job_id}`

完了したジョブの結果を取得

| 項目 | 値 |
|------|-----|
| **説明** | プロット、テーブル、CSV を返す |
| **メソッド** | `GET` |
| **パスパラメータ** | `job_id` (str) |
| **ステータスコード** | `200 OK` \| `404 Not Found` \| `409 Conflict` |

**レスポンス本体**:

```json
{
  "plots": {
    "pressure_profile": "iVBORw0KGgoAAAANSUhEUgAAAAUA...",
    "velocity_profile": "iVBORw0KGgoAAAANSUhEUgAAAAUA...",
    "temperature_profile": "iVBORw0KGgoAAAANSUhEUgAAAAUA..."
  },
  "table_rows": [
    {
      "x": 0.0,
      "P": 200000.0,
      "V": 10.5,
      "T": 300.0
    },
    {
      "x": 0.1,
      "P": 195000.0,
      "V": 12.3,
      "T": 295.0
    }
  ],
  "csv_content": "x,P,V,T\n0.0,200000.0,10.5,300.0\n0.1,195000.0,12.3,295.0\n",
  "run_count": 1
}
```

**マルチバリュースイープ時**:

```json
{
  "plots": {
    "pressure_overlay": "iVBORw0KGgoAAAANSUhEUgAAAAUA...",
    "velocity_overlay": "iVBORw0KGgoAAAANSUhEUgAAAAUA..."
  },
  "table_rows": [
    { "run_label": "Pt_in=200k", "x": 0.0, "P": 200000 },
    { "run_label": "Pt_in=200k", "x": 0.1, "P": 195000 },
    { "run_label": "Pt_in=250k", "x": 0.0, "P": 250000 }
  ],
  "csv_content": "run_label,x,P\nPt_in=200k,0.0,200000\n...",
  "run_count": 3
}
```

---

---

# 💬 4. Chat Router

**用途**: ケース対応チャット・AI 支援設定変更

**プレフィックス**: `/api/chat`

**機能**:
- チャットスレッド管理
- メッセージ送受信
- スレッド要約
- AI による設定変更提案・承認

---

## 4.1 チャットスレッド管理

### 4.1.1 GET `/threads`

ケースのチャットスレッド一覧を取得

| 項目 | 値 |
|------|-----|
| **説明** | ケースに属するスレッド一覧を返す |
| **メソッド** | `GET` |
| **クエリパラメータ** | `case_name` (str, 必須), `project_name` (str, オプション) |
| **ステータスコード** | `200 OK` \| `400 Bad Request` \| `404 Not Found` |

**URL 例**:

```
GET /api/chat/threads?case_name=my_case&project_name=my_project
```

**レスポンス本体**:

```json
{
  "threads": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "title": "Performance optimization",
      "created_at": "2026-05-09T10:00:00Z",
      "updated_at": "2026-05-09T10:30:00Z"
    },
    {
      "id": "550e8400-e29b-41d4-a716-446655440001",
      "title": "Geometry analysis",
      "created_at": "2026-05-08T15:00:00Z",
      "updated_at": "2026-05-08T16:00:00Z"
    }
  ]
}
```

---

### 4.1.2 POST `/threads`

新しいチャットスレッドを作成

| 項目 | 値 |
|------|-----|
| **説明** | ケース内に新規スレッドを作成 |
| **メソッド** | `POST` |
| **ステータスコード** | `201 Created` \| `400 Bad Request` \| `404 Not Found` |

**リクエスト本体**:

```json
{
  "project_name": "my_project",
  "case_name": "my_case",
  "title": "Performance optimization"
}
```

**レスポンス本体**:

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Performance optimization",
  "created_at": "2026-05-09T10:00:00Z",
  "updated_at": "2026-05-09T10:00:00Z",
  "messages": []
}
```

---

### 4.1.3 GET `/threads/{thread_id}`

スレッドの詳細を取得（メッセージ履歴を含む）

| 項目 | 値 |
|------|-----|
| **説明** | スレッド全体とメッセージ履歴を返す |
| **メソッド** | `GET` |
| **パスパラメータ** | `thread_id` (str) |
| **クエリパラメータ** | `case_name` (str, 必須), `project_name` (str, オプション) |
| **ステータスコード** | `200 OK` \| `404 Not Found` |

**URL 例**:

```
GET /api/chat/threads/550e8400-e29b-41d4-a716-446655440000?case_name=my_case
```

**レスポンス本体**:

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Performance optimization",
  "created_at": "2026-05-09T10:00:00Z",
  "updated_at": "2026-05-09T10:30:00Z",
  "messages": [
    {
      "role": "user",
      "content": "How can I improve the performance?"
    },
    {
      "role": "assistant",
      "content": "Based on your current configuration, I recommend..."
    }
  ]
}
```

---

### 4.1.4 PATCH `/threads/{thread_id}`

スレッドをリネーム

| 項目 | 値 |
|------|-----|
| **説明** | スレッド名を変更 |
| **メソッド** | `PATCH` |
| **パスパラメータ** | `thread_id` (str) |
| **ステータスコード** | `200 OK` \| `404 Not Found` |

**リクエスト本体**:

```json
{
  "project_name": "my_project",
  "case_name": "my_case",
  "title": "Updated thread title"
}
```

---

### 4.1.5 DELETE `/threads/{thread_id}`

スレッドを削除

| 項目 | 値 |
|------|-----|
| **説明** | スレッドを削除（メッセージも含む）|
| **メソッド** | `DELETE` |
| **パスパラメータ** | `thread_id` (str) |
| **クエリパラメータ** | `case_name` (str, 必須), `project_name` (str, オプション) |
| **ステータスコード** | `204 No Content` \| `404 Not Found` |

---

### 4.1.6 PUT `/threads/{thread_id}/messages`

スレッドのメッセージを全て置き換え

| 項目 | 値 |
|------|-----|
| **説明** | メッセージ履歴を置き換え |
| **メソッド** | `PUT` |
| **パスパラメータ** | `thread_id` (str) |
| **ステータスコード** | `200 OK` \| `404 Not Found` |

**リクエスト本体**:

```json
{
  "project_name": "my_project",
  "case_name": "my_case",
  "messages": [
    { "role": "user", "content": "Hello" },
    { "role": "assistant", "content": "Hi there!" }
  ]
}
```

---

## 4.2 メッセージ送受信

### 4.2.1 POST `/messages`

ユーザーメッセージを送信、AI 応答を取得

| 項目 | 値 |
|------|-----|
| **説明** | ケース文脈を含むメッセージを送信 |
| **メソッド** | `POST` |
| **ステータスコード** | `200 OK` \| `400 Bad Request` \| `500 Internal Server Error` |

**リクエスト本体**:

```json
{
  "project_name": "my_project",
  "case_name": "my_case",
  "thread_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_message": "What should I adjust to reduce pressure drop?"
}
```

**レスポンス本体**:

```json
{
  "role": "assistant",
  "content": "To reduce pressure drop, consider:\n1. Increasing the throat area...\n2. Reducing the inlet Mach number..."
}
```

---

### 4.2.2 POST `/summary`

チャットスレッドの要約を生成

| 項目 | 値 |
|------|-----|
| **説明** | スレッド全体の簡潔な要約を生成 |
| **メソッド** | `POST` |
| **ステータスコード** | `200 OK` \| `400 Bad Request` \| `500 Server Error` |

**リクエスト本体**:

```json
{
  "project_name": "my_project",
  "case_name": "my_case",
  "thread_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**レスポンス本体**:

```json
{
  "summary": "Discussed optimization strategies for nozzle design. Decided to increase throat area and adjust inlet conditions. Next steps: run simulation and validate results."
}
```

---

## 4.3 AI 支援設定変更

### 4.3.1 POST `/config-changes/proposals`

AI による設定変更提案を生成

| 項目 | 値 |
|------|-----|
| **説明** | ユーザー要求に基づいて設定パッチを提案 |
| **メソッド** | `POST` |
| **ステータスコード** | `200 OK` \| `400 Bad Request` \| `500 Server Error` |

**リクエスト本体**:

```json
{
  "project_name": "my_project",
  "case_name": "my_case",
  "thread_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_request": "Optimize for lower pressure drop",
  "scoped_paths": ["boundary_conditions", "geometry"]
}
```

**レスポンス本体**:

```json
{
  "proposal_id": "prop-550e8400-e29b-41d4-a716",
  "state": "proposed",
  "changes": [
    { "path": "boundary_conditions.Pt_in", "value": 250000 },
    { "path": "geometry.num_cells", "value": 150 }
  ]
}
```

---

### 4.3.2 POST `/config-changes/proposals/{proposal_id}/apply`

提案パッチを適用・検証（差分を表示）

| 項目 | 値 |
|------|-----|
| **説明** | パッチを適用し、適用前後の差分を返す |
| **メソッド** | `POST` |
| **パスパラメータ** | `proposal_id` (str) |
| **ステータスコード** | `200 OK` \| `404 Not Found` \| `422 Unprocessable Entity` |

**リクエスト本体**:

```json
{
  "project_name": "my_project",
  "case_name": "my_case"
}
```

**レスポンス本体**:

```json
{
  "proposal_id": "prop-550e8400-e29b-41d4-a716",
  "state": "applied",
  "before_after_diffs": [
    {
      "path": "boundary_conditions.Pt_in",
      "before": 200000,
      "after": 250000
    },
    {
      "path": "geometry.num_cells",
      "before": 100,
      "after": 150
    }
  ]
}
```

---

### 4.3.3 POST `/config-changes/proposals/{proposal_id}/confirm`

提案パッチを確定・永続化

| 項目 | 値 |
|------|-----|
| **説明** | パッチを確定、ケース YAML に保存 |
| **メソッド** | `POST` |
| **パスパラメータ** | `proposal_id` (str) |
| **ステータスコード** | `200 OK` \| `409 Conflict` (状態が不適切) |

**リクエスト本体**:

```json
{
  "project_name": "my_project",
  "case_name": "my_case"
}
```

**レスポンス本体**:

```json
{
  "proposal_id": "prop-550e8400-e29b-41d4-a716",
  "state": "confirmed",
  "updated_case": {
    "fluid": { "working_fluid": "air" },
    "boundary_conditions": {
      "Pt_in": 250000,
      "Tt_in": 300,
      "Ps_out": 101325
    },
    "geometry": { "num_cells": 150 }
  }
}
```

---

### 4.3.4 POST `/config-changes/proposals/{proposal_id}/reject`

提案パッチを却下

| 項目 | 値 |
|------|-----|
| **説明** | 提案を却下・削除 |
| **メソッド** | `POST` |
| **パスパラメータ** | `proposal_id` (str) |
| **ステータスコード** | `200 OK` \| `409 Conflict` |

**リクエスト本体**:

```json
{
  "project_name": "my_project",
  "case_name": "my_case"
}
```

**レスポンス本体**:

```json
{
  "proposal_id": "prop-550e8400-e29b-41d4-a716",
  "state": "rejected"
}
```

---

---

# 📏 5. Units Router

**用途**: 単位設定の管理

**プレフィックス**: `/api/units`

---

## 5.1 GET `/preferences`

現在の単位設定を取得

| 項目 | 値 |
|------|-----|
| **説明** | グループ単位の現在の設定を返す |
| **メソッド** | `GET` |
| **ステータスコード** | `200 OK` |

**レスポンス本体**:

```json
{
  "pressure": "Pa",
  "temperature": "K",
  "length": "m",
  "velocity": "m/s",
  "diameter": "m",
  "time": "s"
}
```

---

## 5.2 PATCH `/preferences`

単位設定を部分更新

| 項目 | 値 |
|------|-----|
| **説明** | 一部グループの単位を変更 |
| **メソッド** | `PATCH` |
| **ステータスコード** | `200 OK` \| `400 Bad Request` |

**リクエスト本体**:

```json
{
  "pressure": "bar",
  "temperature": "°C",
  "diameter": "mm"
}
```

**レスポンス本体**: 全設定を返す（GET と同じ形式）

---

## 5.3 GET `/groups`

利用可能な全単位グループと変換仕様を取得

| 項目 | 値 |
|------|-----|
| **説明** | 全単位オプションと変換係数を返す |
| **メソッド** | `GET` |
| **ステータスコード** | `200 OK` |

**レスポンス本体**:

```json
{
  "pressure": {
    "Pa": { "scale": 1.0, "offset": 0.0 },
    "bar": { "scale": 1e-5, "offset": 0.0 },
    "atm": { "scale": 9.8692e-6, "offset": 0.0 },
    "psi": { "scale": 0.00014504, "offset": 0.0 }
  },
  "temperature": {
    "K": { "scale": 1.0, "offset": 0.0 },
    "°C": { "scale": 1.0, "offset": -273.15 },
    "°F": { "scale": 1.8, "offset": -459.67 }
  },
  "length": {
    "m": { "scale": 1.0, "offset": 0.0 },
    "mm": { "scale": 1000.0, "offset": 0.0 },
    "cm": { "scale": 100.0, "offset": 0.0 }
  },
  "velocity": {
    "m/s": { "scale": 1.0, "offset": 0.0 },
    "km/h": { "scale": 3.6, "offset": 0.0 }
  },
  "diameter": {
    "m": { "scale": 1.0, "offset": 0.0 },
    "mm": { "scale": 1000.0, "offset": 0.0 },
    "μm": { "scale": 1e6, "offset": 0.0 }
  }
}
```

**変換式**: `表示値 = SI値 × scale + offset`

**例**:
- `Si 圧力 = 200000 Pa → bar`: `200000 × 1e-5 = 2.0 bar`
- `SI 温度 = 300 K → °C`: `300 × 1.0 + (-273.15) = 26.85°C`

---

---

# 🐛 6. Debug Router

**用途**: クライアント側ログをサーバーで収集

**プレフィックス**: `/api/debug`

---

## 6.1 POST `/log`

クライアント側デバッグメッセージをサーバーに送信

| 項目 | 値 |
|------|-----|
| **説明** | ブラウザ側のログをサーバー側で記録 |
| **メソッド** | `POST` |
| **ステータスコード** | `200 OK` |

**リクエスト本体**:

```json
{
  "message": "WebSocket connection failed",
  "details": "Connection refused on ws://localhost:8000/ws"
}
```

**レスポンス本体**: `null`

---

---

# 🚀 ワークフロー例

## ワークフロー 1: 単一ケースのシミュレーション実行

```
1. GET /api/cases/projects/my_project/cases/
   └─ ケース一覧を取得

2. GET /api/cases/projects/my_project/cases/my_case
   └─ ケース設定を確認

3. PUT /api/cases/projects/my_project/cases/my_case
   └─ 必要に応じて設定を更新

4. POST /api/simulation/run
   ├─ リクエスト: { project_name, case_name, config: null }
   └─ レスポンス: { job_id }

5. GET /api/simulation/status/{job_id}
   ├─ ポーリング間隔: 800ms
   └─ 完了まで繰り返す

6. GET /api/simulation/result/{job_id}
   └─ プロット、テーブル、CSV を取得
```

---

## ワークフロー 2: マルチバリュースイープ

```
1. POST /api/simulation/run
   ├─ リクエスト:
   │  {
   │    project_name: "my_project",
   │    case_name: "my_case",
   │    config: {
   │      "boundary_conditions.Pt_in": [200000, 250000, 300000],
   │      "boundary_conditions.Tt_in": [300, 350]
   │    }
   │  }
   └─ レスポンス: { job_id }

2. GET /api/simulation/status/{job_id}
   └─ ポーリング（複数実行のため時間がかかる）

3. GET /api/simulation/result/{job_id}
   ├─ plots: オーバーレイプロット
   ├─ table_rows: 全実行結果の集約
   ├─ csv_content: 全結果
   └─ run_count: 6 (3×2)
```

---

## ワークフロー 3: AI 支援設定変更

```
1. POST /api/chat/threads
   └─ チャットスレッドを作成

2. POST /api/chat/messages
   ├─ ユーザー: "Optimize for lower pressure drop"
   └─ AI: (提案内容)

3. POST /api/chat/config-changes/proposals
   ├─ AI が設定変更を提案
   └─ レスポンス: { proposal_id, changes: [...] }

4. POST /api/chat/config-changes/proposals/{proposal_id}/apply
   ├─ 差分を表示（before/after）
   └─ ユーザーが確認

5. POST /api/chat/config-changes/proposals/{proposal_id}/confirm
   ├─ YAML に永続化
   └─ ケース更新完了

6. POST /api/simulation/run
   └─ 更新されたケースで実行
```

---

# 📊 エラーハンドリング

## エラーレスポンス形式

すべてのエラーは以下の形式：

```json
{
  "detail": "エラー説明"
}
```

---

## HTTP ステータスコード一覧

| コード | 意味 | 例 |
|--------|------|-----|
| `200` | 成功 | GET 成功 |
| `201` | 作成完了 | POST で新規作成 |
| `204` | 内容なし（成功） | DELETE 完了 |
| `400` | リクエストエラー | 無効なパラメータ |
| `404` | 見つからない | ケースが存在しない |
| `409` | 競合 | ケース名が重複 |
| `422` | 処理不可 | 検証失敗 |
| `500` | サーバーエラー | LLM エラー等 |

---

## エラー例

### 400 Bad Request

```json
{
  "detail": "Invalid project name: contains invalid characters"
}
```

### 404 Not Found

```json
{
  "detail": "Case 'my_case' not found."
}
```

### 409 Conflict

```json
{
  "detail": "Case 'my_case' already exists."
}
```

### 500 Internal Server Error

```json
{
  "detail": "LLM provider error: connection timeout"
}
```

---

# 📚 参考資料

## ドキュメント

- [docs/architecture.md](./docs/architecture.md) — 全体アーキテクチャ
- [docs/api-endpoints.md](./docs/api-endpoints.md) — 詳細 API ドキュメント
- [src/supersonic_atomizer/gui/routers/](./src/supersonic_atomizer/gui/routers/) — ルーター実装

## 実装ファイル

| ファイル | 責務 |
|---------|------|
| `fastapi_app.py` | FastAPI アプリケーション工場 |
| `routers/index_router.py` | HTML シェル |
| `routers/cases_router.py` | ケース CRUD |
| `routers/simulation_router.py` | ジョブ管理 |
| `routers/chat_router.py` | チャット・AI 提案 |
| `routers/units_router.py` | 単位設定 |
| `routers/debug_router.py` | デバッグログ |
| `service_bridge.py` | ソルバーへのアダプタ |

---

# 🔗 実行コマンド

## 開発環境で起動

```bash
# 環境設定
source .venv/bin/activate  # Linux/Mac
# または
.\.venv\Scripts\Activate.ps1  # Windows PowerShell

# FastAPI 起動（ホットリロード）
uv run uvicorn supersonic_atomizer.gui.fastapi_app:app --reload

# または直接
uvicorn supersonic_atomizer.gui.fastapi_app:app --reload --host 0.0.0.0 --port 8000
```

## ブラウザアクセス

```
http://localhost:8000
```

## API ドキュメント（自動生成）

```
http://localhost:8000/docs          (Swagger UI)
http://localhost:8000/redoc         (ReDoc)
```

---

# 🎯 まとめ

| ルーター | 主機能 | エンドポイント数 |
|---------|--------|-----------------|
| **Index** | SPA シェル | 2 |
| **Cases** | プロジェクト・ケース CRUD | 19 |
| **Simulation** | バックグラウンドジョブ | 3 |
| **Chat** | チャット・AI 提案 | 12 |
| **Units** | 単位設定 | 3 |
| **Debug** | クライアントログ | 1 |
| **合計** | | **40** |

API 設計は以下の原則に従っています：

✅ **ノンブロッキング** — 実行・ポーリング・結果取得の 3 ステップ  
✅ **RESTful** — HTTP メソッド（GET、POST、PUT、DELETE）に従う  
✅ **JSON** — 標準的なリクエスト・レスポンス形式  
✅ **エラー処理** — 明確なステータスコードと詳細メッセージ  
✅ **スケーラブル** — 複数値スイープと AI 支援機能をサポート
