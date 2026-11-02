# Colab MCP 接続メモ（この課題用）

公式: [Colab MCP README](https://github.com/googlecolab/colab-mcp) · [発表記事](https://developers.googleblog.com/announcing-the-colab-mcp-server-connect-any-ai-agent-to-google-colab/)

## いまの設定（PC）

`%USERPROFILE%\.cursor\mcp.json` の `colab-proxy-mcp` は、公式の素の `uvx git+...` ではなく、Windows向け **bridge** を使っている（正常）。

```json
"colab-proxy-mcp": {
  "command": "uv",
  "args": [
    "run",
    "--with",
    "git+https://github.com/googlecolab/colab-mcp",
    "python",
    "<PATH_TO>/colab_mcp_bridge.py"
  ],
  "timeout": 180000
}
```

- `timeout` は **180000**（3分）。認証・初回起動が 30 秒で切れるのを防ぐ。
- ログ: `%LOCALAPPDATA%\colab-mcp-bridge\logs\`
- WebSocket: `localhost:8765`

## 緑マークなのに Agent から使えないとき

Cursor の MCP 一覧が緑でも、Agent 側は **`mcp_auth` 完了前**だと編集ツールが見えない。

1. MCP を再読み込み（設定変更後は必須）
2. Cursor の MCP パネルで `colab-proxy-mcp` を開き、**Authenticate / 接続**をユーザーが押す  
   （Agent 経由の `mcp_auth` はクライアント側 30 秒制限で落ちやすい）
3. 認証後、Agent に「接続して」と頼む → `open_colab_browser_connection`
4. 初回は空ノートが開く。ランタイムを **G4** に変更
5. Drive マウントはユーザー操作

## 公式との差分

| 項目 | 公式 README / Blog | この PC |
|---|---|---|
| 起動 | `uvx` + `git+https://github.com/googlecolab/colab-mcp` | bridge 経由（意図的） |
| クライアント例 | Gemini CLI / Claude Code / Windsurf | Cursor + bridge |
| タイムアウト | 30000 | **180000** |

素の公式設定に戻すのは、bridge が動かないときの最終手段。
