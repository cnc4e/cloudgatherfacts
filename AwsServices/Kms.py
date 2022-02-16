from logging import getLogger
import boto3

class Keys(object):
  def __init__(self, my_config):
    self.logger = getLogger("Main").getChild(self.__class__.__name__)
    self.kms = boto3.client('kms', config=my_config)
  def GetData(self, parameters, options):
    self.logger.debug("START. parameters: %s, options: %s" % (parameters,options))
    response = self.kms.list_keys(**parameters)
    key_details = list()
    for key in response["Keys"]:
      key_detail = (self.kms.describe_key(KeyId=key["KeyId"]))["KeyMetadata"]
      key_detail["Aliases"] = (self.kms.list_aliases(KeyId=key["KeyId"]))["Aliases"]
      key_details.append(key_detail)
    return {"Keys": key_details}
