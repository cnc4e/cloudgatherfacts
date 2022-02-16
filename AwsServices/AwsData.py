from logging import getLogger
from botocore.config import Config
from botocore.exceptions import ClientError, EndpointConnectionError, ParamValidationError
from .Ec2 import Vpcs, Subnets, Reservations, SecurityGroups, Volumes, NetworkInterfaces
from .Ec2 import RouteTables, NetworkAcls, InternetGateways, Addresses, NatGateways, DhcpOptions
from .Elb import LoadBalancers, TargetGroups
from .Iam import Users, Groups, Roles, Policies
from .Kms import Keys
from .S3 import Buckets
from .Sns import Topics
from .CloudTrail import Trails
from .CloudWatch import MetricAlarms, EventRules, LogGroups, MetricFilters
from .Efs import FileSystems
from .Route53 import HostedZones
from .Lambda import Functions
from .Backup import Backups
from .DirectConnectGateway import DirectConnectGateways
from .Rds import DBInstances, DBProxies, EventSubscriptions
from .Utils import GetEc2RegionNames, IsGlobal, stop_watch

class AwsData(object):
  def __init__(self):
    self.logger = getLogger("Main").getChild(self.__class__.__name__)
    
  def GetAwsData(self, typeName, parameters, options, regions):
    self.logger.debug("START. typeName: %s, parameters: %s, options: %s, regions: %s" % (typeName, parameters, options, regions))
    config = None
    result_list = list()

    for region in regions:
      self.logger.info("リソースの情報を収集しています: %s (%s)" % (typeName, "global" if IsGlobal(typeName) else region))
      config = Config(region_name = region)
      # typeNameの名前から対応するクラスのインスタンスを生成する
      try:
        cls = globals()[typeName]
        instance = cls(config)
      except Exception:
        # リソースタイプが未対応
        raise ResourceTypeError(typeName)
      # リソースの情報を収集する
      try:
        response = instance.GetData(parameters, options)
      except ParamValidationError as e:
        # parametersのバリデーションエラー
        raise ParameterError(e.args)
      except ClientError as e:
        # AWSの例外が発生
        raise AWSClientError(e.args)
      # 要素にリージョン名を追加
      for resource in response[typeName]:
        resource["Region"] = "global" if IsGlobal(typeName) else region

      result_list.extend(response[typeName])
      # グローバルリージョン対象のリソースならループを抜ける
      if IsGlobal(typeName): break

    return result_list

  # AWS リージョン名のリストを取得する
  # AWSへの接続確認（認証情報, プロキシのチェック）も兼ねる
  def GetAllRegionNames(self):
    self.logger.debug("START")
    try:
      regions = GetEc2RegionNames()
    except EndpointConnectionError as e:
      # ネットワーク的な問題（プロキシ設定等）
      raise AWSConnectionError("ネットワークの設定を確認してください: %s" % e)
    except ClientError as e:
      # 認証の問題（アクセスキー/シークレットアクセスキー/セッショントークン）
      if e.response['Error']['Code'] == 'AuthFailure':
        raise AWSConnectionError("認証に失敗しました。アクセスキー/シークレットアクセスキーを確認してください: %s" % e.response['Error']['Message'])
    return regions

class ResourceTypeError(Exception):
  """リソースタイプが未対応であることを知らせる例外クラス"""
  pass

class AWSConnectionError(Exception):
  """AWSサービスへの接続に失敗したことを知らせる例外クラス"""
  pass

class ParameterError(Exception):
  """parametersのバリデーションエラーを知らせる例外クラス"""
  pass

class AWSClientError(Exception):
  """AWSのClientErrorをラップする例外クラス"""
  pass

class QueryInvalidError(Exception):
  """AWSConfigのクエリ構文エラーをラップする例外クラス"""
  pass