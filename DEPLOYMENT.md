# 部署记录（腾讯云演示环境）

## 当前地址

- 活动页：https://demo.jevious.top/
- 管理后台：https://demo.jevious.top/manage-7f3c9a2d
- 管理员账号：`admin`
- 管理员密码：部署时通过 `/etc/hulunbuir-quiz.env` 设置，不写入仓库
- 运行模式：`demo`
- 数据库：`/var/lib/hulunbuir-quiz/quiz.db`
- 当前数据：已清空测试用户，无演示答题记录
- HTTPS：Let's Encrypt 证书，自动续期（certbot.timer，下一次 2026-11-17 05:21）

## 服务器

- 公网 IP：`49.233.166.151`
- 系统：Ubuntu 24.04 LTS
- 规格：2 核 4G / 50GB SSD
- 登录用户：`ubuntu`（可 sudo）
- SSH 端口：22
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
# 服务状态
sudo systemctl status hulunbuir-quiz nginx

# 重启应用
sudo systemctl restart hulunbuir-quiz

# 查看日志
sudo journalctl -u hulunbuir-quiz -f

# 检查本地健康
curl http://127.0.0.1:8080/api/health

# 备份数据库（SQLite 在线备份，不能直接复制正在写入的主文件）
sudo -u quiz /opt/hulunbuir-quiz/.venv/bin/python - <<'PY'
import sqlite3, datetime
src='/var/lib/hulunbuir-quiz/quiz.db'
dst='/var/lib/hulunbuir-quiz/backup-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S')+'.db'
s=sqlite3.connect(src); d=sqlite3.connect(dst); s.backup(d); d.close(); s.close()
print(dst)
PY
```

## 修改管理员密码

编辑 `/etc/hulunbuir-quiz.env` 中的 `ADMIN_PASSWORD`，然后：

```bash
sudo systemctl restart hulunbuir-quiz
```

不要把密码写进代码、聊天群或公开文档。

## 当前限制

1. 已启用 **HTTPS 域名 `demo.jevious.top`**；HTTP 自动跳转 HTTPS。
2. `APP_MODE=demo`，允许演示登录；正式活动需改为 `production`，配置微信 OAuth、商户支付。
3. 0.5 元现金红包是否可发、积分奖品是否占用中奖次数，仍需主办方/商户确认。
4. 当前是单实例 + SQLite；正式活动前需按 Q-09 规模做压测，若并发较高需迁移 PostgreSQL/多实例。
5. 后台没有额外的 IP 白名单或双因素保护，依赖管理员密码；正式上线前建议加 Cloudflare Access 或 Nginx IP 限制。
6. 域名备案在阿里云、服务器在腾讯云，正式对外前需在腾讯云办理 **新增接入备案**，避免备案接入不一致。
7. 微信公众号还需在后台配置：网页授权域名 `demo.jevious.top`、JS 接口安全域名 `demo.jevious.top`，并把公众号的 `MP_verify_*.txt` 校验文件放到服务器根目录。需要时把文件发我配置。
8. Let's Encrypt 证书已设置自动续期，但注册时未填写通知邮箱；如需到期提醒，提供一个能收信的邮箱后可补上。

## 更新代码

在本机项目目录上传新文件后：

```bash
scp -i <部署私钥> server.py wechat_pay.py ubuntu@49.233.166.151:/tmp/
scp -r -i <部署私钥> static ubuntu@49.233.166.151:/tmp/
# 服务器上
sudo cp -a /tmp/server.py /tmp/wechat_pay.py /opt/hulunbuir-quiz/
sudo cp -a /tmp/static/. /opt/hulunbuir-quiz/static/
sudo systemctl restart hulunbuir-quiz
```

## 题库

- 已导入《修改 扫黑除恶题库.docx》解析后的 53 题：单选 26、多选 27。
- 导入文件：docs/题库导入_扫黑除恶_53题.xlsx
- 解析报告：docs/题库解析报告.md
- 原 60 道演示题已从服务器题库删除；后台题库当前共 53 题。
- 答案按原 Word 标注提取，未自行改答案；正式活动前请主办方复核。

## 验收测试账号

- 后台 **用户管理 → 标记测试**，输入测试标记密码（由 `TEST_MARK_PASSWORD` 配置），即可把指定用户标记为测试账号。
- 标记后：不限答题次数、提交固定 100 分、抽奖个人次数放开；普通用户规则不变。
- 再次操作“取消测试”并输入密码，即可恢复普通用户。
- 密码可通过环境变量 `TEST_MARK_PASSWORD` 修改；生产环境应改成独立强密码。
- 测试账号的答题、抽奖、订单仍会正常写入数据库，测试结束可在后台查看或清理。

## 证书续期注意

- 证书当前有效至 2027-02-14，HTTPS 正常。
- Certbot 已配置自动续期，但续期演练时 Let's Encrypt 的次要验证节点对 `demo.jevious.top` 返回 DNS SERVFAIL；当前证书不受影响，但 90 天后自动续期存在失败风险。
- 证书通知邮箱已提交更新（不在仓库中记录具体地址），但 Let's Encrypt 账户接口目前仍显示无联系人；如必须依赖到期邮件，建议改用商业证书或更换 DNS 服务商后重新签发。
- 建议在到期前至少 30 天手动检查续期；可更换为 Cloudflare/Tencent DNSPod 解析，或提供阿里云 DNS API 凭据用 DNS-01 方式续期。

## 已确认事项（2026-11-16）

- 题库：锁定为当前导入的 53 题（单选 26、多选 27），不再使用演示题。
- 奖品：保持当前六类配置与前 50 名话费档位不变。
- 0.5 元现金红包：商户确认可发，正式联调时需做真实小额验证。
- 积分奖品：计入每日/全程中奖次数（当前系统口径）。
- 正式活动起止时间：未定，确定后更新配置。

## 微信配置入口

- 后台左侧 **微信配置**：维护公众号 AppID/AppSecret、商户号、商户 API 密钥、证书路径、支付模式和红包文案。
- 保存后立即生效，不需要重启服务；AppSecret/商户密钥不在页面回显，留空表示不修改。
- 环境变量仍作为兜底；生产环境建议使用独立密钥管理并限制后台访问。

## 访问限制

- 活动首页 `/` 仅允许微信内置浏览器访问；电脑浏览器打开会显示“请在微信中打开”和公众号二维码。
- 管理后台单独使用 `/manage-7f3c9a2d`，电脑端可直接访问登录。
