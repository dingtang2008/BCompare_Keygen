#!/usr/bin/env python3
"""
对 macOS 上的 Beyond Compare 5.x 应用进行 RSA modulus 替换 + ad-hoc 重签。

为什么需要这个脚本(README 旧手动方案在新版 macOS 上的坑):

  1. 现在的 BCompare 是 Universal Binary(x86_64 + arm64),fat 文件里能搜到
     两处 `p1+wk` —— 不是同一份密钥重复两次,而是两个架构 slice 各持一份。
     旧 README "改第二处" 的说法在 Intel Mac 上是错的(改的是 arm64 那份,
     Intel 跑的 x86_64 完全没动)。本脚本直接两处都改。

  2. macOS Ventura+ 的 App Management 保护让终端无法直接修改
     /Applications 里的 .app —— 必须先在别处操作再用 Finder 拖回去。
     脚本默认输出到 ~/Desktop。

  3. 修改后代码签名失效,Apple Silicon 严格,Intel 上 AMFI 也会拒。
     必须 ad-hoc 重签,但 codesign 嫌弃 com.apple.FinderInfo,需要先精准
     清理 .app 根、.appex、.framework 上的这个 xattr(xattr -cr 静默失败)。

用法:
    python3 patch_macos.py
    python3 patch_macos.py --src "/Applications/Beyond Compare.app" \\
                          --dst ~/Desktop/Beyond\\ Compare.app
"""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

OLD_TAIL = b"p1+wk"
NEW_TAIL = b"pn+wk"
DEFAULT_SRC = "/Applications/Beyond Compare.app"
DEFAULT_DST = str(Path.home() / "Desktop" / "Beyond Compare.app")

# 这几个目录上的 com.apple.FinderInfo 必须显式删除,否则 codesign 会以
# "resource fork, Finder information, or similar detritus not allowed" 报错。
# 列表是实测找出来的:`xattr -cr` 不会进入 .appex 和 .framework。
FINDERINFO_BLOCKERS = [
    "",
    "Contents/PlugIns/BCFinder.appex",
    "Contents/Frameworks/LetsMove.framework",
]


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
        if not target.exists():
            continue
        subprocess.run(
            ["xattr", "-d", "com.apple.FinderInfo", str(target)],
            stderr=subprocess.DEVNULL,
        )


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--src", default=DEFAULT_SRC, help=f"源 .app 路径 (默认 {DEFAULT_SRC})")
    ap.add_argument("--dst", default=DEFAULT_DST, help=f"输出 .app 路径 (默认 {DEFAULT_DST})")
    args = ap.parse_args()

    src = Path(args.src)
    dst = Path(args.dst)
    if not src.is_dir():
        print(f"ERROR: 源不存在或不是目录: {src}", file=sys.stderr)
        return 1
    if src.resolve() == dst.resolve():
        print("ERROR: --src 和 --dst 不能相同(App Management 会拦原地修改)", file=sys.stderr)
        return 1

    if dst.exists():
        print(f"[1/4] 清理已存在的 {dst}")
        shutil.rmtree(dst)
    print(f"[1/4] 拷贝 {src} → {dst}")
    shutil.copytree(src, dst, symlinks=True)

    bin_path = dst / "Contents" / "MacOS" / "BCompare"
    bak = bin_path.parent / "BCompare.bak"
    if bak.exists():
        bak.unlink()

    n = patch_binary(bin_path)
    if n == 0:
        print("ERROR: 未找到 p1+wk —— 可能已经 patch 过,或 BCompare 版本不匹配", file=sys.stderr)
        return 1
    print(f"[2/4] 替换 {n} 处 p1+wk → pn+wk")

    print("[3/4] 清理 com.apple.FinderInfo")
    strip_finderinfo(dst)

    print("[4/4] ad-hoc 重签 + 校验")
    try:
        subprocess.run(["codesign", "--force", "--deep", "--sign", "-", str(dst)], check=True)
        subprocess.run(["codesign", "-v", str(dst)], check=True)
    except subprocess.CalledProcessError as e:
        print(f"ERROR: 签名失败: {e}", file=sys.stderr)
        return 1

    print()
    print("=" * 60)
    print(f"完成。已 patch + 重签的 .app: {dst}")
    print()
    print("接下来你来做(脚本无法绕过的 GUI 步骤):")
    print(f"  1) Finder 把 {dst.name} 拖进 /Applications,选择「替换」")
    print("     —— 系统会要求授权 Finder 修改 /Applications,同意即可。")
    print("  2) 第一次启动:右键 → 打开,Gatekeeper 弹窗里点「打开」")
    print("     —— 因为 ad-hoc 签名 = 未知开发者。也可在 系统设置 →")
    print("     隐私与安全性 底部点「仍要打开」。")
    print("  3) 启动后用 keygen 生成的 license 注册即可。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
