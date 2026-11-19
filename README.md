# 呼伦贝尔市扫黑除恶有奖竞答系统

公众号 H5 移动端 + Vue 管理后台 + Python API + SQLite。

## 系统组成

```text
/                 原生 H5 移动端
/vue/             Vue 管理后台
/manage-7f3c9a2d  原生后台入口（备用）
```

- `server.py`：HTTP API、会话、答题、抽奖、发奖、后台任务。
- `static/`：原生 H5 页面、样式和脚本。
- `vue/`：Vue 3 + Vite 管理后台。
- `wechat_pay.py` / `wechat_transfer.py`：微信支付适配。
- `data/quiz.db`：运行数据库（首次启动生成，不提交）。

## 参与流程

1. 微信授权登录，校验公众号关注状态。
2. 阅读规则，开始一套 5 道单选 + 5 道多选题。
3. 单选每题 8 分，多选每题 12 分；多选全部选对才得分。
4. 达到配置分数可抽奖；未达标可按配置使用复活机会。
5. 抽奖奖品支持积分、微信红包和未中奖。
6. 活动结束后封榜，前 50 名按话费奖励档位发放。

积分规则：

- 每天取当天最高分。
- 跨天累加为累计积分。
- 同一天多套只计最高分，不重复累计。
- 抽奖积分另行累加。
- 榜单总用时按每天最高分对应套次的用时累加，显示为“X分XX秒”。

当前奖品只有积分、红包和未中奖，不包含实物邮寄或线下领取。

## 管理后台

Vue 管理后台：

```text
https://正式域名/vue/
```

支持：

- 运营概览
- 活动配置
- 题库管理（含 Excel 导入）
- 奖品管理（新增、编辑、启停、删除）
- 用户管理
- 记录与发奖
- 账号管理
- 微信配置
- 移动端页面文案

超级管理员可修改活动名称、预算、页面文案、微信配置和账号；运营账号只能做活动运营操作，服务端强制校验权限。

## 活动配置

支持配置：

- 活动时间、暂停状态
- 每日免费次数、复活次数、达标分数、限时
- 总预算、每日预算、单人每日/全程中奖上限
- 排行榜人数、评优人数
- 分享复活方式
- 评优说明
- 首页、规则、答题、结果、抽奖、榜单、获奖公示、我的奖品文案

文案留空会保持为空；需要恢复默认文案时重新填写默认内容。

## 微信与支付

后台“活动配置”可维护微信分享标题、分享描述和分享链接；分享链接留空时使用当前活动页。

后台“微信配置”维护：

- 公众号 AppID / AppSecret
- 商户号
- APIv3 密钥
- 商户证书、私钥
- 商家转账场景
- 红包文案
- 支付模式

生产模式要求：

```text
APP_MODE=production
ADMIN_PASSWORD=至少16字符强密码
PUBLIC_URL=https://正式域名
WECHAT_APP_ID=公众号AppID
WECHAT_APP_SECRET=公众号AppSecret
DATABASE_PATH=/data/quiz.db
```

生产环境必须使用 HTTPS，并在公众号后台配置网页授权域名、JS 接口安全域名和服务器 IP 白名单。

真实红包和话费发放前必须完成：

- 小额真实支付
- 用户确认收款
- 超时、失败、重复点击和回调验证
- 每日商户流水对账

## 部署

```text
浏览器 -> Nginx HTTPS -> 127.0.0.1:8080 -> systemd -> SQLite
```

应用目录：

```text
/opt/hulunbuir-quiz
```

常用命令：

```bash
sudo systemctl status hulunbuir-quiz nginx
sudo systemctl restart hulunbuir-quiz
sudo journalctl -u hulunbuir-quiz -f
curl http://127.0.0.1:8080/api/health
```

Vue 管理后台构建：

```bash
cd vue
pnpm install
pnpm build
```

构建产物部署到 `/opt/hulunbuir-quiz/static/vue`。

## 备份与监控

- 每日 03:00 自动备份 SQLite，保留 14 天。
- 备份目录：`/var/backups/hulunbuir-quiz`。
- 每 5 分钟检查应用、数据库和磁盘。
- 监控日志：`/var/lib/hulunbuir-quiz/monitor.log`。
- 建议配置异地加密备份和告警 Webhook。

详细命令见 `docs/运维手册.md`。

## 安全

- 管理员密码 PBKDF2-SHA256 哈希保存。
- 超级管理员/运营账号两级权限。
- HttpOnly、SameSite 会话 Cookie。
- Origin/CSRF 校验。
- 参数化 SQL。
- 上传文件类型、大小和文件头校验。
- 抽奖、预算、库存、发奖在事务内校验。
- 红包以订单号作为商户幂等键。
- 后台密钥不回显。

正式上线前应完成：

- 修改所有曾出现在聊天或文档中的密码和密钥。
- 后台增加 IP 白名单、VPN 或 WAF。
- 配置异地备份和异常告警。
- 完成微信 OAuth、分享、转账真机回归。
- 完成容量演练并准备降级开关。

## 目录

```text
server.py                 后端服务
static/                   原生 H5
vue/                      Vue 管理后台
scripts/                  备份、监控、运维脚本
docs/                     需求、部署、运维和安全文档
data/                     运行时数据库（不提交）
```