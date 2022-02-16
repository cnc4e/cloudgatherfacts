from logging import getLogger
from botocore.config import Config
import boto3
import json
from .Utils import IsGlobal, stop_watch

class AwsConfig(object):
  def __init__(self, typeName):
    self.logger = getLogger("Main").getChild(self.__class__.__name__)
    self.typeName = typeName

  def ExecQuery(self, query, regions):
    self.logger.debug("START. query: %s, regions: %s" % (query, regions))
    result_list = list()

    for region in regions:
      self.logger.info("リソースの情報を収集しています: %s (%s)" % (self.typeName, region))
      client = boto3.client('config', config=Config(region_name = region))
      response = client.select_resource_config(Expression=query)
      while "NextToken" in response:
        response = self.client.select_resource_config(Expression=query, NextToken=response["NextToken"])
      resultjsons = list()
      for result in response["Results"]:
        resultjsons.append(json.loads(result))
      # 要素にリージョン名を追加
      for resource in resultjsons:
        resource["Region"] = region
      result_list.extend(resultjsons)

    return result_list
