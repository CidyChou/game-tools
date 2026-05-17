# Tailwind Guidelines

本项目当前是静态 HTML + Tailwind Play CDN。页面可以继续零构建运行，但所有新增 UI 都应遵守这份约定，避免把一次性 class 写成互相冲突的视觉系统。

参考资料：
- Tailwind Play CDN: https://tailwindcss.com/docs/installation/play-cdn
- Tailwind theme variables: https://tailwindcss.com/docs/theme

## 使用方式

- 当前入口是 `web_static/index.html`，通过 `<script src="https://cdn.tailwindcss.com"></script>` 使用 Tailwind。
- Play CDN 适合本地工具台和快速迭代；如果页面变复杂或要发布到生产环境，迁移到 Tailwind CLI/Vite 构建流程。
- 主题扩展先放在页面内的 `tailwind = { theme: { extend: ... } }`；迁移构建流程时，再移动到正式配置或 CSS `@theme`。

## 颜色 Token

使用语义颜色，不在组件里随意增加新的主色。

- `surface`: `bg-white`, `bg-slate-50`, `bg-slate-100`
- `border`: `border-slate-200`, 强调边框用 `border-indigo-300`
- `text`: `text-slate-950`, 次级文本用 `text-slate-600`, 辅助文本用 `text-slate-500`
- `primary`: `bg-indigo-600`, hover 用 `hover:bg-indigo-700`, 弱背景用 `bg-indigo-50`
- `success`: `text-emerald-700`
- `danger`: `text-red-600`
- `focus`: `focus:outline focus:outline-4 focus:outline-indigo-100` 或 `focus:ring-4 focus:ring-indigo-100`

## 组件约定

- 页面容器：`mx-auto w-full max-w-7xl px-4 sm:px-6 lg:px-8`
- 工具区：白底、细边框、轻阴影，优先 `rounded-lg border border-slate-200 bg-white shadow-sm`。
- 预览面板：内部画布/图片区使用 `bg-slate-100`，外层仍保持白底工具卡。
- 表单控件：最小高度 `min-h-11`，可读标签必须常驻显示，不只依赖 placeholder。
- 主按钮：`bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-50`。
- 次级按钮/下载链接：`border border-slate-200 bg-white text-slate-700`，disabled 使用 `cursor-not-allowed text-slate-400`。
- Drop zone：`border-2 border-dashed border-slate-300 bg-slate-50`，hover/drag 状态只强化边框和背景，不缩放布局。
- 状态标签：`rounded-full border border-indigo-200 bg-indigo-50 text-indigo-700`。
- 导航项：使用 `data-nav-link` 和 `aria-current="true"` 表示当前工具区。

## 布局约定

- 主页面保持单页锚点结构，不引入路由。
- Sticky 导航位于顶部，工具区使用 `.tool-section` 设置 `scroll-margin-top`，防止跳转后标题被遮挡。
- 移动端导航允许横向滚动，不换行挤压按钮文字。
- 工具区之间使用 `gap-6`；复杂双栏工具在 `lg` 或 `xl` 后再展开。
- 固定格式元素如 canvas、预览区、按钮组必须有稳定尺寸或 `min-h-*`，避免内容加载后跳动。

## 交互与无障碍

- 所有按钮、链接、上传区域保持至少 44px 高度。
- 不移除 focus 样式；新增交互元素必须有可见 focus ring。
- 颜色不能作为唯一反馈，状态文案仍通过 `role="status"` 区域输出。
- 动画只用于状态反馈，持续时间控制在 `duration-200` 左右。
- 尊重 `prefers-reduced-motion`；平滑滚动和非必要动效要能关闭。

## 后续迁移建议

如果未来从 Play CDN 迁移到构建式 Tailwind：

- 将字体、颜色、阴影、圆角等设计 token 移到 Tailwind 配置或 v4 `@theme`。
- 把重复组件 class 收敛到模板片段或小型组件，不在页面里继续复制长 class。
- 保留本文件作为设计规范，配置文件只负责机器可读 token。
