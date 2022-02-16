from logging import getLogger
import boto3
from botocore.exceptions import ClientError

class FileSystems(object):
  def __init__(self, my_config):
    self.logger = getLogger("Main").getChild(self.__class__.__name__)
    self.efs = boto3.client('efs', config=my_config)
  def GetData(self, parameters, options):
    self.logger.debug("START. parameters: %s, options: %s" % (parameters,options))
    try:
      all_file_systems = list()
      filesystems = self.efs.describe_file_systems(**parameters)
      all_file_systems.extend(filesystems["FileSystems"])
      while "NextMarker" in filesystems:
        filesystems = self.efs.describe_file_systems(**parameters, Marker=filesystems["NextMarker"])
        all_file_systems.extend(filesystems["FileSystems"])

      for filesystem in all_file_systems:
        try:
          all_mount_targets = list()
          mount_targets = self.efs.describe_mount_targets(FileSystemId=filesystem["FileSystemId"])
          all_mount_targets.extend(mount_targets["MountTargets"])
          while "NextMarker" in mount_targets:
            mount_targets = self.efs.describe_mount_targets(FileSystemId=filesystem["FileSystemId"], Marker=mount_targets["NextMarker"])
            all_mount_targets.extend(mount_targets["MountTargets"])
          
          for mount_target in all_mount_targets:
            mount_target["SecurityGroups"] = (self.efs.describe_mount_target_security_groups(MountTargetId=mount_target["MountTargetId"]))["SecurityGroups"]
        except ClientError as e:
          self.logger.debug("FileSystemId: %s, Exception: %s" % (filesystem["FileSystemId"], e), exc_info=True)
          # マウントターゲットが見つからなかったら空のリストを返す
          if e.response['Error']['Code'] == 'MountTargetNotFound': filesystem["MountTargets"] = []
        filesystem["MountTargets"] = all_mount_targets
    except ClientError as e:
      self.logger.debug(e, exc_info=True)
      # ファイルシステムが見つからなかったら空のリストを返す
      if e.response['Error']['Code'] == 'FileSystemNotFound': filesystems = []
    return {"FileSystems": all_file_systems}