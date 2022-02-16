from logging import getLogger
import boto3
from botocore.exceptions import ClientError

class HostedZones(object):
  def __init__(self, my_config):
    self.logger = getLogger("Main").getChild(self.__class__.__name__)
    self.route53 = boto3.client('route53', config=my_config)
  def GetData(self, parameters, options):
    self.logger.debug("START. parameters: %s, options: %s" % (parameters,options))
    all_hosted_zones = list()
    response = self.route53.list_hosted_zones(**parameters)
    all_hosted_zones.extend(response["HostedZones"])
    while "NextMarker" in response:
      response = self.route53.list_hosted_zones(**parameters, Marker=response["NextMarker"])
      all_hosted_zones.extend(response["HostedZones"])

    for hosted_zone in all_hosted_zones:
      record_sets = self.route53.list_resource_record_sets(HostedZoneId=hosted_zone["Id"])
      hosted_zone["ResourceRecordSets"] = record_sets["ResourceRecordSets"]
    return {"HostedZones": all_hosted_zones}