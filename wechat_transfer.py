"""微信支付 APIv3 商家转账（新版）适配器。

官方文档：/v3/fund-app/mch-transfer/transfer-bills
- 普通商户
- 商户 API 证书 + RSA-SHA256 签名
- 用户确认收款模式
"""
import base64
import json
import secrets
import ssl
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request

API_BASE = 'https://api.mch.weixin.qq.com'
CREATE_PATH = '/v3/fund-app/mch-transfer/transfer-bills'

class TransferError(Exception):
    pass

def _cert_serial(cert_path):
    try:
        info = ssl._ssl._test_decode_cert(cert_path)
        serial = info.get('serialNumber')
        if not serial:
            raise ValueError('证书缺少序列号')
        return str(serial).replace(':', '').upper()
    except Exception as e:
        raise TransferError('无法读取商户证书序列号：' + str(e)[:120])

def _rsa_sign(private_key_path, message):
    try:
        proc = subprocess.run(
            ['openssl', 'dgst', '-sha256', '-sign', private_key_path],
            input=message, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        return base64.b64encode(proc.stdout).decode()
    except FileNotFoundError:
        raise TransferError('服务器缺少 openssl，无法完成 APIv3 签名')
    except subprocess.CalledProcessError as e:
        msg = (e.stderr or b'').decode('utf-8', 'ignore')[:160]
        raise TransferError('商户私钥签名失败：' + msg)

def _request(method, path, body, cfg):
    mch_id = str(cfg.get('wechatMchId') or '').strip()
    cert = cfg.get('wechatCertPath') or ''
    key = cfg.get('wechatKeyPath') or ''
    if not mch_id or not cert or not key:
        raise TransferError('商户号/证书/私钥未配置')
    serial = _cert_serial(cert)
    timestamp = str(int(time.time()))
    nonce = secrets.token_hex(16)
    raw = json.dumps(body, ensure_ascii=False, separators=(',', ':')).encode() if body is not None else b''
    message = (method + '\n' + path + '\n' + timestamp + '\n' + nonce + '\n').encode() + raw + b'\n'
    signature = _rsa_sign(key, message)
    authorization = (
        'WECHATPAY2-SHA256-RSA2048 '
        f'mchid="{mch_id}",nonce_str="{nonce}",signature="{signature}",'
        f'timestamp="{timestamp}",serial_no="{serial}"'
    )
    headers = {
        'Authorization': authorization,
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'User-Agent': 'HulunbuirQuiz/1.0',
    }
    req = urllib.request.Request(
        API_BASE + path,
        data=raw if body is not None else None,
        headers=headers,
        method=method,
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = resp.read(1024 * 1024)
            return json.loads(data.decode('utf-8') or '{}')
    except urllib.error.HTTPError as e:
        text = e.read(1024 * 1024).decode('utf-8', 'ignore')
        try:
            payload = json.loads(text)
            raise TransferError(str(payload.get('message') or payload.get('code') or text)[:300])
        except json.JSONDecodeError:
            raise TransferError(str(text)[:300])
    except Exception as e:
        raise TransferError('微信支付接口异常：' + str(e)[:200])

def create_transfer(order, user, cfg):
    """发起商家转账，返回微信响应（可能是 WAIT_USER_CONFIRM / SUCCESS / FAIL）。"""
    openid = str(user.get('openid') or '').strip()
    if not openid:
        raise TransferError('用户 openid 缺失')
    if not str(cfg.get('wechatAppId') or '').strip():
        raise TransferError('公众号 AppID 未配置')
    scene_id = str(cfg.get('wechatTransferSceneId') or '1000').strip()
    info_type = str(cfg.get('wechatTransferSceneInfoType') or '活动名称')[:15]
    info_content = str(cfg.get('wechatTransferSceneInfoContent') or '呼伦贝尔市有奖答题活动')[:32]
    reward = str(cfg.get('wechatTransferSceneReward') or '有奖答题活动奖励')[:32]
    remark = str(cfg.get('wechatTransferRemark') or '有奖答题活动奖励')[:32]
    perception = str(cfg.get('wechatUserRecvPerception') or '活动奖励')[:32]
    payload = {
        'appid': str(cfg['wechatAppId']),
        'out_bill_no': str(order['id'])[:32],
        'transfer_scene_id': scene_id,
        'openid': openid,
        'transfer_amount': int(order['amountCents']),
        'transfer_remark': remark,
        'transfer_scene_report_infos': [
            {'info_type': info_type, 'info_content': info_content},
            {'info_type': '奖励说明', 'info_content': reward},
        ],
        'user_recv_perception': perception,
        'user_recv_style': {'type': str(cfg.get('wechatUserRecvStyle') or 'RED_PACKET')},
    }
    return _request('POST', CREATE_PATH, payload, cfg)

def query_transfer(out_bill_no, cfg):
    no = urllib.parse.quote(str(out_bill_no), safe='')
    return _request('GET', CREATE_PATH + '/out-bill-no/' + no, None, cfg)
