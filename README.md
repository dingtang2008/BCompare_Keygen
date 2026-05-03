# Beyond Compare 5 Keygen
基于 Python3 编写，用于生成 Beyond Compare 5.x （已在 5.1 ver 31736 上验证通过）版本注册密钥
## 前置工作
使用 010Editor 等二进制工具，修改 Beyond Compare 可执行文件中内置的 RSA 密钥。

> **macOS 用户**：直接用 `python3 patch_macos.py` 一键完成 patch + ad-hoc 重签，详见下方「注意事项」。手动改的话务必读完事项 1～4，否则在 Apple Silicon 或新版 macOS 上会失败。

修改前：
```
++11Ik:7EFlNLs6Yqc3p-LtUOXBElimekQm8e3BTSeGhxhlpmVDeVVrrUAkLTXpZ7mK6jAPAOhyHiokPtYfmokklPELfOxt1s5HJmAnl-5r8YEvsQXY8-dm6EFwYJlXgWOCutNn2+FsvA7EXvM-2xZ1MW8LiGeYuXCA6Yt2wTuU4YWM+ZUBkIGEs1QRNRYIeGB9GB9YsS8U2-Z3uunZPgnA5pF+E8BRwYz9ZE--VFeKCPamspG7tdvjA3AJNRNrCVmJvwq5SqgEQwINdcmwwjmc4JetVK76og5A5sPOIXSwOjlYK+Sm8rvlJZoxh0XFfyioHz48JV3vXbBKjgAlPAc7Np1+wk
```
修改后（修改字符串末尾的 `p1+wk` 为 `pn+wk` ）：
```
++11Ik:7EFlNLs6Yqc3p-LtUOXBElimekQm8e3BTSeGhxhlpmVDeVVrrUAkLTXpZ7mK6jAPAOhyHiokPtYfmokklPELfOxt1s5HJmAnl-5r8YEvsQXY8-dm6EFwYJlXgWOCutNn2+FsvA7EXvM-2xZ1MW8LiGeYuXCA6Yt2wTuU4YWM+ZUBkIGEs1QRNRYIeGB9GB9YsS8U2-Z3uunZPgnA5pF+E8BRwYz9ZE--VFeKCPamspG7tdvjA3AJNRNrCVmJvwq5SqgEQwINdcmwwjmc4JetVK76og5A5sPOIXSwOjlYK+Sm8rvlJZoxh0XFfyioHz48JV3vXbBKjgAlPAc7Npn+wk
```
<img src="asserts/01.png" alt="image-20240902170702727" style="zoom:50%;" /> 

## 生成注册密钥

```shell
git clone https://github.com/garfield-ts/BCompare_Keygen.git
cd BCompare_Keygen
pip3 install -r requirements.txt
# 对于 Python 3.7 及更早版本，需要手动安装 typing_extensions 模块
pip3 install typing_extensions==4.7.1
```
### 基于 Web 页面生成注册密钥
```shell
python3 app.py
```
<img src="./asserts/08.png" alt="image-20250707160150740" /> 

启动服务后访问 http://localhost:8000/ 即可看到相应页面，该页面由 AI 自动生成。

<img src="./asserts/09.png" alt="image-20250707160652595" style="zoom:67%;" /> 

点击 `生成密钥` 即可按照填写的参数生成注册密钥，点击 `复制` 按钮可将生成的密钥复制到剪贴板中。

<img src="./asserts/10.png" alt="image-20250707160933288" style="zoom:67%;" /> 

在页面底部还会展示注册密钥对应的详细参数，供研究学习使用。

<img src="./asserts/11.png" alt="image-20250707161229638" style="zoom:67%;" /> 

### 基于命令行生成注册密钥

```shell
python3 keygen.py
```
得到可用的注册密钥：
```
--- BEGIN LICENSE KEY ---
7uo7UY8gVANuMyCkDtSZRnNBkDXr1o4msYwtu7GFPaZ9B6naWXfsqEBgD5hM8jm3Sw2L4oFHY53VchaHv4j3q4QNiNxPgcv3qz89nKu3VSgQDVpPrAUWKgkjko5Gvck7BBBJmnKbGZJtDTi21WnJ5AMm7upD6QXgbf2BUS7toxB7jzhFLyotDj59KMGkgXMBXeUoa6T7Yt76MZN6UcHqYG5fMLuBp1JfGxpMXE7AMeUXXLwvAxsJGMkC5oS93WoVLopUoBW4SYNpS7YzzirkqZdRt58TbQpqcvwFeD32X2ZamVAv9SjeQUQhyEwktExFwTc541HrJeDV2xqfr4EgbUprSWEu8p
--- END LICENSE KEY -----
```
默认生成的注册密钥使用以下信息：
```
Version: 0x3d
Serial: Abcd-Efgh
Username: Test
Company: Home
Max users: 1
```
可以通过传入相关参数，自定义注册密钥的信息

<img src="asserts/06.png" alt="image-20240903162908919" style="zoom:50%;" /> 

## 使用密钥进行注册
打开 Beyond Compare 5，此时会弹出 `评估模式错误` 的提示，点击 `输入密钥` 按钮进入注册页面：

<img src="asserts/03.png" alt="image-20240902172200651" style="zoom:50%;" /> 

将脚本生成的注册密钥粘贴到输入框中，点击 `确定` 即可激活。

<img src="asserts/04.png" alt="image-20240902172404873" style="zoom:40%;" /> 

<img src="asserts/05.png" alt="image-20240902172829613" style="zoom:50%;" /> 

## 注意事项

1. RSA 密钥位置：
   - `macOS`：`/Applications/Beyond Compare.app/Contents/MacOS/BCompare`
   - `Windows`：`BCompare.exe`

2. **macOS 当前版本是 Universal Binary（x86_64 + arm64）**，整个文件里能搜到两处 `p1+wk`，但**那不是同一份密钥重复两次**，而是两个架构 slice 各自持有一份。
   - **Intel Mac**：要改的是第一处（地址较小，在 x86_64 slice 内）
   - **Apple Silicon**：要改的是第二处（地址较大，在 arm64 slice 内）
   - 旧文档「修改第二处」的说法仅在 Intel 单架构时代成立，新版 universal binary 上对 Intel Mac 是错的。**最稳妥的做法是两处都改**（用本仓库的 `patch_macos.py` 自动处理）。

3. **macOS 必须重新签名**。修改密钥字节后代码签名失效，Apple Silicon 直接拒绝执行；Intel 则可能在「无法验证开发者」的弹窗里点「仍要打开」后跑起来，但首次注册可能也会被 AMFI 拦。统一处理方法：
   ```bash
   xattr -d com.apple.FinderInfo "/path/to/Beyond Compare.app"
   xattr -d com.apple.FinderInfo "/path/to/Beyond Compare.app/Contents/PlugIns/BCFinder.appex"
   xattr -d com.apple.FinderInfo "/path/to/Beyond Compare.app/Contents/Frameworks/LetsMove.framework"
   codesign --force --deep --sign - "/path/to/Beyond Compare.app"
   ```
   注：`xattr -cr` 在新版 macOS 上对 `.appex` / `.framework` 静默失败，必须按上面这样精准定位 `com.apple.FinderInfo`。

4. **macOS Ventura+ 的 App Management 保护**：终端进程默认无权直接修改 `/Applications` 里的 `.app`，会报 `Operation not permitted`。绕过方法：
   - 用 Finder 操作（Finder 自动持有 App Management 权限），或
   - 在 `~/Desktop` 等其它目录上完成 patch + 重签，再用 Finder 拖回 `/Applications`。

5. SIP 不是必须关。早期 macOS 上确实需要关闭 SIP，否则 patched 二进制会被「**“Beyond Compare” 意外退出**」干掉（详见 [少数派文章](https://sspai.com/post/55066)）。但在新版 macOS（Sonoma 起）上，按上面第 3 步重签后，SIP 开着也能正常运行。如果遇到启动闪退，再考虑关 SIP。

6. `Windows` 版只有 1 处密钥，直接改即可，不涉及上述 macOS 特有的签名/权限问题。

   <img src="asserts/07.png" alt="image-20250707104436903" style="zoom:100%;" /> 

## macOS 一键脚本

```shell
python3 patch_macos.py
```

脚本流程：
1. 把 `/Applications/Beyond Compare.app` 拷贝到 `~/Desktop/`（避开 App Management）
2. 在桌面副本里把所有 `p1+wk` 替换为 `pn+wk`（同时覆盖 x86_64 和 arm64 两个 slice）
3. 清理 `com.apple.FinderInfo` 后做 ad-hoc 重签
4. 提示你用 Finder 把桌面那份拖回 `/Applications` 替换原版

之后第一次启动时右键「打开」一次（或在「系统设置 → 隐私与安全性」点「仍要打开」），即可使用 keygen 生成的密钥注册。

## TODO

- Windows 版 patch 自动化
- ……
