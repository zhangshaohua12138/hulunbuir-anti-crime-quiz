"""微信现金红包（商户已开通普通红包权限）适配器。
使用同一 mch_billno 查询后重试；支付不确定时保留挂账，禁止换单号。
"""
import hashlib
import os
import secrets
import ssl
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta

class PaymentPending(Exception): pass

def billno(order_id, created=0, merchant=None):
    # 商户号 + 订单创建日 + 10位稳定序号；跨天重试保持不变。
    merchant=merchant or os.environ['WECHAT_MCH_ID']
    date=datetime.fromtimestamp(created, timezone(timedelta(hours=8))).strftime('%Y%m%d')
    suffix=str(int(hashlib.sha256(order_id.encode()).hexdigest(),16) % 10**10).zfill(10)
    return merchant + date + suffix

def request_xml(endpoint, fields, cfg=None):
    key=(cfg or {}).get('wechatPayKey') or os.environ['WECHAT_PAY_KEY']
    cert=(cfg or {}).get('wechatCertPath') or os.environ['WECHAT_CERT_PATH']
    cert_key=(cfg or {}).get('wechatKeyPath') or os.environ['WECHAT_KEY_PATH']
    fields={**fields,'nonce_str':secrets.token_hex(16)}
    raw='&'.join(f'{k}={fields[k]}' for k in sorted(fields) if fields[k] not in ('',None))+'&key='+key
    fields['sign']=hashlib.md5(raw.encode()).hexdigest().upper()
    root=ET.Element('xml')
    for k,v in fields.items(): ET.SubElement(root,k).text=str(v)
    context=ssl.create_default_context()
    context.load_cert_chain(cert,cert_key)
    req=urllib.request.Request('https://api.mch.weixin.qq.com'+endpoint,data=ET.tostring(root,encoding='utf-8'),headers={'Content-Type':'application/xml'})
    with urllib.request.urlopen(req,context=context,timeout=15) as response: body=response.read(1024*1024)
    if b'<!DOCTYPE' in body or b'<!ENTITY' in body: raise PaymentPending('微信响应格式异常')
    result={n.tag:n.text or '' for n in ET.fromstring(body)}
    if result.get('return_code')!='SUCCESS': raise PaymentPending(result.get('return_msg','微信连接异常'))
    if result.get('sign'):
        signed='&'.join(f'{k}={result[k]}' for k in sorted(result) if k!='sign' and result[k]!='')+'&key='+key
        import hmac
        if not hmac.compare_digest(hashlib.md5(signed.encode()).hexdigest().upper(),result['sign']): raise PaymentPending('微信响应签名校验失败')
    return result

def transfer(order,user,cfg=None):
    cfg=cfg or {}
    merchant=cfg.get('wechatMchId') or os.environ['WECHAT_MCH_ID']; appid=cfg.get('wechatAppId') or os.environ['WECHAT_APP_ID']; number=billno(order['id'],order.get('created',0),merchant)
    base=dict(mch_id=merchant,mch_billno=number)
    result=request_xml('/mmpaymkttransfers/gethbinfo',{**base,'appid':appid,'bill_type':'MCHT'},cfg)
    if result.get('result_code')=='SUCCESS':
        status=result.get('status')
        if status=='RECEIVED': return {'status':'paid','transactionId':result.get('detail_id') or number}
        if status in ('SENT','SENDING'): return {'status':'sent','transactionId':result.get('detail_id') or number}
        raise PaymentPending('红包状态：'+str(status)+'，请商户平台核实')
    if result.get('err_code') not in ('NOT_FOUND','NOTFUND'):
        raise PaymentPending('查询红包失败：'+result.get('err_code_des','未知错误'))
    response=request_xml('/mmpaymkttransfers/sendredpack',{**base,'wxappid':appid,'send_name':cfg.get('wechatSendName') or os.getenv('WECHAT_SEND_NAME','活动主办方'),'re_openid':user['openid'],'total_amount':order['amountCents'],'total_num':1,'wishing':cfg.get('wechatWishing') or os.getenv('WECHAT_WISHING','感谢参与平安建设'),'client_ip':cfg.get('wechatClientIp') or os.environ['WECHAT_CLIENT_IP'],'act_name':cfg.get('wechatActName') or os.getenv('WECHAT_ACT_NAME','扫黑除恶知识答题'),'remark':'有奖答题活动奖励'},cfg)
    if response.get('result_code')!='SUCCESS': raise PaymentPending(response.get('err_code_des','红包发放待核实'))
    # 发放成功表示红包已发送，并不等于用户已经领取到账。
    return {'status':'sent','transactionId':response.get('send_listid') or number}
