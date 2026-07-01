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

**陷阱**:能画直线的地方出现了多余弯折(orthogonalEdgeStyle 自动路由导致)。

**解法**:精确计算 exit/entry 的绝对 x 或 y,确保对齐。如果两端 x 差值 < 1px,线就是直的;差值大了就会产生水平弯折段。能直的线绝不弯折。

**对齐公式**:当 source 节点中心 x 与 target 泳道中心 x 不匹配时:
```
exit_abs_x = source_swimlane.x + node.x + node.width * exitX
entryX = (exit_abs_x - target.x) / target.width
```
同理,如果节点位置导致出口偏移,也可以反向调整节点 x 使其中心对齐。

**陷阱**:waypoint 与 pinned entry 的坐标不一致产生死折。例如 waypoint x=560 但 entry 绝对 x=600,渲染出一个 40px 的无意义拐角。垂直进入时 `waypoint.x === entry_abs_x`,水平进入时 `waypoint.y === entry_abs_y`,必须逐条用算式核对,不能目测。

**陷阱**:走廊绕行(corridor routing)时,最后一个 waypoint 离 target 边缘太近,箭头压在弯角上。例如 waypoint y=980 而 target 底边 y=970,stub 只有 10px(规则要求 ≥20px)。

**解法**:绕行路由写完后逐条验证 `abs(last_waypoint - target_edge) >= 20`,不足就把 waypoint 往走廊深处移。

**陷阱**:主路径(高视觉权重的边)出现 dogleg,因为 source 中心与 target 入口没有对上。

**解法**:优先移动节点让最重要的边走直线(如把 WAF 整体右移 100px,让移动端主路径垂直直落),次要边才接受 Z 形绕行。"能直则直"的优先级按边的视觉权重排序。

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

**间距(呼吸感)**:
- 泳道间 gap:60px(全图统一,不能有的紧有的松)
- 节点间 gap:24-26px
- 节点内 padding:spacingLeft=14, spacingTop=12

**一致性**:
- 同层级节点宽度一致,高度尽量一致
- 箭头统一 `endArrow=classic;endFill=1`
- 不用虚线(除非有明确语义)
- 所有节点用 `html=1` + `absoluteArcSize=1;arcSize=8`

**内容准确**:
- 外部依赖只放 package.json / CDN 引入的直接依赖,间接依赖用详情文字描述,不单独开节点
- 信息量少的节点(≤2行)不需要标题/详情分层,加粗分色反而增加噪音

## 六、元素与边框间距

**陷阱**:节点到泳道边框的上下 padding 不一致 — 上面紧贴标题栏,下面大片空白,或反过来。

**解法**:
- 标准值: **上下各 16px**
- 计算: `上padding = 首节点.y - startSize`, `下padding = 泳道.height - (末节点.y + 末节点.height)`
- 上下 padding 差值控制在 **4px 以内**
- **用验证脚本逐个泳道检查**,不能靠肉眼或猜测
- **算完必须导出 PNG 看图确认** — drawio 内部坐标和渲染结果可能有偏差

**泳道间距**:泳道与泳道之间的 gap 必须全图一致(标准值 **60px**)。用脚本验证: `gap = 下一泳道.y - (上一泳道.y + 上一泳道.height)`

**验证脚本模板**:
```python
top_pad = first_node_y - startSize
bottom_pad = swimlane_height - (last_node_y + last_node_height)
gap = next_swimlane_y - (current_swimlane_y + current_swimlane_height)
assert abs(top_pad - bottom_pad) <= 4, f"padding 不一致: top={top_pad}, bottom={bottom_pad}"
assert gap == 60, f"gap 不一致: {gap}"
```

## 七、颜色规则

**线条一律黑色** — 不加 `strokeColor` 即可,默认黑色。线本身不承载语义区分,节点填充色和标签文字色才承载。

**标签文字跟随链路色** — 例如 Webmake 链路的标签文字用绿色 (#82b366),Magpie 链路用紫色 (#9673a6),与图例中对应色系保持一致。

**全图一致性** — 同一语义的标签,无论出现在哪个 gap 或哪条 edge 上,必须使用相同颜色。不能上面用了绿色,下面同名标签却变成黑色。

**图例必须建立并严格遵守** — 每种填充色对应一个语义角色,不随意分配。

**判断前先自问** — "这个颜色有依据吗？和图例一致吗？全图统一了吗？" 不要凭感觉随意分配。

## 八、文字与标签背景

**陷阱 (z-order)**:draw.io 按 XML 文档顺序渲染——后定义的元素画在上层。如果独立标签(text 元素)定义在 edge 之前,edge 的线条会画在标签上方,即使标签有 `fillColor` 也会被线穿透。

**解法**:gap 中需要覆盖线条的标签,**不要用独立 text 元素**,直接把文字放在 edge 的 `value` 属性上,配合 `labelBackgroundColor=#ffffff`:
```xml
<mxCell id="e_xxx" value="标签文字" style="...endArrow=classic;endFill=1;fontSize=11;fontStyle=1;fontColor=#xxx;labelBackgroundColor=#ffffff;" .../>
```
这样标签由 edge 自身渲染,保证背景在线条之上。

**陷阱 (`text` 形状)**:`text` 形状的 `fillColor` 在某些导出模式/渲染器下不渲染为实心背景。

**解法**:如果必须用独立元素(不能放在 edge value 上),用标准矩形替代 `text` 形状,并确保在 XML 中定义在相关 edge 之后:
```
style="rounded=0;whiteSpace=wrap;html=1;fontSize=11;fontStyle=1;fontColor=#xxx;align=center;verticalAlign=middle;fillColor=#ffffff;strokeColor=none;"
```

**Gap 区标签定位**:标签放在 gap 中点(y = gap_mid - label_height/2),确保白底完全覆盖线条。

## 八½、边标签冗余判断

**原则**:当目标节点标题已包含分支语义时,edge 上的标签是冗余的,应该去掉。

**需要边标签的场景**:
- 条件分支(yes/no、成功/失败)
- 连接语义不能从两端节点名推断
- 多条边从同一节点出发,需要区分用途

**不需要边标签的场景**:
- 目标节点标题已经写了分支名称(如 "Magpie: emit before-render")
- 只有一条入边,连接语义显而易见

**判断方法**:遮住边标签,只看源节点和目标节点——如果仍然能理解分支语义,标签就是冗余的。

## 九、改动后全局级联检查

**陷阱**:改了一个泳道的 y 或 height 后,只更新了该泳道内部元素,忽略了所有依赖绝对坐标的外部元素,导致标签错位、线条偏移。

**必须同步更新的元素清单**:
1. **下游泳道 y** — 逐个向下级联: `next.y = current.y + current.height + gap`
2. **gap 中的独立标签** (parent="1") — y = 新 gap 中点 - label_height/2
3. **gap 中的 waypoints** — mxPoint 的 y 值需要更新到新 gap 区域
4. **Fieldset Legend 标签** (parent="1") — y = 新 build_box_abs_top - label_height/2
5. **跨泳道 edge 的 entry/exit 比例** — 如果目标泳道尺寸变了,entryX/entryY 比例可能需要重算
6. **pageHeight / dy** — 整体画布可能需要调大

**检查顺序**:
```
改泳道 y/h → 级联更新下游泳道 y → 重算 gap 中标签 y → 重算 waypoint y → 重算 legend y → 导出 PNG → 逐区域验证
```

## 九½、竖排泳道标题

**陷阱**:`swimlane;horizontal=0;` 的标题竖排在 30px 侧条里,字数受泳道高度限制。"业务服务层 · 事件总线居中" 这类带说明的长标题会挤压变形。

**解法**:泳道标签只写层名(如"业务服务层"),设计说明放图外文字或副标题,不塞进泳道标签。

## 十、布局设计（生成 XML 前必须遵守）

以下规则从大量失败案例中提炼，**在规划节点位置和连线之前**就要决定好，不是事后修补能解决的。

### 10.1 多终止节点

**硬性规则**：当多条路径（正常完成、已退款、已取消等）最终都要到达终止符号时，**每个终端状态就近放一个独立的 End 节点**。禁止所有路径汇聚到一个 End——这是长距离路由和边穿越的第一大来源。

```
✗ 错误：已完成 ──长线──→ End ←──长线── 已退款 ←──更长线── 已取消
✓ 正确：已完成 → End₁    已退款 → End₂    已取消 → End₃
```

### 10.2 异常节点位置

**硬性规则**：异常/终止状态（已取消、商家拒单、退款中、已退款）放在主干的**外侧**（左边缘或右边缘），永远不要放在主干脊柱上。异常节点应尽量靠近触发它的判断节点：

```
✗ 错误：商家拒单放在图底部（离商家审核很远）
✓ 正确：商家拒单放在商家审核的同一行或下一行，水平偏移到侧面
```

### 10.3 异常路径走廊

所有异常路径的连线走同一条**外围走廊**（图的最右侧或最左侧的固定 x 值）。走廊 x 值必须在所有节点 bbox 的外面，不能穿过任何节点。多条异常路径共享走廊时，用同一个 x 值避免交叉。

### 10.4 主干脊柱

TB 布局中，正常路径的主干应该是一条从上到下的**直线**（所有主干节点中心 x 对齐）。分支从主干**水平伸出**，不要打断主干的垂直连续性。

### 10.5 Fork/Join 平衡

Fork 的两侧分支**深度差不超过 2 层**。如果一侧有 5 个节点而另一侧只有 2 个，要么调整 Fork 的位置（把一些节点移到 Fork 之前），要么在短侧增加中间状态。不平衡的分支导致长距离路由。

### 10.6 颜色按功能域分配

同一功能域用同一色系，不同域用不同色系。常用分配：
- 蓝色 (#dae8fc/#6c8ebf)：订单相关（待支付、已支付）
- 橙色 (#ffe6cc/#d79b00)：商家相关（通知商家、商家接单、备餐中、待取餐）
- 紫色 (#e1d5e7/#9673a6)：配送相关（分配配送员、配送员接单、取餐中、配送中、已送达）
- 绿色 (#d5e8d4/#82b366)：完成状态（已完成）
- 红色 (#f8cecc/#b85450)：异常状态（已取消、商家拒单、退款中、已退款）
- 黄色 (#fff2cc/#d6b656)：判断节点

**禁止所有正常节点用同一个颜色。**

### 10.7 Fork/Join 拓扑设计

**硬性规则**：Fork bar 的两侧必须有**真正独立并行的节点**，不能是顺序依赖的。放了 Fork bar 就必须有对应的 Join bar，中间是两条独立路径。

```
✗ 错误：Fork → A → B → C → D → E（全部串行，Fork 是摆设）
✓ 正确：Fork → [左: A → B] + [右: C → D] → Join → E
```

**设计原则**：
- Fork 的位置选择要让两侧深度接近（差不超过 2 层）
- 如果某个业务流程是纯顺序的（无并行），不要强加 Fork/Join
- Fork 前的节点应该是触发并行的决策点（如"商家接单后同时备餐和分配配送员"）

### 10.8 ER 图 / 表格类图表

**禁止使用 `shape=table` + `shape=tableRow`** — draw.io CLI 导出时 `tableRow;horizontal=0` 会把文字渲染成竖排乱码。**必须用 swimlane + stackLayout + text 子元素**：

```xml
<!-- 正确：swimlane 容器 + text 子元素 -->
<mxCell id="t" value="TableName" style="swimlane;fontStyle=1;childLayout=stackLayout;
  horizontal=1;startSize=26;fillColor=#6c8ebf;strokeColor=#6c8ebf;fontColor=#ffffff;
  fontSize=13;html=1;collapsible=0;whiteSpace=wrap;" vertex="1" parent="1">
  <mxGeometry x="40" y="40" width="200" height="122" as="geometry" />
</mxCell>
<mxCell id="f1" value="PK  id  BIGINT" style="text;strokeColor=#6c8ebf;fillColor=#dae8fc;
  align=left;verticalAlign=middle;spacingLeft=8;overflow=hidden;rotatable=0;
  whiteSpace=wrap;html=1;fontStyle=1;fontSize=11;" vertex="1" parent="t">
  <mxGeometry y="26" width="200" height="24" as="geometry" />
</mxCell>
```

**表格宽度**：`width = max(字段名字符数) × 8 + 60`，最小 200px。

**字段数** ≤ 8，超出用省略行。**字号**：表头 13px bold，字段 11px。**表间距**：水平 ≥ 80px，垂直 ≥ 60px。

**PK 行**用 `fontStyle=1`（粗体）+ 浅色填充背景。**FK 行**用 `fontStyle=2`（斜体）。

**禁止 `overflow=hidden`** — 这个属性会硬截文字而不是换行，导致最后几个字符消失。用 `overflow=visible` 或不写 overflow。UML 类图的属性/方法行同理。

### 10.9 菱形（rhombus）出口连线

**硬性规则**：菱形节点水平方向出口（exitX=0 或 exitX=1）的连线，**禁止使用 `edgeStyle=orthogonalEdgeStyle`**。orthogonal 路由在菱形的对角边缘会产生可见的 jog（小弯折）。

```
✗ 错误：style="edgeStyle=orthogonalEdgeStyle;...exitX=1;exitY=0.5;..."
✓ 正确：style="rounded=1;html=1;...exitX=1;exitY=0.5;..."（直连，无 orthogonal）
```

菱形垂直方向出口（exitY=0 或 exitY=1）可以用 orthogonalEdgeStyle，因为垂直出口在菱形顶/底点，不会产生 jog。

## 十一、工作流程

1. **每次改动必须导出 PNG 并用 vision 看图验证** — 不能只看代码。drawio 内部坐标和实际渲染可能有偏差。
   - **全图缩略 vision 检查发现不了 <40px 级别的错位**(死折、5px 偏移、过短的箭头 stub)。复杂图必须二选一:(a) 用 PIL 裁剪 2-3 个关键区域放大后逐区 vision 检查;(b) 用脚本对每条 edge 断言 waypoint/entry/exit 坐标对齐。只看整图缩略等于没检查。
2. **全局看图,不只看局部** — 改了一处后,整张图从上到下扫一遍,检查是否引入新问题(标签错位、线偏移、间距变化)。
3. **一次修多个问题优于反复小改** — 避免改一处引发另一处回归。
4. **坐标计算要精确** — 泳道子元素用相对坐标,跨泳道连线/标签用绝对坐标。
5. **自己判断"可接受"无效** — 必须用户确认。
6. **用验证脚本量化检查** — padding、gap 等用脚本算出精确值,不靠肉眼估计。
7. **XML 编辑注意去重** — 避免产生 duplicate mxGeometry 等问题。
