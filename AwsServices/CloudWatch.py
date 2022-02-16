from logging import getLogger
import boto3
import json

class MetricAlarms(object):
  def __init__(self, my_config):
    self.logger = getLogger("Main").getChild(self.__class__.__name__)
    self.cloudwatch = boto3.client('cloudwatch', config=my_config)
  def GetData(self, parameters, options):
    self.logger.debug("START. parameters: %s, options: %s" % (parameters,options))
    all_alarms = list()
    response = self.cloudwatch.describe_alarms(**parameters)
    all_alarms.extend(response["MetricAlarms"])
    while "NextToken" in response:
      response = self.cloudwatch.describe_alarms(**parameters, NextToken=response["NextToken"])
      all_alarms.extend(response["MetricAlarms"])
    return {"MetricAlarms": all_alarms}

class EventRules(object):
  def __init__(self, my_config):
    self.logger = getLogger("Main").getChild(self.__class__.__name__)
    self.rules = boto3.client('events', config=my_config)
  def GetData(self, parameters, options):
    self.logger.debug("START. parameters: %s, options: %s" % (parameters,options))
    all_rules = list()
    response = self.rules.list_rules(**parameters)
    all_rules.extend(response["Rules"])
    while "NextToken" in response:
      response = self.rules.list_rules(**parameters, NextToken=response["NextToken"])
      all_rules.extend(response["Rules"])

    for rule in all_rules:
      if "EventPattern" in rule: rule["EventPattern"] = json.loads(rule["EventPattern"])
      rule["EventBus"] = self.rules.describe_event_bus(Name=rule["EventBusName"])
      rule["EventBus"].pop("ResponseMetadata")
      if "Policy" in rule["EventBus"]: rule["EventBus"]["Policy"] = json.loads(rule["EventBus"]["Policy"])
      else: rule["EventBus"]["Policy"] = {}
      rule["Targets"] = self.rules.list_targets_by_rule(Rule=rule["Name"])["Targets"]
    return {"EventRules": all_rules}

class LogGroups(object):
  def __init__(self, my_config):
    self.logger = getLogger("Main").getChild(self.__class__.__name__)
    self.cloudwatch = boto3.client('logs', config=my_config)
  def GetData(self, parameters, options):
    self.logger.debug("START. parameters: %s, options: %s" % (parameters,options))
    all_groups = list()
    response = self.cloudwatch.describe_log_groups(**parameters)
    all_groups.extend(response["logGroups"])
    while "NextToken" in response:
      response = self.cloudwatch.describe_log_groups(**parameters, NextToken=response["NextToken"])
      all_groups.extend(response["logGroups"])
    return {"LogGroups": all_groups}

class MetricFilters(object):
  def __init__(self, my_config):
    self.logger = getLogger("Main").getChild(self.__class__.__name__)
    self.cloudwatch = boto3.client('logs', config=my_config)
  def GetData(self, parameters, options):
    self.logger.debug("START. parameters: %s, options: %s" % (parameters,options))
    all_filters = list()
    response = self.cloudwatch.describe_metric_filters(**parameters)
    all_filters.extend(response["metricFilters"])
    while "NextToken" in response:
      response = self.cloudwatch.describe_metric_filters(**parameters, NextToken=response["NextToken"])
      all_filters.extend(response["metricFilters"])
    return {"MetricFilters": all_filters}