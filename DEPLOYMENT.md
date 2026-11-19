# 部署记录

## 当前地址

- 活动页：https://demo.jevious.top/
- Vue 管理后台：https://demo.jevious.top/vue/
- 原生后台入口：https://demo.jevious.top/manage-7f3c9a2d
- 管理员账号：`admin`
- 管理员密码：部署时通过 `/etc/hulunbuir-quiz.env` 设置，不写入仓库
- 数据库：`/var/lib/hulunbuir-quiz/quiz.db`
- HTTPS：Let's Encrypt 证书，自动续期

## 服务器

- 公网 IP：`49.233.166.151`
- 系统：Ubuntu 24.04 LTS
- 规格：2 核 4G / 50GB SSD
- 部署密钥：本机私钥，不提交到仓库

## 运行架构

```text
浏览器 -> Nginx :443/HTTPS -> 127.0.0.1:8080 -> systemd 服务 hulunbuir-quiz -> SQLite
```

- 应用目录：`/opt/hulunbuir-quiz`
- Python 虚拟环境：`/opt/hulunbuir-quiz/.venv`
- 环境变量：`/etc/hulunbuir-quiz.env`
- systemd：`hulunbuir-quiz.service`
- Nginx 主站点：`/etc/nginx/sites-available/hulunbuir-quiz`
- Nginx 域名站点：`/etc/nginx/sites-available/hulunbuir-quiz-domain`
- 证书：`/etc/letsencrypt/live/demo.jevious.top/`
- 日志：`journalctl -u hulunbuir-quiz`

## 常用命令

```bash
sudo systemctl status hulunbuir-quiz nginx
sudo systemctl restart hulunbuir-quiz
sudo journalctl -u hulunbuir-quiz -f
curl http://127.0.0.1:8080/api/health
```

备份数据库：

```bash
sudo -u quiz /opt/hulunbuir-quiz/.venv/bin/python - <<'PY'
import sqlite3, datetime
src='/var/lib/hulunbuir-quiz/quiz.db'
dst='/var/lib/hulunbuir-quiz/backup-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S')+'.db'
s=sqlite3.connect(src); d=sqlite3.connect(dst); s.backup(d); d.close(); s.close()
print(dst)
PY
```

## 正式上线前

1. 将 `APP_MODE` 切换为 `production`。
2. 配置正式 `PUBLIC_URL`、公众号、商户和支付参数。
3. 在公众号后台配置网页授权域名、JS 接口安全域名和服务器 IP 白名单。
4. 在商户平台完成 APIv3 密钥、证书和商家转账场景配置。
5. 修改 `ADMIN_PASSWORD`，并轮换曾经出现在聊天或文档中的密钥。
6. 给后台增加 IP 白名单、VPN 或 WAF。
7. 完成微信 OAuth、关注校验、分享、红包和话费发放真机回归。
8. 完成小额真实支付、超时、失败、重复点击和每日对账验证。

## 当前限制

- 单实例 + SQLite，写操作串行；高并发场景建议迁移 PostgreSQL 和多实例。
- 后台没有额外双因素保护，依赖强密码和访问控制。
- 域名备案在阿里云、服务器在腾讯云，正式对外前需办理新增接入备案。
- Let's Encrypt 证书已自动续期，但存在续期验证节点不稳定风险，建议到期前 30 天人工检查。
- 话费奖励若第 50 名大量并列，会按并列同奖规则生成超过 50 份，需要单独设置预算上限。

## 更新代码

```bash
scp -i <部署私钥> server.py wechat_pay.py wechat_transfer.py ubuntu@49.233.166.151:/tmp/
scp -r -i <部署私钥> static ubuntu@49.233.166.151:/tmp/
scp -r -i <部署私钥> vue/dist ubuntu@49.233.166.151:/tmp/vue-dist
# 服务器上
sudo cp -a /tmp/server.py /tmp/wechat_pay.py /tmp/wechat_transfer.py /opt/hulunbuir-quiz/
sudo cp -a /tmp/static/. /opt/hulunbuir-quiz/static/
sudo rm -rf /opt/hulunbuir-quiz/static/vue
sudo cp -a /tmp/vue-dist /opt/hulunbuir-quiz/static/vue
sudo chown -R quiz:quiz /opt/hulunbuir-quiz
sudo systemctl restart hulunbuir-quiz
```

## 题库

- 已导入 53 题：单选 26、多选 27。
- 导入文件：`docs/题库导入_扫黑除恶_53题.xlsx`
- 解析报告：`docs/题库解析报告.md`
- 正式活动前请主办方复核题目与答案。

## 证书续期

- 证书自动续期已启用。
- 到期前至少 30 天手动检查。
- 如自动续期持续失败，可改用商业证书或 DNS-01 验证方式。

## 微信配置

- 后台左侧“微信配置”维护公众号、商户、APIv3 密钥、证书、转账场景和红包文案。
- 保存后立即生效，不需要重启服务。
- AppSecret 和商户密钥不回显，留空表示保持原值。
- 生产环境建议使用独立密钥管理并限制后台访问。

## 访问限制

- 活动首页 `/` 仅允许微信内置浏览器访问；电脑打开显示公众号二维码。
- 管理后台使用独立入口，电脑端可直接访问登录页。