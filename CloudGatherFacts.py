import os
import sys
import json
import yaml
import argparse
from datetime import date, datetime
from logging import getLogger, StreamHandler, Formatter, FileHandler, DEBUG, INFO
from AwsServices.AwsData import AwsData, ResourceTypeError, ParameterError, AWSClientError, QueryInvalidError
from AwsServices.AwsConfig import AwsConfig
from Database import DbManager
from AwsServices.Utils import GetAccountInfo, GetSessionRegionInfo

def main():
  args = get_option()

  # ログの設定
  logger = setup_logger(args.debug)
  logger.debug("--------------------------------------------------------------------")

  # 設定ファイルの読み込み
  try:
    with open(args.config, 'r') as yml:
      config = yaml.load(yml, Loader=yaml.SafeLoader)
  except yaml.YAMLError as e:
    logger.error('実行に失敗しました。設定ファイルの記載形式が正しくありません: %s' % e)
    sys.exit(1)
  except FileNotFoundError as e:
    logger.error('実行に失敗しました。設定ファイルが見つかりません: %s' % e)
    sys.exit(1)

  # cloudtypeの確認（AWS以外ならエラー終了）
  if "cloudtype" not in config:
    logger.error('実行に失敗しました。設定ファイルに cloudtype が指定されていません。')
    sys.exit(1)
  if config["cloudtype"] not in ["AWS"]:
    logger.error('実行に失敗しました。指定されたクラウドは対象外です: %s' % config["cloudtype"])
    sys.exit(1)

  # 出力用フォルダの準備
  try:
    os.makedirs(config["outputdir"], exist_ok=True)
  except Exception as e:
    logger.error('実行に失敗しました。outputdirで指定したフォルダが見つかりません: %s' % e)
    sys.exit(1)

  aws = AwsData()
  # AWSへの接続確認（認証情報, プロキシのチェック）を兼ねて
  # リージョン名の一覧を取得する
  try:
    regions = list(aws.GetAllRegionNames())
  except Exception as e:
    logger.error('実行に失敗しました。AWSサービスに接続できません: %s' % e)
    logger.debug(e, exc_info=True)
    sys.exit(1)

  # 指定されたリージョン名の確認(--regionオプション指定時のみ)
  if args.region:
    option_regions = [x.strip() for x in args.region.split(',')]
    unexpected_region = list()
    for region in option_regions:
      if region not in regions:
        unexpected_region.append(region)
    if len(unexpected_region):
      logger.error('実行に失敗しました。リージョン名が不正です: %s' % unexpected_region)
      sys.exit(1)
  else:
    option_regions = [GetSessionRegionInfo()]
      
  outdict = {}
  logger.info("実行を開始します。")

  # AWSからリソース情報を収集
  # 設定ファイルにresources:要素が未定義/要素が空でもエラーにならないよう対処
  resources = config.get("resources", [])
  for resource in resources if resources else []:
    try:
      response = aws.GetAwsData(resource.get("type"), resource.get("parameters", {}), resource.get("options", {}), option_regions)
    except ResourceTypeError as e:
      logger.error('指定されたリソースは未対応です: %s' % e)
      break
    except ParameterError as e:
      logger.error('parametersの記載形式が正しくありません: %s' % e)
      logger.debug(e, exc_info=True)
      break
    except AWSClientError as e:
      logger.error('実行中にエラーが発生しました: %s' % e)
      logger.debug(e, exc_info=True)
      break      
    outdict.update({resource.get("type"): response})
  
  # AWSConfig クエリ実行
  # 設定ファイルにawsconfig:要素が未定義/要素が空でもエラーにならないよう対処
  resources = config.get("awsconfig",[])
  for resource in resources if resources else []:
    typeName = resource.get("name")
    if typeName in outdict:
      logger.warning("指定したリソース名は既に存在します。リソース情報を上書きします。: %s" % typeName)
    query = AwsConfig(typeName)
    try:
      response = query.ExecQuery(resource["query"], option_regions)
    except AWSClientError as e:
      logger.error('実行中にエラーが発生しました: %s' % e)
      logger.debug(e, exc_info=True)
      break
    except QueryInvalidError as e:
      logger.error('クエリの構文が間違っています: %s' % e)
      logger.debug(e, exc_info=True)
      break
    outdict.update({typeName: response})

  # 実行したアカウント、リージョンの情報を付与
  account = GetAccountInfo()
  targetresion = None
  if args.region:
    targetresion = args.region
  else:
    targetresion = GetSessionRegionInfo()
  outdict['Environment'] = {
    'IAM': account,
    'Resion': targetresion
  }

  # 収集した情報(Dictionary)をJSON形式でファイル出力
  try:
    outfile = config["outputdir"] + "/" + config["outputfile"]
    with open(outfile, 'w') as f:
      json.dump(outdict, f, default=json_serial, indent=4)
  except Exception as e:
    logger.error('実行に失敗しました。outputfileで指定したファイルを出力できません: %s' % e)
    sys.exit(1)

  if args.event:
    with open(outfile) as ef:
      outdict2 = json.load(ef)
    # DBへの処理
    try:
      dburl = config['database']['url']
    except (KeyError, TypeError):
      logger.error('実行に失敗しました。設定ファイルにデータベース接続情報が設定されていません。')
      sys.exit(1)
    try:
      manager = DbManager(dburl)
      # イベントテーブルのレコードを作成
      eid = manager.InsertEvent(category='AwsFacts', comment=args.event)
      # CloudGatherFactsデータをDBに保存
      manager.InsertItem(className='AwsFacts', indict=outdict2, eventid=eid, account=account['Account'])
      # コミット
      manager.DbCommit()
    except Exception as e:
      logger.error('実行に失敗しました。データベースにデータ登録できませんでした: %s' % e)
      sys.exit(1)

  logger.info("実行を完了しました。")

# コマンド引数の設定
def get_option():
  parser = argparse.ArgumentParser(description='CloudGatherFacts - クラウド上のリソース情報を収集するツール')
  parser.add_argument('config', help='設定ファイル名')
  parser.add_argument('-R', '--region', help='リージョン名')
  parser.add_argument('-E', '--event', help='DB登録イベントのコメント')
  parser.add_argument('-D', '--debug', help='デバッグログを出力', action='store_true')
  parser.add_argument('-V', '--version', action='version', version='%(prog)s 4.1')
  return parser.parse_args()

# date, datetimeの変換関数
def json_serial(obj):
    # 日付型を文字列に変換
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    # 上記以外はサポート対象外
    raise TypeError ("Type %s not serializable" % type(obj))

# ログの設定
def setup_logger(is_debug):
  logger = getLogger("Main")
  logger.setLevel(DEBUG)
  # 標準出力
  sh = StreamHandler()
  sh.setLevel(INFO)
  sh.setFormatter(Formatter('[%(levelname)s] %(message)s'))
  logger.addHandler(sh)
  # デバッグログ
  if is_debug:
    fh = FileHandler(filename='{0}.log'.format(date.today()), encoding='utf-8')
    fh.setLevel(DEBUG)
    fh.setFormatter(Formatter('%(asctime)s - %(name)s - %(funcName)s - %(levelname)s - %(message)s'))
    logger.addHandler(fh)
  return logger

if __name__ == '__main__':
  main()
