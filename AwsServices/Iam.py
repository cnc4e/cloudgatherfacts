from logging import getLogger
import boto3
from botocore.exceptions import ClientError

class Users(object):
  def __init__(self, my_config):
    self.logger = getLogger("Main").getChild(self.__class__.__name__)
    self.iam = boto3.client('iam', config=my_config)
  def GetData(self, parameters, options):
    self.logger.debug("START. parameters: %s, options: %s" % (parameters,options))
    all_users = list()
    users = self.iam.list_users(**parameters)
    all_users.extend(users["Users"])
    while "Marker" in users:
      users = self.iam.list_users(**parameters, Marker=users["Marker"])
      all_users.extend(users["Users"])

    for user in all_users:
      groups = (self.iam.list_groups_for_user(UserName=user["UserName"]))["Groups"]
      user["Groups"] = groups
      user["AttachedUserPolicies"] = (self.iam.list_attached_user_policies(UserName=user["UserName"]))["AttachedPolicies"]

      g_policies = list()
      for group in groups:
        policies = (self.iam.list_attached_group_policies(GroupName=group["GroupName"]))["AttachedPolicies"]
        g_policies.extend(policies)
      user["AttachedGroupPolicies"] = g_policies

      i_detail_policies = list()
      i_policies = (self.iam.list_user_policies(UserName=user["UserName"]))["PolicyNames"]
      for policyName in i_policies:
        policy = self.iam.get_user_policy(UserName=user["UserName"], PolicyName=policyName)
        policy.pop("ResponseMetadata")
        i_detail_policies.append(policy)
      user["InlinePolicies"] = i_detail_policies

      user["AccessKeyIDs"] = (self.iam.list_access_keys(UserName=user["UserName"]))["AccessKeyMetadata"]
    return {"Users": all_users}

class Groups(object):
  def __init__(self, my_config):
    self.logger = getLogger("Main").getChild(self.__class__.__name__)
    self.iam = boto3.client('iam', config=my_config)
  def GetData(self, parameters, options):
    self.logger.debug("START. parameters: %s, options: %s" % (parameters,options))
    all_groups = list()
    groups = self.iam.list_groups(**parameters)
    all_groups.extend(groups["Groups"])
    while "Marker" in groups:
      groups = self.iam.list_groups(**parameters, Marker=groups["Marker"])
      all_groups.extend(groups["Groups"])
    
    for group in all_groups:
      group["AttachedGroupPolicies"] = (self.iam.list_attached_group_policies(GroupName=group["GroupName"]))["AttachedPolicies"]

      i_detail_policies = list()
      i_policies = (self.iam.list_group_policies(GroupName=group["GroupName"]))["PolicyNames"]
      for policyName in i_policies:
        policy = self.iam.get_group_policy(GroupName=group["GroupName"], PolicyName=policyName)
        policy.pop("ResponseMetadata")
        i_detail_policies.append(policy)
      group["InlinePolicies"] = i_detail_policies

      group["Users"] = (self.iam.get_group(GroupName=group["GroupName"]))["Users"]
    return {"Groups": all_groups}

class Roles(object):
  def __init__(self, my_config):
    self.logger = getLogger("Main").getChild(self.__class__.__name__)
    self.iam = boto3.client('iam', config=my_config)
  def GetData(self, parameters, options):
    self.logger.debug("START. parameters: %s, options: %s" % (parameters,options))
    all_roles = list()
    roles = self.iam.list_roles(**parameters)
    all_roles.extend(roles["Roles"])
    while "Marker" in roles:
      roles = self.iam.list_roles(**parameters, Marker=roles["Marker"])
      all_roles.extend(roles["Roles"])
    
    for role in all_roles:
      role["AttachedRolePolicies"] = (self.iam.list_attached_role_policies(RoleName=role["RoleName"]))["AttachedPolicies"]
    return {"Roles": all_roles}

class Policies(object):
  def __init__(self, my_config):
    self.logger = getLogger("Main").getChild(self.__class__.__name__)
    self.iam = boto3.client('iam', config=my_config)
  def GetData(self, parameters, options):
    self.logger.debug("START. parameters: %s, options: %s" % (parameters,options))
    all_policies = list()
    policies = self.iam.list_policies(**parameters)
    all_policies.extend(policies["Policies"])
    while "Marker" in policies:
      policies = self.iam.list_policies(**parameters, Marker=policies["Marker"])
      all_policies.extend(policies["Policies"])
    
    policy_details = list()
    for policy in all_policies:
      policy_detail = (self.iam.get_policy(PolicyArn=policy["Arn"]))["Policy"]
      policy_detail["PolicyVersion"] = (self.iam.get_policy_version(PolicyArn=policy["Arn"],VersionId=policy["DefaultVersionId"]))["PolicyVersion"]
      policy_details.append(policy_detail)
    return {"Policies": policy_details}
