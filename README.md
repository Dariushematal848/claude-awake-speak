# claude-awake-speak — 让你的 Claude Code 会说话

> 给 Claude Code 装上嘴巴。每次回复结束后，自动用语音朗读中文内容，告别冷冰冰的纯文字终端。

## 功能特点

Claude Code 回复完毕后，自动用 **微软 Edge TTS** 把中文内容读出来。

- 只读中文，代码块、表格、URL、纯英文全部跳过
- 超过 300 字自动截断（不然听到天荒地老）
- 后台异步播放，不阻塞 Claude 的工作流
- 8 种微软官方音色，实时切换，支持试听
- 完全免费，不需要 API Key
- **不消耗额外 token**（hook 只读取已生成的回复文本，不触发新的 API 调用）

## 可选音色

| 音色 ID | 中文名 | 性别 | 风格 | 推荐场景 |
|---------|--------|------|------|---------|
| `zh-CN-YunjianNeural` | 云健 | 男 | 体育解说风 | **默认**，热血激情 |
| `zh-CN-YunxiNeural` | 云希 | 男 | 小说旁白风 | 阳光开朗 |
| `zh-CN-YunyangNeural` | 云扬 | 男 | 新闻播报风 | 专业稳重 |
| `zh-CN-XiaoxiaoNeural` | 晓晓 | 女 | 通用女声 | 温暖亲切 |
| `zh-CN-XiaoyiNeural` | 晓伊 | 女 | 儿童故事风 | 活泼可爱 |
| `zh-CN-YunxiaNeural` | 云夏 | 男 | 少儿男声 | 可爱少年感 |
| `zh-CN-liaoning-XiaobeiNeural` | 晓北 | 女 | 辽宁方言 | 搞笑担当 |
| `zh-CN-shaanxi-XiaoniNeural` | 晓妮 | 女 | 陕西方言 | 地道西北味 |

## 安装

### 1. 安装依赖

```bash
pip install edge-tts
```

### 2. 复制脚本

把 `tts-speak.py` 复制到你的 Claude Code hooks 目录：

```bash
# Windows
mkdir %USERPROFILE%\.claude\hooks
copy tts-speak.py %USERPROFILE%\.claude\hooks\tts-speak.py

# macOS/Linux
mkdir -p ~/.claude/hooks
cp tts-speak.py ~/.claude/hooks/tts-speak.py
```

### 3. 配置 Hook

编辑 `~/.claude/settings.json`，添加 `hooks` 字段：

```json
{
  "hooks": {
    "Stop": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "python ~/.claude/hooks/tts-speak.py",
            "timeout": 30,
            "async": true
          }
        ]
      }
    ]
  }
}
```

> **Windows 用户**：把路径改为 `python C:/Users/你的用户名/.claude/hooks/tts-speak.py`

### 4. 复制音色切换工具（可选）

```bash
# Windows
copy voice-switch.py %USERPROFILE%\.claude\hooks\voice-switch.py

# macOS/Linux
cp voice-switch.py ~/.claude/hooks/voice-switch.py
```

### 5. 重启 Claude Code

退出当前会话，重新打开即可。

## 配置

### 切换音色

**方法一：命令行工具（推荐）**

```bash
# 交互式菜单
python ~/.claude/hooks/voice-switch.py

# 直接切换
python ~/.claude/hooks/voice-switch.py set xiaoxiao    # 晓晓·温暖亲切
python ~/.claude/hooks/voice-switch.py set yunxi        # 云希·阳光开朗
python ~/.claude/hooks/voice-switch.py set xiaobei      # 晓北·东北方言

# 试听音色
python ~/.claude/hooks/voice-switch.py preview yunyang   # 试听云扬
python ~/.claude/hooks/voice-switch.py preview xiaoyi    # 试听晓伊

# 列出所有音色
python ~/.claude/hooks/voice-switch.py list

# 查看当前设置
python ~/.claude/hooks/voice-switch.py status
```

**方法二：直接编辑配置文件**

配置文件位置：`~/.claude/hooks/voice-config.json`

```json
{
  "voice": "yunjian",
  "max_chars": 300,
  "enabled": true
}
```

`voice` 字段可选值：`yunjian` / `yunxi` / `yunyang` / `xiaoxiao` / `xiaoyi` / `yunxia` / `xiaobei` / `xiaoni`

### 调整最大朗读字数

```bash
python ~/.claude/hooks/voice-switch.py chars 500   # 改成500字
```

或编辑 `voice-config.json` 的 `max_chars` 字段。

### 开关语音

```bash
python ~/.claude/hooks/voice-switch.py off    # 关闭
python ~/.claude/hooks/voice-switch.py on     # 开启
```

或编辑 `voice-config.json` 的 `enabled` 字段。

## 工作原理

```
Claude 回复结束
       ↓
Stop Hook 触发
       ↓
tts-speak.py 从 stdin 读取 last_assistant_message
       ↓
提取中文文本（过滤代码/表格/URL/英文）
       ↓
edge-tts 生成 mp3 临时文件
       ↓
系统播放音频（Windows: PowerShell / macOS: afplay / Linux: mpv）
       ↓
播放完毕，自动删除临时文件
```

## 平台支持

| 平台 | 状态 | 播放方式 |
|------|------|---------|
| Windows | 已验证 | PowerShell MediaPlayer（presentationCore） |
| macOS | 支持 | afplay（系统自带） |
| Linux | 支持 | mpv / ffplay / aplay |

## 已知限制

- edge-tts 需要联网（调用微软 Edge 的在线 TTS 服务）
- 不支持离线使用
- 长文本会被截断（默认 300 字）
- 音色固定为预设，不支持声纹克隆

## 常见问题

### 语音会消耗额外的 token 吗？

**不会。** Hook 是在 Claude 回复生成完毕后触发的，它只读取已经生成好的 `last_assistant_message` 文本，不会触发新的 API 调用，不产生任何额外 token 消耗。

### 为什么听到的是乱码？

大概率是 Windows 编码问题。确保脚本里用了 `sys.stdin.buffer.read().decode('utf-8')` 而不是 `sys.stdin.read()`。

### 为什么没有声音？

排查步骤：
1. `pip show edge-tts` 确认已安装
2. `edge-tts --voice zh-CN-YunjianNeural --text "测试" --write-media test.mp3` 手动生成
3. 双击 `test.mp3` 确认有声音
4. 检查 `~/.claude/settings.json` 的 hooks 配置
5. 重启 Claude Code

## 开源协议

MIT

## 致谢

- [edge-tts](https://github.com/rany2/edge-tts) — 免费的微软 Edge TTS Python 库
- [Claude Code](https://claude.com/claude-code) — Anthropic 的 CLI 工具
