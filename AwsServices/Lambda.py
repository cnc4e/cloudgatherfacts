from logging import getLogger
import boto3
from botocore.exceptions import ClientError
import json

class Functions(object):
  def __init__(self, my_config):
    self.logger = getLogger("Main").getChild(self.__class__.__name__)
    self.functions = boto3.client('lambda', config=my_config)
    self.ec2 = boto3.client('ec2', config=my_config)
  def GetData(self, parameters, options):
    self.logger.debug("START. parameters: %s, options: %s" % (parameters,options))
    all_list_functions = list()
    response = self.functions.list_functions(**parameters)
    all_list_functions.extend(response["Functions"])
    while "NextMarker" in response:
      response = self.functions.list_functions(**parameters, Marker=response["NextMarker"])
      all_list_functions.extend(response["Functions"])

    for function in all_list_functions:
      try:
        policys = self.functions.get_policy(FunctionName=function["FunctionName"])
        function["Policy"] = json.loads(policys["Policy"])
      except ClientError as e:
        self.logger.debug("Function Name: %s, Exception: %s" % (function["FunctionName"], e), exc_info=True)
        # 見つからなかったら空のオブジェクトを返す
        if e.response['Error']['Code'] == 'ResourceNotFoundException': 
          function["Policy"] = {}

      if "Environment" not in function: function["Environment"] = {"Variables": {}}

      if "VpcConfig" in function:
        if len(function["VpcConfig"]["SubnetIds"]) > 0:
          function["VpcConfig"]["Subnets"] = (self.ec2.describe_subnets(SubnetIds=function["VpcConfig"]["SubnetIds"]))["Subnets"]
        if len(function["VpcConfig"]["SecurityGroupIds"]) > 0:
          function["VpcConfig"]["SecurityGroups"] = (self.ec2.describe_security_groups(GroupIds=function["VpcConfig"]["SecurityGroupIds"]))["SecurityGroups"]
    return {"Functions": all_list_functions}