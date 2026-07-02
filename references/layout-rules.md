# 布局规则 Checklist（生成 XML 前必读）

生成任何 .drawio 图之前，逐条对照。这 7 条规则解决了 90% 的出图质量问题。

## 1. 图例必须有

每张图必须有一个 `图例` 区域（swimlane 容器），**三项缺一不可**：
1. 颜色块 + 含义（如 `蓝=订单` `红=异常`）
2. 线型示例（绿色实线箭头 + 文字"正常路径"，红色虚线箭头 + 文字"异常路径"）
3. 特殊符号（菱形=判断，Fork/Join bar，UML Start/End）

validate.py 检测图例是否存在，但**不检测内容完整性**——你必须自查。

## 2. 颜色按功能域分配

5 个以上节点的图必须用 3 种以上 fillColor。每个功能域一个色系：
- 蓝 (#dae8fc) 橙 (#ffe6cc) 紫 (#e1d5e7) 绿 (#d5e8d4) 红 (#f8cecc) 黄 (#fff2cc)

正常路径绿色实线，异常路径红色虚线。不要全黑。

## 3. 多终止节点

每个终端状态（已完成/已取消/已退款等）就近放一个独立 End 节点。**禁止**所有路径汇聚到一个 End。

## 4. 节点位置决定线的质量

先摆节点，后连线。如果一条线需要穿越半张图，说明**节点位置有问题**——重排节点让这条线变短。不要用 waypoint 绕路来修复烂布局。

具体策略：
- TB 布局：主干节点中心 x 对齐，异常节点放两侧
- LR 布局：主干节点中心 y 对齐
- DFD/ER：高关联度的节点放近，外部实体可画副本避免长连线
- Fork/Join：两侧深度差 ≤2 层
- **共享终态**：如果多个节点都指向同一个终态（如"退款中"），把终态放在**最多指向源的附近**，而不是放在图的最底部
- **多边同入一节点**：当 2+ 条边指向同一个节点时，**每条边必须用不同的 entryX/entryY**（如 entryX=0 从左进、entryX=0.5 从上进、entryY=1 从下进），不能都挤在同一个入口点——否则箭头重叠无法区分

## 5. 紧凑间距

节点之间的垂直间距控制在 **50-70px**（节点底边到下一节点顶边）。不要留大片空白。

**目标高度 = 节点数 × 100px**（14 节点 → ≤1400px 坐标空间）。超过此值 2 倍说明间距过大，检查并收紧。**绝不能为了控制高度而删减业务节点**——prompt 要求的所有状态/步骤必须全部保留。

Fork/Join bar 的宽度只需覆盖两侧分支即可，不要比分支区域宽太多。

## 6. 菱形出口不要 orthogonalEdgeStyle

菱形水平出口（exitX=0 或 1）的连线用直连样式，不要 `edgeStyle=orthogonalEdgeStyle`——会产生弯折。垂直出口可以用。

## 7. 语言和符号

- 标签语言跟随 prompt 语言（中文 prompt = 中文标签）
- UML Start = 实心黑圆（无文字）：`style="ellipse;fillColor=#000000;strokeColor=#000000;aspect=fixed;" width="36" height="36"`
- UML End = 靶心圆（无文字）：外圈 `style="ellipse;fillColor=#FFFFFF;strokeColor=#000000;strokeWidth=3;aspect=fixed;" width="40" height="40"` + 内圈 `style="ellipse;fillColor=#000000;strokeColor=#000000;aspect=fixed;" width="24" height="24"`（居中嵌套）
- 节点只写核心名称，不加副标题
- ER/表格**禁止** `shape=tableRow`，用 `swimlane+stackLayout+text` 子元素
- `id="join"` 是 draw.io 保留字，会导致导出失败

---

详细几何规则（waypoint 对齐、泳道 padding、级联更新等）见 `references/pitfalls.md`。
