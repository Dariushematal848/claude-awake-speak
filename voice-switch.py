#!/usr/bin/env python3
"""
voice-switch — 切换 claude-awake-speak 的语音设置
支持：切换音色、试听音色、调整字数上限、开关语音
"""

import sys
import os

# 把 tts-speak.py 所在目录加入 path，复用其中的配置和音色表
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from importlib import import_module
tts = import_module("tts-speak")


def print_voices():
    """打印音色列表"""
    config = tts.load_config()
    current = config.get("voice", tts.DEFAULT_VOICE)
    print("\n可选音色：")
    print("-" * 70)
    for i, (key, v) in enumerate(tts.VOICES.items(), 1):
        marker = " <-- 当前" if key == current else ""
        print(f"  {i}. {key:10s} | {v['gender']} | {v['style']:6s} | {v['desc']}{marker}")
    print("-" * 70)


def preview_voice(voice_key: str):
    """试听指定音色"""
    if voice_key not in tts.VOICES:
        print(f"未知音色: {voice_key}")
        return
    v = tts.VOICES[voice_key]
    print(f"试听: {voice_key} ({v['gender']} · {v['style']})")
    import tempfile, subprocess
    with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as f:
        tmp_path = f.name
    try:
        subprocess.run(
            ['edge-tts', '--voice', v['id'], '--text',
             f"你好，我是{v['style']}音色，{v['desc']}。",
             '--write-media', tmp_path],
            capture_output=True, timeout=15
        )
        if os.path.exists(tmp_path) and os.path.getsize(tmp_path) > 0:
            tts.play_audio(tmp_path)
            print("正在播放...")
        else:
            print("生成失败，请检查 edge-tts 是否安装")
    except Exception as e:
        print(f"出错: {e}")


def switch_voice(voice_key: str):
    """切换音色"""
    if voice_key not in tts.VOICES:
        print(f"未知音色: {voice_key}")
        return
    config = tts.load_config()
    config["voice"] = voice_key
    tts.save_config(config)
    v = tts.VOICES[voice_key]
    print(f"已切换为: {voice_key} ({v['gender']} · {v['style']} · {v['desc']})")


def toggle_voice(enable: bool = None):
    """开关语音"""
    config = tts.load_config()
    if enable is None:
        enable = not config.get("enabled", True)
    config["enabled"] = enable
    tts.save_config(config)
    print(f"语音已{'开启' if enable else '关闭'}")


def set_max_chars(n: int):
    """设置最大朗读字数"""
    config = tts.load_config()
    config["max_chars"] = n
    tts.save_config(config)
    print(f"最大朗读字数已设为: {n}")


def show_status():
    """显示当前配置状态"""
    config = tts.load_config()
    voice_key = config.get("voice", tts.DEFAULT_VOICE)
    v = tts.VOICES.get(voice_key, {})
    enabled = config.get("enabled", True)
    max_chars = config.get("max_chars", tts.MAX_CHARS)
    print(f"\n当前配置:")
    print(f"  语音状态: {'开启' if enabled else '关闭'}")
    print(f"  当前音色: {voice_key} ({v.get('gender', '?')} · {v.get('style', '?')})")
    print(f"  最大字数: {max_chars}")
    print(f"  配置文件: {tts._config_path()}")
    print()


def interactive_menu():
    """交互式菜单"""
    print("\n=== claude-awake-speak 语音设置 ===\n")
    show_status()
    print("操作：")
    print("  1. 切换音色")
    print("  2. 试听音色")
    print("  3. 开启/关闭语音")
    print("  4. 设置最大朗读字数")
    print("  5. 查看当前状态")
    print("  0. 退出")
    print()

    while True:
        choice = input("请选择 (0-5): ").strip()
        if choice == "0":
            print("再见！")
            break
        elif choice == "1":
            print_voices()
            keys = list(tts.VOICES.keys())
            sel = input(f"输入编号 (1-{len(keys)}) 或音色名: ").strip()
            if sel.isdigit() and 1 <= int(sel) <= len(keys):
                switch_voice(keys[int(sel) - 1])
            elif sel in tts.VOICES:
                switch_voice(sel)
            else:
                print("无效选择")
        elif choice == "2":
            print_voices()
            keys = list(tts.VOICES.keys())
            sel = input(f"输入编号 (1-{len(keys)}) 或音色名: ").strip()
            if sel.isdigit() and 1 <= int(sel) <= len(keys):
                preview_voice(keys[int(sel) - 1])
            elif sel in tts.VOICES:
                preview_voice(sel)
            else:
                print("无效选择")
        elif choice == "3":
            toggle_voice()
        elif choice == "4":
            n = input("最大朗读字数 (当前 {}): ".format(tts.load_config().get("max_chars", tts.MAX_CHARS))).strip()
            if n.isdigit() and int(n) > 0:
                set_max_chars(int(n))
            else:
                print("请输入正整数")
        elif choice == "5":
            show_status()
        else:
            print("无效选择")
        print()


def print_usage():
    print("""
用法：
  python voice-switch.py                    交互式菜单
  python voice-switch.py list               列出所有音色
  python voice-switch.py set <音色名>       切换音色
  python voice-switch.py preview <音色名>   试听音色
  python voice-switch.py on                 开启语音
  python voice-switch.py off                关闭语音
  python voice-switch.py chars <数字>       设置最大朗读字数
  python voice-switch.py status             查看当前状态

音色名：yunjian, yunxi, yunyang, xiaoxiao, xiaoyi, yunxia, xiaobei, xiaoni
""")


def main():
    args = sys.argv[1:]

    if not args:
        interactive_menu()
        return

    cmd = args[0].lower()

    if cmd == "list":
        print_voices()
    elif cmd == "set" and len(args) >= 2:
        switch_voice(args[1])
    elif cmd == "preview" and len(args) >= 2:
        preview_voice(args[1])
    elif cmd == "on":
        toggle_voice(True)
    elif cmd == "off":
        toggle_voice(False)
    elif cmd == "chars" and len(args) >= 2:
        if args[1].isdigit():
            set_max_chars(int(args[1]))
        else:
            print("请输入正整数")
    elif cmd == "status":
        show_status()
    else:
        print_usage()


if __name__ == '__main__':
    main()
