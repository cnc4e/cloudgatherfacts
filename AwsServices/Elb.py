from logging import getLogger
import boto3
from botocore.exceptions import ClientError

class LoadBalancers(object):
  def __init__(self, my_config):
    self.logger = getLogger("Main").getChild(self.__class__.__name__)
    self.elb = boto3.client('elbv2', config=my_config)
  def GetData(self, parameters, options):
    self.logger.debug("START. parameters: %s, options: %s" % (parameters,options))
    try:
      all_load_balancers = list()
      loadBalancers = self.elb.describe_load_balancers(**parameters)
      all_load_balancers.extend(loadBalancers["LoadBalancers"])
      while "NextMarker" in loadBalancers:
        loadBalancers = self.elb.describe_load_balancers(**parameters, Marker=loadBalancers["NextMarker"])
        all_load_balancers.extend(loadBalancers["LoadBalancers"])

      for loadbalancer in all_load_balancers:
        # ロードバランサーの追加属性
        lb_attributes = self.elb.describe_load_balancer_attributes(LoadBalancerArn=loadbalancer["LoadBalancerArn"])
        for attr in lb_attributes["Attributes"]:
          loadbalancer[attr['Key']] = attr['Value']
        # タグ
        lb_tags = self.elb.describe_tags(ResourceArns=[loadbalancer["LoadBalancerArn"]])
        loadbalancer["Tags"] = lb_tags["TagDescriptions"][0]["Tags"]
        # リスナー
        try:
          all_listeners = list()
          listeners = self.elb.describe_listeners(LoadBalancerArn=loadbalancer["LoadBalancerArn"])
          all_listeners.extend(listeners["Listeners"])
          while "NextMarker" in listeners:
            listeners = self.elb.describe_listeners(LoadBalancerArn=loadbalancer["LoadBalancerArn"], Marker=listeners["NextMarker"])
            all_listeners.extend(listeners["Listeners"])

          for listener in all_listeners:
            try:
              all_rules = list()
              rules = self.elb.describe_rules(ListenerArn=listener["ListenerArn"])
              all_rules.extend(rules["Rules"])
              while "NextMarker" in rules:
                rules = self.elb.describe_rules(ListenerArn=listener["ListenerArn"], Marker=rules["NextMarker"])
                all_rules.extend(rules["Rules"])
              listener["Rules"] = all_rules
            except ClientError as e:
              self.logger.debug("LoadBalancerArn: %s, ListenerArn: %s, Exception: %s" % (loadbalancer["LoadBalancerArn"], listener["ListenerArn"], e), exc_info=True)
              # ルールが見つからなかったら、空のリストを返す
              if e.response['Error']['Code'] == 'RuleNotFound': listener["Rules"] = []
        except ClientError as e:
          self.logger.debug("LoadBalancerArn: %s, Exception: %s" % (loadbalancer["LoadBalancerArn"], e), exc_info=True)
          # リスナーが見つからなかったら、空のリストを返す
          if e.response['Error']['Code'] == 'ListenerNotFound': listeners = []
        loadbalancer["Listeners"] = all_listeners
    except ClientError as e:
      self.logger.debug(e, exc_info=True)
      # ロードバランサーが見つからなかったら、空のリストを返す
      if e.response['Error']['Code'] == 'LoadBalancerNotFound': loadBalancers = []
    return {"LoadBalancers": all_load_balancers}
    
class TargetGroups(object):
  def __init__(self, my_config):
    self.logger = getLogger("Main").getChild(self.__class__.__name__)
    self.elb = boto3.client('elbv2', config=my_config)
  def GetData(self, parameters, options):
    self.logger.debug("START. parameters: %s, options: %s" % (parameters,options))
    try:
      targetgroups = (self.elb.describe_target_groups(**parameters))["TargetGroups"]
      for targetgroup in targetgroups:
        try:
          targetgroup["TargetHealthDescriptions"] = (self.elb.describe_target_health(TargetGroupArn=targetgroup["TargetGroupArn"]))["TargetHealthDescriptions"]
        except ClientError as e:
          self.logger.debug("TargetGroupArn: %s, Exception: %s" % (targetgroup["TargetGroupArn"], e), exc_info=True)
          if e.response['Error']['Code'] in ['HealthUnavailable','InvalidTarget']: targetgroup["TargetHealthDescriptions"] = []
    except ClientError as e:
      self.logger.debug(e, exc_info=True)
      # ターゲットグループが見つからなかったら、空のリストを返す
      if e.response['Error']['Code'] in ['LoadBalancerNotFound','TargetGroupNotFound']: targetgroups = []
    return {"TargetGroups": targetgroups}
