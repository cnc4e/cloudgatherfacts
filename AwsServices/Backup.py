from logging import getLogger
import boto3
from botocore.exceptions import ClientError
import json

class Backups(object):
  def __init__(self, my_config):
    self.logger = getLogger("Main").getChild(self.__class__.__name__)
    self.backups = boto3.client('backup', config=my_config)
  def GetData(self, parameters, options):
    self.logger.debug("START. parameters: %s, options: %s" % (parameters,options))
    all_list_plans = list()
    response = self.backups.list_backup_plans(**parameters)
    all_list_plans.extend(response["BackupPlansList"])
    while "NextToken" in response:
      response = self.backups.list_backup_plans(**parameters, NextToken=response["NextToken"])
      all_list_plans.extend(response["BackupPlansList"])

    for plan in all_list_plans:
      try:
        Rules = self.backups.get_backup_plan(BackupPlanId=plan["BackupPlanId"])
        plan["Rules"] = Rules["BackupPlan"]["Rules"]
      except ClientError as e:
        self.logger.debug("plan Id: %s, Exception: %s" % (plan["BackupPlanId"], e), exc_info=True)
        # 見つからなかったら空のオブジェクトを返す
        if e.response['Error']['Code'] == 'ResourceNotFoundException': 
          plan["Rules"] = {}
      
      for rule in plan["Rules"]:
        try:
          vault = self.backups.describe_backup_vault(BackupVaultName=rule["TargetBackupVaultName"])
          vault.pop("ResponseMetadata")
          rule["TargetBackupVault"] = vault
        except ClientError as e:
          self.logger.debug("tBackupVault Name: %s, Exception: %s" % (rule["TargetBackupVaultName"], e), exc_info=True)
          # 見つからなかったら空のオブジェクトを返す
          if e.response['Error']['Code'] == 'ResourceNotFoundException': 
            plan["Rules"]["TargetBackupVault"] = {}
      
    return {"Backups": all_list_plans}