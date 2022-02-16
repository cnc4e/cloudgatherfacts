from logging import getLogger
import boto3

class Vpcs(object):
  def __init__(self, my_config):
    self.logger = getLogger("Main").getChild(self.__class__.__name__)
    self.ec2 = boto3.client('ec2', config=my_config)
  def GetData(self, parameters, options):
    self.logger.debug("START. parameters: %s, options: %s" % (parameters,options))
    all_vpcs = list()
    response = self.ec2.describe_vpcs(**parameters)
    all_vpcs.extend(response["Vpcs"])
    while "NextToken" in response:
      response = self.ec2.describe_vpcs(**parameters, NextToken=response["NextToken"])
      all_vpcs.extend(response["Vpcs"])
    for vpc in all_vpcs:
      response = self.ec2.describe_vpc_attribute(Attribute='enableDnsSupport', VpcId=vpc["VpcId"])
      vpc["EnableDnsSupport"] = response["EnableDnsSupport"]["Value"]
      response = self.ec2.describe_vpc_attribute(Attribute='enableDnsHostnames', VpcId=vpc["VpcId"])
      vpc["EnableDnsHostnames"] = response["EnableDnsHostnames"]["Value"]
    return {"Vpcs": all_vpcs}

class Subnets(object):
  def __init__(self, my_config):
    self.logger = getLogger("Main").getChild(self.__class__.__name__)
    self.ec2 = boto3.client('ec2', config=my_config)
  def GetData(self, parameters, options):
    self.logger.debug("START. parameters: %s, options: %s" % (parameters, options))
    all_subnets = list()
    response = self.ec2.describe_subnets(**parameters)
    all_subnets.extend(response["Subnets"])
    while "NextToken" in response:
      response = self.ec2.describe_subnets(**parameters, NextToken=response["NextToken"])
      all_subnets.extend(response["Subnets"])
    return {"Subnets": all_subnets}

class Reservations(object):
  def __init__(self, my_config):
    self.logger = getLogger("Main").getChild(self.__class__.__name__)
    self.ec2 = boto3.client('ec2', config=my_config)
    self.iam = boto3.client('iam', config=my_config)
  def GetData(self, parameters, options):
    self.logger.debug("START. parameters: %s, options: %s" % (parameters,options))
    all_instances = list()
    response = self.ec2.describe_instances(**parameters)
    all_instances.extend(response["Reservations"])
    while "NextToken" in response:
      response = self.ec2.describe_instances(**parameters, NextToken=response["NextToken"])
      all_instances.extend(response["Reservations"])
    
    for reservation in all_instances:
      for instance in reservation["Instances"]:
        # Reservationの所有者IDをインスタンスにも設定
        instance["OwnerId"] = reservation["OwnerId"]
        # Reservationの所有者IDをインスタンスにも設定
        instance["ReservationId"] = reservation["ReservationId"]
        # インスタンスプロファイル情報があったら詳細情報を取得する
        if "IamInstanceProfile" in instance:
          # IamInstanceProfileのARNからインスタンスプロファイル名を取得
          profileName = instance["IamInstanceProfile"]["Arn"].split('/')[-1]
          instance["IamInstanceProfile"] = self.iam.get_instance_profile(InstanceProfileName=profileName)["InstanceProfile"]
    return {"Reservations": all_instances}

class SecurityGroups(object):
  def __init__(self, my_config):
    self.logger = getLogger("Main").getChild(self.__class__.__name__)
    self.ec2 = boto3.client('ec2', config=my_config)
  def GetData(self, parameters, options):
    self.logger.debug("START. parameters: %s, options: %s" % (parameters,options))
    all_security_groups = list()
    response = self.ec2.describe_security_groups(**parameters)
    all_security_groups.extend(response["SecurityGroups"])
    while "NextToken" in response:
      response = self.ec2.describe_security_groups(**parameters, NextToken=response["NextToken"])
      all_security_groups.extend(response["SecurityGroups"])
    return {"SecurityGroups": all_security_groups}
    
class Volumes(object):
  def __init__(self, my_config):
    self.logger = getLogger("Main").getChild(self.__class__.__name__)
    self.ec2 = boto3.client('ec2', config=my_config)
  def GetData(self, parameters, options):
    self.logger.debug("START. parameters: %s, options: %s" % (parameters,options))
    all_volumes = list()
    response = self.ec2.describe_volumes(**parameters)
    all_volumes.extend(response["Volumes"])
    while "NextToken" in response:
      response = self.ec2.describe_volumes(**parameters, NextToken=response["NextToken"])
      all_volumes.extend(response["Volumes"])
    return {"Volumes": all_volumes}

class NetworkInterfaces(object):
  def __init__(self, my_config):
    self.logger = getLogger("Main").getChild(self.__class__.__name__)
    self.ec2 = boto3.client('ec2', config=my_config)
  def GetData(self, parameters, options):
    self.logger.debug("START. parameters: %s, options: %s" % (parameters,options))
    all_network_interfaces = list()
    response = self.ec2.describe_network_interfaces(**parameters)
    all_network_interfaces.extend(response["NetworkInterfaces"])
    while "NextToken" in response:
      response = self.ec2.describe_network_interfaces(**parameters, NextToken=response["NextToken"])
      all_network_interfaces.extend(response["NetworkInterfaces"])
    return {"NetworkInterfaces": all_network_interfaces}

class RouteTables(object):
  def __init__(self, my_config):
    self.logger = getLogger("Main").getChild(self.__class__.__name__)
    self.ec2 = boto3.client('ec2', config=my_config)
  def GetData(self, parameters, options):
    self.logger.debug("START. parameters: %s, options: %s" % (parameters,options))
    all_route_tables = list()
    response = self.ec2.describe_route_tables(**parameters)
    all_route_tables.extend(response["RouteTables"])
    while "NextToken" in response:
      response = self.ec2.describe_route_tables(**parameters, NextToken=response["NextToken"])
      all_route_tables.extend(response["RouteTables"])
    return {"RouteTables": all_route_tables}

class NetworkAcls(object):
  def __init__(self, my_config):
    self.logger = getLogger("Main").getChild(self.__class__.__name__)
    self.ec2 = boto3.client('ec2', config=my_config)
  def GetData(self, parameters, options):
    self.logger.debug("START. parameters: %s, options: %s" % (parameters,options))
    all_network_acls = list()
    response = self.ec2.describe_network_acls(**parameters)
    all_network_acls.extend(response["NetworkAcls"])
    while "NextToken" in response:
      response = self.ec2.describe_network_acls(**parameters, NextToken=response["NextToken"])
      all_network_acls.extend(response["NetworkAcls"])
    return {"NetworkAcls": all_network_acls}

class InternetGateways(object):
  def __init__(self, my_config):
    self.logger = getLogger("Main").getChild(self.__class__.__name__)
    self.ec2 = boto3.client('ec2', config=my_config)
  def GetData(self, parameters, options):
    self.logger.debug("START. parameters: %s, options: %s" % (parameters,options))
    all_internet_gateways = list()
    response = self.ec2.describe_internet_gateways(**parameters)
    all_internet_gateways.extend(response["InternetGateways"])
    while "NextToken" in response:
      response = self.ec2.describe_internet_gateways(**parameters, NextToken=response["NextToken"])
      all_internet_gateways.extend(response["InternetGateways"])
    return {"InternetGateways": all_internet_gateways}

class Addresses(object):
  def __init__(self, my_config):
    self.logger = getLogger("Main").getChild(self.__class__.__name__)
    self.ec2 = boto3.client('ec2', config=my_config)
  def GetData(self, parameters, options):
    self.logger.debug("START. parameters: %s, options: %s" % (parameters,options))
    response = self.ec2.describe_addresses(**parameters)
    response.pop("ResponseMetadata")
    return response

class NatGateways(object):
  def __init__(self, my_config):
    self.logger = getLogger("Main").getChild(self.__class__.__name__)
    self.ec2 = boto3.client('ec2', config=my_config)
  def GetData(self, parameters, options):
    self.logger.debug("START. parameters: %s, options: %s" % (parameters,options))
    all_nat_gateways = list()
    response = self.ec2.describe_nat_gateways(**parameters)
    all_nat_gateways.extend(response["NatGateways"])
    while "NextToken" in response:
      response = self.ec2.describe_nat_gateways(**parameters, NextToken=response["NextToken"])
      all_nat_gateways.extend(response["NatGateways"])
    return {"NatGateways": all_nat_gateways}

class DhcpOptions(object):
  def __init__(self, my_config):
    self.logger = getLogger("Main").getChild(self.__class__.__name__)
    self.ec2 = boto3.client('ec2', config=my_config)
  def GetData(self, parameters, options):
    self.logger.debug("START. parameters: %s, options: %s" % (parameters,options))
    all_dhcp_options = list()
    response = self.ec2.describe_dhcp_options(**parameters)
    all_dhcp_options.extend(response["DhcpOptions"])
    while "NextToken" in response:
      response = self.ec2.describe_dhcp_options(**parameters, NextToken=response["NextToken"])
      all_dhcp_options.extend(response["DhcpOptions"])
    return {"DhcpOptions": all_dhcp_options}
