from logging import getLogger
import boto3
from botocore.exceptions import ClientError

class Topics(object):
  def __init__(self, my_config):
    self.logger = getLogger("Main").getChild(self.__class__.__name__)
    self.sns = boto3.client('sns', config=my_config)
  def GetData(self, parameters, options):
    self.logger.debug("START. parameters: %s, options: %s" % (parameters,options))
    all_topics = list()
    topics = self.sns.list_topics(**parameters)
    all_topics.extend(topics["Topics"])
    while "NextToken" in topics:
      topics = self.sns.list_topics(**parameters, NextToken=topics["NextToken"])
      all_topics.extend(topics["Topics"])

    for topic in all_topics:
      all_subscriptions = list()
      subscription = self.sns.list_subscriptions_by_topic(TopicArn=topic["TopicArn"])
      if "Subscriptions" in subscription:
        all_subscriptions.extend(subscription["Subscriptions"])
        while "NextToken" in subscription:
          subscription = self.sns.list_subscriptions_by_topic(TopicArn=topic["TopicArn"], NextToken=subscription["NextToken"])
          all_subscriptions.extend(subscription["Subscriptions"])
        topic["Subscriptions"] = all_subscriptions
      tags = self.sns.list_tags_for_resource(ResourceArn=topic["TopicArn"])
      if "Tags" in tags:
        topic["Tags"] = tags["Tags"]
    return {"Topics": all_topics}
