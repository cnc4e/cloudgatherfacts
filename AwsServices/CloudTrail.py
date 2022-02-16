from logging import getLogger
import boto3
from botocore.exceptions import ClientError

class Trails(object):
  def __init__(self, my_config):
    self.logger = getLogger("Main").getChild(self.__class__.__name__)
    self.ctrail = boto3.client('cloudtrail', config=my_config)
  def GetData(self, parameters, options):
    self.logger.debug("START. parameters: %s, options: %s" % (parameters,options))
    all_trails = list()
    response = self.ctrail.list_trails(**parameters)
    all_trails.extend(response["Trails"])
    while "NextToken" in response:
      response = self.ctrail.list_trails(**parameters, NextToken=response["NextToken"])
      all_trails.extend(response["Trails"])

    trail_details = list()
    for trail in all_trails:
      trail_detail = (self.ctrail.get_trail(Name=trail["TrailARN"]))["Trail"]
      status = self.ctrail.get_trail_status(Name=trail["TrailARN"])
      status.pop("ResponseMetadata")
      trail_detail["Status"] = status
      tags = self.ctrail.list_tags(ResourceIdList=[trail["TrailARN"]])
      if "TagsList" in tags["ResourceTagList"][0]:
        trail_detail["Tags"] = tags["ResourceTagList"][0]["TagsList"]
      if trail_detail["HasCustomEventSelectors"] is True:
        event_selectors = self.ctrail.get_event_selectors(TrailName=trail["TrailARN"])
        if "EventSelectors" in event_selectors:
          trail_detail["EventSelectors"] = event_selectors["EventSelectors"]
        if "AdvancedEventSelectors" in event_selectors:
          trail_detail["AdvancedEventSelectors"] = event_selectors["AdvancedEventSelectors"]
      trail_details.append(trail_detail)
    return {"Trails": trail_details}
