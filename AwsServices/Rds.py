from logging import getLogger
import boto3
import json

class DBInstances(object):
  def __init__(self, my_config):
    self.logger = getLogger("Main").getChild(self.__class__.__name__)
    self.rds = boto3.client('rds', config=my_config)
  def GetData(self, parameters, options):
    self.logger.debug("START. parameters: %s, options: %s" % (parameters,options))
    all_instances = list()
    response = self.rds.describe_db_instances(**parameters)
    all_instances.extend(response["DBInstances"])
    while "Marker" in response:
      response = self.rds.describe_db_instances(**parameters, Marker=response["Marker"])
      all_instances.extend(response["DBInstances"])
    return {"DBInstances": all_instances}

class DBProxies(object):
  def __init__(self, my_config):
    self.logger = getLogger("Main").getChild(self.__class__.__name__)
    self.rds = boto3.client('rds', config=my_config)
    self.ec2 = boto3.client('ec2', config=my_config)
  def GetData(self, parameters, options):
    self.logger.debug("START. parameters: %s, options: %s" % (parameters,options))
    all_proxies = list()
    response = self.rds.describe_db_proxies(**parameters)
    all_proxies.extend(response["DBProxies"])
    for proxies in all_proxies:
      if len(proxies["VpcSecurityGroupIds"]) > 0:
        proxies["SecurityGroups"] = (self.ec2.describe_security_groups(GroupIds=proxies["VpcSecurityGroupIds"]))["SecurityGroups"]
      if len(proxies["VpcSubnetIds"]) > 0:
        proxies["VpcSubnets"] = (self.ec2.describe_subnets(SubnetIds=proxies["VpcSubnetIds"]))["Subnets"]
    while "Marker" in response:
      response = self.rds.describe_db_proxies(**parameters, Marker=response["Marker"])
      all_proxies.extend(response["DBProxies"])
    return {"DBProxies": all_proxies}

class EventSubscriptions(object):
  def __init__(self, my_config):
    self.logger = getLogger("Main").getChild(self.__class__.__name__)
    self.rds = boto3.client('rds', config=my_config)
  def GetData(self, parameters, options):
    self.logger.debug("START. parameters: %s, options: %s" % (parameters,options))
    all_ubscriptions = list()
    response = self.rds.describe_event_subscriptions(**parameters)
    all_ubscriptions.extend(response["EventSubscriptionsList"])
    while "Marker" in response:
      response = self.rds.describe_event_subscriptions(**parameters, Marker=response["Marker"])
      all_ubscriptions.extend(response["EventSubscriptionsList"])
    return {"EventSubscriptions": all_ubscriptions}
