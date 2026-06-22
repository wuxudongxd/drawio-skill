# 上传到学城（km.sankuai.com / citadel）的渲染差异与验证

当图要通过 **citadel skill 的 `uploadDrawioToDocument`** 插入学城文档时，**学城内嵌的 drawio 渲染器与本地 draw.io 桌面版有几处硬差异**。本地预览正常 ≠ 学城正常，本地预览绝不能当作学城渲染的验证证据。

## 三个必避的渲染坑（本地看不出，学城才暴露）

1. **不支持 HTML 标签。** `html=1` 配合 `<b>` / `<span style=…>` / `<br>` 在本地渲染正常，上传学城后会**原样显示为文字**（如 `<b style=`）。
   → 用 drawio 原生样式属性：加粗 `fontStyle=1`（2=斜体、4=下划线，可叠加）、`fontSize=14`、`fontColor=#333333`。

2. **不认 `&#xa;` 换行。** 本地认（所以本地预览看着是多行、没问题），学城把带 `&#xa;` 的标签当**单行**渲染——文本超出框宽就溢出、被边缘裁掉（典型：「改造后（FCP 自关）」在 110px 框被裁成「女造后」）。
   → 标签写**单行**；放不下就**加宽 `width`**（必要时把整组元素右移、给标签列腾出宽度）。**不要靠缩 `fontSize` 硬塞**——会让该标签比其它字明显小、显挤、不一致。

3. **`text;` 单元格默认白底黑框。** 纯文字标题/注释/轴标签用 `style="text;html=1;…"` 时，本地默认透明无边（预览看不到框），但学城 mxgraph→SVG 会渲染成 `fill=white + stroke=black` 的方框，把标题、注释统统套上黑框。
   → text 单元格必须显式 `fillColor=none;strokeColor=none;`，例：`style="text;html=1;fillColor=none;strokeColor=none;align=left;…"`。需要边框的色块/表头格子则各自保留 `fillColor`/`strokeColor`。

## 验证闭环（必做，不要拿本地 draw.io 当证据）

1. `oa-skills citadel fetchDrawio --mis <mis> --drawioUrl "<上传返回的 CDN url>" --save /tmp/x.svg` —— 拿**学城服务端生成的真 SVG**（即学城实际渲染物）。
2. 用 **Chrome headless**（浏览器内核，与学城同源、整幅不裁）渲染为 PNG 再肉眼核对：
   ```bash
   "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new --disable-gpu \
     --force-device-scale-factor=2 --window-size=<W+20>,<H+20> --default-background-color=FFFFFFFF \
     --screenshot=/tmp/x.png "file:///tmp/x.svg"
   ```
   图过大读不了（如 >2000px）就 `sips -Z 1800 x.png --out x-s.png` 缩一下。
3. 结构可直接 grep SVG 佐证：带描边的 `<rect stroke="rgb(0, 0, 0)">` 数应等于"有意要框的格子数"，多出来的就是误框；文本单元格应为 `fill="none" stroke="none"`。
4. **`qlmanage -t` 会把宽图裁成近方形、丢右侧内容，别用它当完整验证**；没有 rsvg/cairosvg 时统一用 Chrome headless。

## 上传与改图格式

- `uploadDrawioToDocument --file` 只接受**纯 `<mxCell>` 列表**（不含 `<mxfile>`/`<mxGraphModel>`/`<root>` 外层与 `id=0`/`id=1`），外层由工具自动补。
- 改已有图：先 `fetchDrawio` 取 `mxGraphXml` → 改 mxCell → 重新 `uploadDrawioToDocument` → 把文档里旧的 `:::drawio{src=…}:::` 的 src 换成新附件 URL → `updateDocumentByMd` 回传 → 再拉一次确认 src 已更新。
