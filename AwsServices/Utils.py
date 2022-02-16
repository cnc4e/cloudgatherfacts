import boto3
from functools import wraps
import time

# AWS リージョン名のリストを取得する
def GetEc2RegionNames():
  ec2 = boto3.client('ec2')
  regions = map(lambda x: x['RegionName'], ec2.describe_regions()['Regions'])
  return regions

# アカウント情報を取得する
def GetAccountInfo():
  sts = boto3.client('sts')
  id_info = sts.get_caller_identity()
  id_info.pop('ResponseMetadata')
  return id_info

# セッション情報からリージョン情報を取得する
def GetSessionRegionInfo():
  return boto3.session.Session().region_name

# リージョン選択不要なタイプを判別
def IsGlobal(typeName):
    globaltype_list = ["Users", "Roles", "Groups", "Policies", "Buckets", "HostedZones", "DirectConnectGateways"]
    return bool(typeName in globaltype_list)

# 時間計測用のデコレータ関数
def stop_watch(func) :
    @wraps(func)
    def wrapper(*args, **kargs) :
        start = time.time()
        result = func(*args,**kargs)
        elapsed_time =  time.time() - start
        print(f"{func.__name__} は {elapsed_time:.3f} 秒かかりました")
        return result
    return wrapper