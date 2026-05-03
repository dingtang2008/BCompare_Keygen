#!/usr/bin/env python3
"""
macOS 一键 patch + 重签 + 安装回 /Applications + 生成 license + 启动注册。

完整流程(自动):
  1. 退出正在运行的 Beyond Compare
  2. 把 .app 拷到 ~/Desktop,把 RSA modulus 末位 p1+wk 改成 pn+wk
     (同时覆盖 x86_64 和 arm64 两个 slice)
  3. 清理 com.apple.FinderInfo 后 ad-hoc 重签
  4. 通过 AppleScript 让 Finder 把桌面副本移回 /Applications
     (Finder 自带 App Management 权限,无需手动拖拽 ——
      首次执行 macOS 会弹「允许 osascript 控制 Finder」,点 OK 即可)
  5. 用 keygen 生成 license 并复制到剪贴板
  6. 启动 Beyond Compare,等弹注册框时 ⌘V 粘贴 → 确定

用法:
    python3 patch_macos.py
    python3 patch_macos.py -u Alice -c Acme -s Abcd-1234 -n 5
    python3 patch_macos.py --no-launch       # 不自动启动 BC
    python3 patch_macos.py --no-keygen       # 只 patch,不生成 license
"""

import argparse
import platform
import shutil
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    from lic_manager import LicenseEncoder, check_serial
except ImportError as e:
    print(f"ERROR: 导入 lic_manager 失败({e})", file=sys.stderr)
    print("请先安装依赖:", file=sys.stderr)
    print("  pip3 install -r requirements.txt", file=sys.stderr)
    print("或在 venv 里运行(macOS Homebrew Python 受 PEP-668 保护):", file=sys.stderr)
    print("  python3.13 -m venv .venv", file=sys.stderr)
    print("  .venv/bin/pip install -r requirements.txt", file=sys.stderr)
    print("  .venv/bin/python patch_macos.py", file=sys.stderr)
    sys.exit(1)

OLD_TAIL = b"p1+wk"
NEW_TAIL = b"pn+wk"
DEFAULT_SRC = "/Applications/Beyond Compare.app"
DEFAULT_DST = str(Path.home() / "Desktop" / "Beyond Compare.app")

# 这三个目录上的 com.apple.FinderInfo 必须显式删,否则 codesign 会报
# "resource fork, Finder information, or similar detritus not allowed"。
# `xattr -cr` 不会进入 .appex 和 .framework,会静默失败。
FINDERINFO_BLOCKERS = [
    "",
    "Contents/PlugIns/BCFinder.appex",
    "Contents/Frameworks/LetsMove.framework",
]


def osascript(script: str) -> str:
    r = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"osascript: {r.stderr.strip()}")
    return r.stdout.strip()


def quit_bcompare(timeout: float = 5.0) -> bool:
    """让 BCompare 优雅退出,等到进程消失。返回是否成功。"""
    osascript("""
        if application "Beyond Compare" is running then
            tell application "Beyond Compare" to quit
        end if
    """)
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if subprocess.run(["pgrep", "-x", "BCompare"], capture_output=True).returncode != 0:
            return True
        time.sleep(0.2)
    return False


def patch_binary(bin_path: Path) -> int:
    data = bytearray(bin_path.read_bytes())
    count = 0
    pos = 0
    while True:
        idx = data.find(OLD_TAIL, pos)
        if idx == -1:
            break
        data[idx:idx + len(OLD_TAIL)] = NEW_TAIL
        count += 1
        pos = idx + len(NEW_TAIL)
    if count:
        bin_path.write_bytes(bytes(data))
    return count


def strip_finderinfo(bundle: Path) -> None:
    for rel in FINDERINFO_BLOCKERS:
        target = bundle / rel if rel else bundle
        if target.exists():
            subprocess.run(
                ["xattr", "-d", "com.apple.FinderInfo", str(target)],
                stderr=subprocess.DEVNULL,
            )


def codesign_adhoc(bundle: Path) -> None:
    subprocess.run(
        ["codesign", "--force", "--deep", "--sign", "-", str(bundle)],
        check=True, capture_output=True,
    )
    subprocess.run(["codesign", "-v", str(bundle)], check=True, capture_output=True)


def finder_move(src: Path, dst_parent: Path) -> None:
    """让 Finder 把 src 移到 dst_parent/(覆盖同名)。Finder 自带 App
    Management 权限,所以能写入 /Applications。"""
    script = f'''
        tell application "Finder"
            set sourceItem to POSIX file "{src}" as alias
            set destFolder to POSIX file "{dst_parent}" as alias
            move sourceItem to destFolder with replacing
        end tell
    '''
    osascript(script)


def pbcopy(text: str) -> None:
    subprocess.run(["pbcopy"], input=text, text=True, check=True)


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("--src", default=DEFAULT_SRC, help=f"源 .app(默认 {DEFAULT_SRC})")
    ap.add_argument("--dst", default=DEFAULT_DST, help=f"中转副本路径(默认 {DEFAULT_DST})")
    ap.add_argument("-u", "--user", default="Test", help="license username(默认 Test)")
    ap.add_argument("-c", "--company", default="Home", help="license company(默认 Home)")
    ap.add_argument("-s", "--serial", default="Abcd-Efgh",
                    help="license serial,需匹配 XXXX-XXXX(默认 Abcd-Efgh)")
    ap.add_argument("-n", "--num", type=int, default=1, help="license 用户数(默认 1)")
    ap.add_argument("--no-keygen", action="store_true",
                    help="只 patch + 安装回 /Applications,不生成 license / 不复制 / 不启动 BC")
    ap.add_argument("--no-launch", action="store_true",
                    help="复制 license 到剪贴板后不自动启动 BC")
    args = ap.parse_args()

    if platform.system() != "Darwin":
        print("ERROR: 仅支持 macOS", file=sys.stderr)
        return 1

    src = Path(args.src)
    dst = Path(args.dst)
    if not src.is_dir():
        print(f"ERROR: 源不存在或不是目录: {src}", file=sys.stderr)
        return 1
    if src.resolve() == dst.resolve():
        print("ERROR: --src 和 --dst 不能相同(App Management 拦截原地修改)", file=sys.stderr)
        return 1
    if not check_serial(args.serial):
        print(f"ERROR: serial {args.serial!r} 不匹配 ^[A-Za-z0-9]{{4}}-[A-Za-z0-9]{{4}}$",
              file=sys.stderr)
        return 1

    total = 6 if not args.no_keygen else 5
    print(f"[1/{total}] 退出正在运行的 Beyond Compare(若有)")
    if not quit_bcompare():
        print("ERROR: BCompare 未能在 5 秒内退出,请手动 ⌘Q 后重试", file=sys.stderr)
        return 1

    print(f"[2/{total}] 拷贝 {src} → {dst}")
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst, symlinks=True)
    bak = dst / "Contents" / "MacOS" / "BCompare.bak"
    if bak.exists():
        bak.unlink()

    bin_path = dst / "Contents" / "MacOS" / "BCompare"
    n = patch_binary(bin_path)
    if n:
        print(f"[3/{total}] 替换 {n} 处 p1+wk → pn+wk")
    else:
        print(f"[3/{total}] 未找到 p1+wk(已经 patched 过,跳过)")

    print(f"[4/{total}] 清理 com.apple.FinderInfo 并 ad-hoc 重签")
    strip_finderinfo(dst)
    try:
        codesign_adhoc(dst)
    except subprocess.CalledProcessError as e:
        msg = e.stderr.decode() if e.stderr else str(e)
        print(f"ERROR: 签名失败: {msg}", file=sys.stderr)
        return 1

    print(f"[5/{total}] 通过 Finder 把 {dst.name} 移回 {src.parent}/")
    print("       (首次执行 macOS 会弹「允许控制 Finder」,点 OK 即可)")
    try:
        finder_move(dst, src.parent)
    except RuntimeError as e:
        print(f"ERROR: Finder 移动失败: {e}", file=sys.stderr)
        print(f"       请手动把 {dst} 拖到 {src.parent}/ 替换", file=sys.stderr)
        return 1

    if args.no_keygen:
        print()
        print("=" * 60)
        print(f"✅ 完成。{src} 已替换为 patched + 重签的版本。")
        return 0

    print(f"[6/{total}] 生成 license 并复制到剪贴板")
    key = LicenseEncoder(
        username=args.user,
        atsite=args.company,
        user_num=args.num,
        serial_num=args.serial,
    ).encode()
    pbcopy(key)

    if not args.no_launch:
        subprocess.Popen(["open", "-a", "Beyond Compare"])

    print()
    print("=" * 60)
    print("✅ 一切就绪。")
    print(f"   user={args.user!r}  company={args.company!r}  "
          f"serial={args.serial!r}  num={args.num}")
    print("   license 已复制到剪贴板。")
    if args.no_launch:
        print("   接下来:打开 Beyond Compare → 等弹注册框 →")
    else:
        print("   Beyond Compare 已启动 → 等弹「评估模式错误」 →")
    print("   1) 点「输入密钥」")
    print("   2) 在输入框里 ⌘V 粘贴")
    print("   3) 点「确定」激活")
    print()
    print("(若首次启动弹「无法验证开发者」,")
    print(" 去「系统设置 → 隐私与安全性」底部点「仍要打开」即可)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
