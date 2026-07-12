# 图形反馈试验场

这套流程使用固定随机种子生成的合成数据测试绘图功能。合成数据不能作为研究结果或实验依据。

## 构建与浏览

```bash
../.venv/bin/python scripts/build_demo_gallery.py
open demo-gallery/index.html
```

构建会重新生成 `demo-gallery/`，其中包含 8 组 CSV、对应 YAML、PDF、SVG、600 dpi PNG、QA 和 provenance 文件。所有图必须通过现有 QA 才会进入画廊。

## 反馈格式

浏览 `demo-gallery/index.html` 后，按稳定编号反馈，例如：

```text
F02 两条线颜色太接近，图例希望放右边。
F04 原始点太密，均值和 CI 不够突出。
F07 横轴文字离图太远。
全局：字号增大一级，PNG 不要透明背景。
```

收到反馈后，修改 `scripts/render_figure.py`，再次运行同一个构建命令。数据和随机种子保持不变，因此前后变化可归因于渲染功能修改。

## 编号覆盖范围

| 编号 | 图形 | 主要测试点 |
| --- | --- | --- |
| F01 | scatter | 连续变量、离群值、中英混排单位 |
| F02 | line | 双组剂量响应、图例、科学单位 |
| F03 | line | 三组中文时间序列、紧凑布局 |
| F04 | point_summary | 原始点、均值、bootstrap CI、分组错位 |
| F05 | box | 偏态和离群值 |
| F06 | violin | 双峰分布和分布形状 |
| F07 | point_summary | 纯中文、缺失值、窄图 |
| F08 | point_summary | 五组颜色和右侧图例压力测试 |
