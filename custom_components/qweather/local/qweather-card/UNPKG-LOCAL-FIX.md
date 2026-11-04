# unpkg 依赖本地化修复（中国网络环境）

## 问题

`local/qweather-card/qweather-more-info.js` 原版写死：

```js
import { LitElement, html, css } from "https://unpkg.com/lit-element@2.0.1/lit-element.js?module";
```

国内网络环境下 unpkg.com 不可靠（HTTP3/QUIC 超时、被墙风险），页面每次加载都会串行请求 26 个外网文件，拖慢整个 HA 前端。

## 修复

- 把 lit-element 2.0.1 + lit-html 1.4.1 的全部依赖（17 个文件）下载到 `vendor/` 目录
- 所有 import 改写为相对路径（不再访问任何外网 CDN）
- `qweather-more-info.js` 的 import 改为 `./vendor/lit-element.js`

```
local/qweather-card/
├── qweather-card.js
├── qweather-more-info.js      # import 改为 ./vendor/lit-element.js
└── vendor/
    ├── lit-element.js
    ├── lib/                   # updating-element / decorators / css-tag
    └── lit-html/
        ├── lit-html.js
        └── lib/               # 14 个文件
```

## 验证

Playwright 实测：修复前 26 个 unpkg.com 外网请求（全部 ERR_TIMED_OUT），修复后归零，无失败请求，qweather 卡片正常加载。

## 建议

上游（dscao/qweather）应把依赖打包进组件，HA 前端卡片不应依赖运行时 CDN。
