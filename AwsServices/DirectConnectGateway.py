from logging import getLogger
import boto3
from botocore.exceptions import ClientError
import json

class DirectConnectGateways(object):
  def __init__(self, my_config):
    self.logger = getLogger("Main").getChild(self.__class__.__name__)
    self.directconnects = boto3.client('directconnect', config=my_config)
    self.ec2 = boto3.client('ec2', config=my_config)
  def GetData(self, parameters, options):
    self.logger.debug("START. parameters: %s, options: %s" % (parameters,options))
    all_list_gateways = list()
    response = self.directconnects.describe_direct_connect_gateways(**parameters)
    all_list_gateways.extend(response["directConnectGateways"])
    while "nextToken" in response:
      response = self.directconnects.describe_direct_connect_gateways(**parameters, nextToken=response["nextToken"])
      all_list_gateways.extend(response["directConnectGateways"])

    for gateway in all_list_gateways:
      # アタッチされた仮想インターフェイスのIDを取得する
      vif_list = list()
      attachments = self.directconnects.describe_direct_connect_gateway_attachments(directConnectGatewayId=gateway["directConnectGatewayId"])
      vif_list.extend(attachments["directConnectGatewayAttachments"])
      while "nextToken" in attachments:
        attachments = self.directconnects.describe_direct_connect_gateway_attachments(directConnectGatewayId=gateway["directConnectGatewayId"], nextToken=response["nextToken"])
        vif_list.extend(attachments["directConnectGatewayAttachments"])
      # 仮想インターフェイス情報を取得する
      attached_vif_list = list()
      for vif in vif_list:
        id = vif["virtualInterfaceId"]
        vif_info = self.directconnects.describe_virtual_interfaces(virtualInterfaceId=id)
        attached_vif_list.extend(vif_info["virtualInterfaces"])
      gateway["virtualInterfaces"] = attached_vif_list
      
      # 関連付けられた仮想ゲートウェイ情報を取得する
      vgw_list = list()
      vgw = self.directconnects.describe_direct_connect_gateway_associations(directConnectGatewayId=gateway["directConnectGatewayId"])
      vgw_list.extend(vgw["directConnectGatewayAssociations"])
      while "nextToken" in vgw:
        vgw = self.directconnects.describe_direct_connect_gateway_associations(directConnectGatewayId=gateway["directConnectGatewayId"], nextToken=response["nextToken"])
        vgw_list.extend(vgw["directConnectGatewayAssociations"])
      for associated_gw in vgw_list:
        vpn = (self.ec2.describe_vpn_gateways(VpnGatewayIds=[associated_gw["associatedGateway"]["id"]]))["VpnGateways"][0]
        associated_gw["Type"] = vpn["Type"]
        associated_gw["Tags"] = vpn["Tags"]
      gateway["directConnectGatewayAssociations"] = vgw_list
      
    return {"DirectConnectGateways": all_list_gateways}