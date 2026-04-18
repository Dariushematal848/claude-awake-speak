#!/usr/bin/env python3
"""
claude-awake-speak — 让你的 Claude Code 会说话
Claude Code Stop Hook: 每次回复后自动朗读中文内容。

Usage: 配置为 Claude Code 的 Stop hook，自动在每次回复后朗读中文内容。
See README.md for installation instructions.
"""

import sys
import json
import re
import subprocess
import tempfile
import os
import platform

# ============ 音色表 ============

VOICES = {
    "yunjian":   {"id": "zh-CN-YunjianNeural",              "gender": "男", "style": "云健",   "desc": "体育解说风，热血激情，默认音色"},
    "yunxi":     {"id": "zh-CN-YunxiNeural",                "gender": "男", "style": "云希",   "desc": "小说旁白风，阳光开朗"},
    "yunyang":   {"id": "zh-CN-YunyangNeural",              "gender": "男", "style": "云扬",   "desc": "新闻播报风，专业稳重"},
    "xiaoxiao":  {"id": "zh-CN-XiaoxiaoNeural",             "gender": "女", "style": "晓晓",   "desc": "通用女声，温暖亲切"},
    "xiaoyi":    {"id": "zh-CN-XiaoyiNeural",               "gender": "女", "style": "晓伊",   "desc": "儿童故事风，活泼可爱"},
    "yunxia":    {"id": "zh-CN-YunxiaNeural",               "gender": "男", "style": "云夏",   "desc": "少儿男声，可爱少年感"},
    "xiaobei":   {"id": "zh-CN-liaoning-XiaobeiNeural",     "gender": "女", "style": "晓北",   "desc": "辽宁方言，搞笑担当"},
    "xiaoni":    {"id": "zh-CN-shaanxi-XiaoniNeural",       "gender": "女", "style": "晓妮",   "desc": "陕西方言，地道西北味"},
}

DEFAULT_VOICE = "yunjian"
MAX_CHARS = 300

# ============ 配置文件 ============

def _config_path() -> str:
    """配置文件路径：~/.claude/hooks/voice-config.json"""
    home = os.path.expanduser("~")
    return os.path.join(home, ".claude", "hooks", "voice-config.json")


def load_config() -> dict:
    """读取配置文件，不存在则返回默认值"""
    path = _config_path()
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return {"voice": DEFAULT_VOICE, "max_chars": MAX_CHARS, "enabled": True}


def save_config(config: dict):
    """保存配置文件"""
    path = _config_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


def get_voice_id() -> str:
    """获取当前音色 ID"""
    config = load_config()
    voice_key = config.get("voice", DEFAULT_VOICE)
    if voice_key in VOICES:
        return VOICES[voice_key]["id"]
    # 兼容直接写完整 ID 的情况
    for v in VOICES.values():
        if v["id"] == voice_key:
            return voice_key
    return VOICES[DEFAULT_VOICE]["id"]


def get_max_chars() -> int:
    """获取最大朗读字数"""
    config = load_config()
    return config.get("max_chars", MAX_CHARS)


def is_enabled() -> bool:
    """语音是否启用"""
    config = load_config()
    return config.get("enabled", True)

# ============ 文本提取 ============

def extract_chinese_text(text: str) -> str:
    """提取纯中文文本，去掉代码块、表格、URL、英文等"""
    if not text:
        return ""

    text = re.sub(r'```[\s\S]*?```', '', text)
    text = re.sub(r'`[^`]+`', '', text)
    text = re.sub(r'^\|.*\|$', '', text, flags=re.MULTILINE)
    text = re.sub(r'https?://\S+', '', text)
    text = re.sub(r'!?\[([^\]]*)\]\([^)]*\)', r'\1', text)
    text = re.sub(r'^#{1,6}\s*', '', text, flags=re.MULTILINE)
    text = re.sub(r'\*{1,3}([^*]+)\*{1,3}', r'\1', text)

    max_chars = get_max_chars()
    lines = text.split('\n')
    chinese_lines = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if re.search(r'[\u4e00-\u9fff]', line):
            cleaned = re.sub(r'[a-zA-Z0-9_\-\.\/\\:@#$%^&*()=+\[\]{}]+', '', line)
            cleaned = cleaned.strip(' -|*>#~')
            if cleaned:
                chinese_lines.append(cleaned)

    result = '，'.join(chinese_lines)

    if len(result) > max_chars:
        result = result[:max_chars] + "……后面太长了不读了"

    return result

# ============ 播放 ============

def play_audio(file_path: str):
    """跨平台播放音频文件"""
    system = platform.system()

    if system == "Windows":
        win_path = file_path.replace('/', '\\')
        ps1_lines = [
            'Add-Type -AssemblyName presentationCore',
            '$mp = New-Object System.Windows.Media.MediaPlayer',
            '$mp.Open([Uri]"' + win_path + '")',
            'Start-Sleep -Seconds 1',
            '$mp.Play()',
            'Start-Sleep -Seconds 1',
            'while($mp.NaturalDuration.HasTimeSpan -and $mp.Position -lt $mp.NaturalDuration.TimeSpan){',
            '    Start-Sleep -Milliseconds 300',
            '}',
            'Start-Sleep -Milliseconds 500',
            '$mp.Close()',
            'Remove-Item "' + win_path + '" -ErrorAction SilentlyContinue',
            '$ps1 = $MyInvocation.MyCommand.Path',
            'Remove-Item $ps1 -ErrorAction SilentlyContinue',
        ]
        ps1_path = file_path.replace('.mp3', '.ps1')
        with open(ps1_path, 'w', encoding='utf-8') as pf:
            pf.write('\n'.join(ps1_lines))
        subprocess.Popen(
            ['powershell', '-ExecutionPolicy', 'Bypass', '-WindowStyle', 'Hidden', '-File', ps1_path],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            creationflags=0x08000000
        )

    elif system == "Darwin":
        subprocess.Popen(
            ['bash', '-c', f'afplay "{file_path}" && rm -f "{file_path}"'],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )

    else:
        for player_cmd in [
            ['mpv', '--no-video', '--really-quiet', file_path],
            ['ffplay', '-nodisp', '-autoexit', '-loglevel', 'quiet', file_path],
            ['aplay', file_path],
        ]:
            try:
                subprocess.Popen(
                    ['bash', '-c', f'{" ".join(player_cmd)} && rm -f "{file_path}"'],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                )
                return
            except FileNotFoundError:
                continue
        try:
            os.unlink(file_path)
        except OSError:
            pass


def speak(text: str):
    """用 edge-tts 生成音频并播放"""
    if not text:
        return

    voice_id = get_voice_id()

    with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as f:
        tmp_path = f.name

    try:
        result = subprocess.run(
            ['edge-tts', '--voice', voice_id, '--text', text,
             '--write-media', tmp_path],
            capture_output=True, timeout=15
        )

        if (result.returncode == 0
                and os.path.exists(tmp_path)
                and os.path.getsize(tmp_path) > 0):
            play_audio(tmp_path)
        else:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass

# ============ Hook 入口 ============

def main():
    try:
        if not is_enabled():
            return

        raw = sys.stdin.buffer.read().decode('utf-8')
        input_data = json.loads(raw)
        message = input_data.get('last_assistant_message', '')

        if not message:
            return

        text = extract_chinese_text(message)
        if text:
            speak(text)
    except Exception:
        pass


if __name__ == '__main__':
    main()
