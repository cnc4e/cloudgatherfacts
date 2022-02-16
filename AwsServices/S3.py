from logging import getLogger
import boto3
from botocore.exceptions import ClientError
import json

class Buckets(object):
  def __init__(self, my_config):
    self.logger = getLogger("Main").getChild(self.__class__.__name__)
    self.s3 = boto3.client('s3', config=my_config)
  def GetData(self, parameters, options):
    self.logger.debug("START. parameters: %s, options: %s" % (parameters, options))
    buckets = (self.s3.list_buckets(**parameters))["Buckets"]

    # Filtersの条件で絞り込む
    if "TagFilters" in options:
      buckets = self.SelectTagFilters(buckets=buckets, filters=options["TagFilters"])       

    if options.get("HasDetail") is not False:
      for bucket in buckets:
        bucket["Location"] = (self.s3.get_bucket_location(Bucket=bucket["Name"]))["LocationConstraint"]
        try:
          bucket["TagSet"] = (self.s3.get_bucket_tagging(Bucket=bucket["Name"]))["TagSet"]
        except ClientError as e:
          self.logger.debug("Bucket Name: %s, Exception: %s" % (bucket["Name"], e), exc_info=True)
          # タグが見つからなかったら空のリストを返す
          if e.response['Error']['Code'] == 'NoSuchTagSetError': bucket["TagSet"] = []

        try:
          bucket["PublicAccessBlockConfiguration"] = (self.s3.get_public_access_block(Bucket=bucket["Name"]))["PublicAccessBlockConfiguration"]
        except ClientError as e:
          self.logger.debug("Bucket Name: %s, Exception: %s" % (bucket["Name"], e), exc_info=True)
          # 見つからなかったら空のオブジェクトを返す
          if e.response['Error']['Code'] == 'NoSuchPublicAccessBlockConfiguration': 
            bucket["PublicAccessBlockConfiguration"] = {}

        acl = self.s3.get_bucket_acl(Bucket=bucket["Name"])
        acl.pop("ResponseMetadata")
        bucket["Acl"] = acl

        try:
          encryption = self.s3.get_bucket_encryption(Bucket=bucket["Name"])
          encryption.pop("ResponseMetadata")
          bucket.update(encryption)
        except ClientError as e:
          self.logger.debug("Bucket Name: %s, Exception: %s" % (bucket["Name"], e), exc_info=True)
          # 見つからなかったら空のオブジェクトを返す
          if e.response['Error']['Code'] == 'ServerSideEncryptionConfigurationNotFoundError': 
            bucket["ServerSideEncryptionConfiguration"] = {}

        versioning = self.s3.get_bucket_versioning(Bucket=bucket["Name"])
        versioning.pop("ResponseMetadata")
        if bool(versioning) is False:
          versioning = {"Status": "Off", "MFADelete": "Disabled"}
        bucket["Versioning"] = versioning

        try:
          lifecycle = (self.s3.get_bucket_lifecycle_configuration(Bucket=bucket["Name"]))
          lifecycle.pop("ResponseMetadata")
          bucket["LifecycleConfiguration"] = lifecycle
        except ClientError as e:
          self.logger.debug("Bucket Name: %s, Exception: %s" % (bucket["Name"], e), exc_info=True)
          # 見つからなかったら空のリストを返す
          if e.response['Error']['Code'] == 'NoSuchLifecycleConfiguration': bucket["LifecycleConfiguration"] = []

        analyticsConfiguration = self.s3.list_bucket_analytics_configurations(Bucket=bucket["Name"])
        if "AnalyticsConfigurationList" in analyticsConfiguration:
          bucket["AnalyticsConfigurationList"] = analyticsConfiguration

        try:
          policy = self.s3.get_bucket_policy(Bucket=bucket["Name"])
          policy.pop("ResponseMetadata")
          policy["Policy"] = json.loads(policy["Policy"])
          bucket.update(policy)
        except ClientError as e:
          self.logger.debug("Bucket Name: %s, Exception: %s" % (bucket["Name"], e), exc_info=True)
          # 見つからなかったらスキップする
          if e.response['Error']['Code'] == 'NoSuchBucketPolicy': pass

        try:
          cors = self.s3.get_bucket_cors(Bucket=bucket["Name"])
          bucket["CORSRules"] = cors["CORSRules"]
        except ClientError as e:
          self.logger.debug("Bucket Name: %s, Exception: %s" % (bucket["Name"], e), exc_info=True)
          # 見つからなかったらスキップする
          if e.response['Error']['Code'] == 'NoSuchCORSConfiguration': pass

    if options.get("HasObject") is not False:
      for bucket in buckets:
        all_s3objects = list()
        s3objects = self.s3.list_objects_v2(Bucket=bucket["Name"])
        if "Contents" in s3objects:
          all_s3objects.extend(s3objects["Contents"])
          # オブジェクトが1000件以上あったら全てのオブジェクトを取得する
          while "NextContinuationToken" in s3objects:
            s3objects = self.s3.list_objects_v2(Bucket=bucket["Name"], ContinuationToken=s3objects["NextContinuationToken"])
            all_s3objects.extend(s3objects["Contents"])
          bucket["Contents"] = all_s3objects
    return {"Buckets": buckets}

  # タグのFilterに適合するバケットに絞り込む
  def SelectTagFilters(self, buckets, filters):
    filtered_buckets = list()
    for bucket in buckets:
      try:
        tagset = (self.s3.get_bucket_tagging(Bucket=bucket["Name"]))["TagSet"]
      except ClientError as e:
        continue
      # filter_matched
      # 0: 合致するタグが見つかっていない状態 
      # 1: 合致するタグが見つかった状態
      # 2: 条件不一致(Keyが一致＆Valueが不一致)のタグが見つかった状態      
      filter_matched = 0       
      for filter in filters:
        for tag in tagset:
          if tag["Key"] == filter["Key"]:
            if tag["Value"] in filter["Values"]:
              filter_matched = 1
              break
            else: 
              filter_matched = 2
              break
        if filter_matched ==2: break
      # 条件合致するタグが1つ以上存在＆条件不一致のタグが存在しないバケットのみを追加する
      if filter_matched == 1: filtered_buckets.append(bucket)
    return filtered_buckets