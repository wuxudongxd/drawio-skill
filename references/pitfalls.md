# draw.io 绘图陷阱与最佳实践

基于实战踩坑总结,绘制 draw.io 图时必须遵守。

## 一、圆角一致性

**陷阱**:`arcSize` 是 `min(width, height)` 的百分比,不是绝对像素值。相同 `arcSize=12`,70px 高的框圆角 8px,250px 高的框圆角 30px,视觉不一致。

**解法**:所有节点统一使用 `absoluteArcSize=1;arcSize=8`,确保不同大小的框圆角视觉一致。

**陷阱**:`html=1` 和非 `html=1` 节点对 `arcSize` 的渲染方式不同,即使数值相同也会产出不同视觉半径。

**解法**:所有节点统一使用 `html=1`,不要混用。

## 二、多行文字

**陷阱**:`whiteSpace=wrap` + `&#xa;` 换行 + `align=left` 三者同时使用时,文字被压缩成一行。

**解法**:
- 需要换行 + 主次分层 → 用 HTML value(`<br>` + `<b>` + `<span style='color:#666'>`) + `html=1`
- 需要换行 + 不需要分层 → 用纯文本 `&#xa;` + 不加 `html=1` + 不加 `whiteSpace=wrap`
- 绝不混用 `whiteSpace=wrap` 和 `&#xa;`

**最佳实践**:多文字节点用 HTML value 做主次分层:
- 标题:`<b style='font-size:13px'>标题</b>`
- 详情:`<span style='color:#666;font-size:11px'>详情</span>`
- 详情内折行按语义判断,不要机械化每行一个要点;步骤链/参数列表独立行,短描述可同行
- 信息量少的节点(≤2行)不需要分层,直接用普通文字

## 三、连线路由

**陷阱**:跨泳道连线必然穿过目标泳道的标题栏区域。

**解法**:
- 计算 entryX 使线避开标题文字(标题居中,线走两侧)
- 或 target 改为泳道本身(`target="s4"`)而非子节点
- 纯垂直线:确保最后一个 waypoint 的 x 与 entry 绝对 x 完全相同

**坐标计算公式**:
```
entry 绝对 x = 泳道.x + 节点.x + 节点.width × entryX
waypoint.x 必须 === entry 绝对 x (否则产生斜线)
waypoint.y 应在泳道间 gap 的中点 = (上段.bottom + 下段.top) / 2
```

**陷阱**:连线标签(value)可能遮盖节点或标题文字。

**解法**:标签放在线的空白段(gap 区),不要放在穿越元素的段上。

## 四、Fieldset Legend 标签

**陷阱**:泳道子元素(parent=swimlane)不能超出 startSize 标题栏区域,导致标签位置受限。

**解法**:
- 标签用 `parent="1"` 绝对定位
- y = 目标框绝对 top - 标签高度/2(骑在边框线上)
- `fillColor=#ffffff`(白底盖住边框线)
- `align=center;verticalAlign=middle`
- value 不加前后空格,靠 align=center 居中
- width 略大于文字宽度即可

## 五、视觉设计原则

**字体层次**:
- 泳道标题:15px bold
- 节点标题:13px bold(HTML `<b>`)
- 节点详情:11px 灰色(HTML `<span style='color:#666'>`)
- 连线标签:11px
- 图例:11px

**颜色规则**:建立图例并严格遵守,每种颜色对应一个语义角色,不随意分配。

**间距(呼吸感)**:
- 泳道间 gap:60-80px
- 节点间 gap:24-26px
- 节点内 padding:spacingLeft=14, spacingTop=12

**一致性**:
- 同层级节点宽度一致
- 箭头统一 `endArrow=classic;endFill=1`
- 不用虚线(除非有明确语义)
- 所有节点用 `html=1` + `absoluteArcSize=1;arcSize=8`

## 六、元素与边框间距

**陷阱**:节点到泳道边框的上下 padding 不一致 — 上面紧贴标题栏,下面大片空白,或反过来。

**解法**:
- 用脚本计算: `上padding = 首节点.y - startSize`, `下padding = 泳道.height - (末节点.y + 末节点.height)`
- 上下 padding 差值控制在 6px 以内
- 推荐值: 上下各 12-16px
- **算完必须导出 PNG 看图确认** — drawio 内部坐标和渲染结果可能有偏差

**泳道间距**:泳道与泳道之间的 gap 必须保持一致(推荐 50-60px),不能有的紧有的松。用脚本验证: `gap = 下一泳道.y - (上一泳道.y + 上一泳道.height)`

## 七、工作流程

1. **每次改动必须导出 PNG 并用 vision 看图验证** — 不能只看代码
2. 一次修多个问题优于反复小改(避免回归)
3. 坐标计算要精确 — 泳道子元素用相对坐标,跨泳道连线用绝对坐标
4. 自己判断"可接受"无效 — 必须用户确认
