from Database import DbManager
import argparse
import yaml
import json
import csv
import os
import sys
import jmespath
from datetime import date
from deepdiff import DeepDiff
from logging import getLogger, StreamHandler, Formatter, FileHandler, DEBUG, INFO

# getコマンドの処理
def command_get(args, logger):
  logger.info("Event ID: %s のデータを取得" % args.event)
  # 設定ファイルの読み込み
  try:
    config = GetConfig(configfile=args.config)
  except Exception as e:
    logger.error('実行に失敗しました。設定ファイルの読み込みに失敗しました: %s' % e)
    sys.exit(1)

  # DBから指定したイベントIDのデータを取得
  try:
    dburl = config['database']['url']
  except (KeyError, TypeError):
    logger.error('実行に失敗しました。設定ファイルにデータベース接続情報が設定されていません。')
    sys.exit(1)
  try:
    datalist = GetDbData(dburl=dburl, events=args.event)
  except Exception as e:
    logger.error('実行に失敗しました。DBからのデータ取得に失敗しました: %s' % e)
    sys.exit(1)

  # queryオプションがあればJMESPathクエリを適用する
  if args.query is not None: datalist = ApplyQuery(datalist, args.query)
  # Factデータをファイルに出力
  try:
    OutPutFactData(outdir=args.outdir, events=args.event, datalist=datalist, ismerge=args.merge, logger=logger) 
  except Exception as e:
    logger.error('実行に失敗しました。取得結果を保存できませんでした: %s' % e)
    sys.exit(1)

# sqlコマンドの処理
def command_sql(args, logger):
  logger.info("SQLを実行")

  query = None
  if args.file is not None:
    # fileオプションがあればファイルからSQL文字列を取得
    try:
      with open(args.file, 'r', encoding='UTF-8') as sqlfile:
        query = sqlfile.read()
    except Exception as e:
      logger.error('実行に失敗しました。SQLファイルの読み込みに失敗しました: %s' % e)
      sys.exit(1)
  else:
    query = args.query
    
  # 設定ファイルの読み込み
  try:
    config = GetConfig(args.config)
  except Exception as e:
    logger.error('実行に失敗しました。設定ファイルの読み込みに失敗しました: %s' % e)
    sys.exit(1)

  # DBへの処理
  try:
    dburl = config['database']['url']
  except (KeyError, TypeError):
    logger.error('実行に失敗しました。設定ファイルにデータベース接続情報が設定されていません。')
    sys.exit(1)
  try:
    manager = DbManager(dburl)
    df = manager.ExecuteSql(query=query)
  except Exception as e:
    logger.error('実行に失敗しました。SQLの実行に失敗しました: %s' % e)
    sys.exit(1)

  try:
    # 出力フォルダを作成
    os.makedirs(args.outdir, exist_ok=True)
    if args.json:
      # jsonオプションがあればJSONファイルとして出力する
      with open(args.outdir+'/SQLResult.json', 'w', newline='') as of:
        if len(df):
          json.dump(df, of, indent=4)
        else:
          of.write("")
    else:
      # jsonオプションがなければCSVファイルとして出力する
      with open(args.outdir+"/SQLResult.csv", 'w', newline="") as f:
        if len(df):
          labels = df[0].keys()
          writer = csv.DictWriter(f, fieldnames=labels)
          writer.writeheader()
          for elem in df:
            writer.writerow(elem)
        else:
          f.write("")

  except Exception as e:
    logger.error('実行に失敗しました。実行結果を保存できませんでした: %s' % e)
    sys.exit(1)

# diffコマンドの処理
def command_diff(args, logger):
  logger.info("Event ID: %s, Event ID: %s の差分を取得" % (args.event1, args.event2))
  # 設定ファイルの読み込み
  try:
    config = GetConfig(configfile=args.config)
  except Exception as e:
    logger.error('実行に失敗しました。設定ファイルの読み込みに失敗しました: %s' % e)
    sys.exit(1)
  try:
    dburl = config['database']['url']
  except (KeyError, TypeError):
    logger.error('実行に失敗しました。設定ファイルにデータベース接続情報が設定されていません。')
    sys.exit(1)

  # 指定されたイベントIDのデータを取得
  eventlist = [args.event1, args.event2]
  try:
    datalist = GetDbData(dburl=dburl, events=eventlist)
  except Exception as e:
    logger.error('実行に失敗しました。DBからのデータ取得に失敗しました: %s' % e)
    sys.exit(1)

  # queryオプションがあればJMESPathクエリを適用する
  if args.query is not None:
    datalist = ApplyQuery(datalist, args.query)
  # Factデータをファイルに出力
  try:
    OutPutFactData(outdir=args.outdir, events=eventlist, datalist=datalist, ismerge=False, logger=logger)
  except Exception as e:
    logger.error('実行に失敗しました。取得結果を保存できませんでした: %s' % e)
    sys.exit(1)

  # diffデータをファイルに出力(DeepDiff)
  try:
    param = config['diff']['deepdiff']
    param['t1'] = datalist[0]
    param['t2'] = datalist[1]
    diff_data = DeepDiff(**param)
    logger.info("相違点を表示します\n" + diff_data.pretty())
    outfile = config['diff']['outputfile']
    with open(args.outdir + "/" + outfile, 'w') as of:
      of.write(diff_data.to_json(indent=4))
  except Exception as e:
    logger.error('実行に失敗しました。差分取得に失敗しました: %s' % e)
    sys.exit(1)

# 指定されたイベントIDのデータをDBから取得する
def GetDbData(dburl, events):
  # DBへの処理
  manager = DbManager(dburl)
  # FactsデータをDBから取得
  outdata = list()
  for event in events:
    data = manager.SelectItem(className='AwsFacts', eventid=int(event)).info
    outdata.append(data)
  return outdata

# JMESPathクエリを適用する
def ApplyQuery(datalist, query):
  new_datalist = list()
  for data in datalist:
    data = jmespath.search(query, data)
    new_datalist.append(data)
  return new_datalist

# 設定ファイルの読み込み
def GetConfig(configfile):
  with open(configfile, 'r') as yml:
    config = yaml.load(yml, Loader=yaml.SafeLoader)
  return config

# FactデータをJSONファイルに出力
def OutPutFactData(outdir, events, datalist, logger, ismerge=False):
  # 出力フォルダを作成
  os.makedirs(outdir, exist_ok=True)
  # FactsデータをJSONファイルに出力
  if ismerge:
    # Factデータを1つのJSONにマージして出力する
    factdata = dict()
    for event, data in zip(events, datalist):
      factdata['Event_'+event] = data
    with open(outdir+'/Facts.json', 'w') as of:
      json.dump(factdata, of, indent=4)
  else:
    # Factデータを1つずつファイルに出力する
    for event, data in zip(events, datalist):
      with open(outdir+'/event_'+event+'.json', 'w') as of:
        json.dump(data, of, indent=4)

def main():
  # コマンドライン引数をパースして対応する関数を実行
  parser = get_option()
  args = parser.parse_args()

  # ログの設定
  logger = setup_logger(args.debug)
  logger.debug("--------------------------------------------------------------------")

  if hasattr(args, 'func'):
    logger.info("実行を開始します。")
    args.func(args, logger)
  else:
    logger.error('実行に失敗しました。引数が不正です。')
    parser.print_help()
    exit(0)
  
  logger.info("実行を完了しました。")

# コマンド引数の設定
def get_option():
  parser = argparse.ArgumentParser(description='FactAnalyze - Factデータを分析するツール')
  parser.add_argument('-V', '--version', action='version', version='FactAnalyze 1.0')
  subparsers = parser.add_subparsers()
  # get コマンドの parser を作成
  parser_cgfrev = subparsers.add_parser('get', help='see `get -h`')
  eidlist = lambda x:list(map(str, x.split(',')))
  parser_cgfrev.add_argument('event', type=eidlist, help='IN: 取得データのイベントID(カンマ区切りで複数指定可能)')
  parser_cgfrev.add_argument('outdir', help='OUT: 結果出力フォルダ')
  parser_cgfrev.add_argument('-Q', '--query', help='抽出するJSONクエリ(JMESPath)')
  parser_cgfrev.add_argument('-M', '--merge', help='取得データを1つのJSONに統合', action='store_true')
  parser_cgfrev.add_argument('-C', '--config', default='AnalyzeConfig.yml', help='設定ファイル名')
  parser_cgfrev.add_argument('-D', '--debug', help='デバッグログを出力', action='store_true')
  parser_cgfrev.set_defaults(func=command_get)
  # diff コマンドの parser を作成
  parser_cgfrev = subparsers.add_parser('diff', help='see `diff -h`')
  parser_cgfrev.add_argument('event1', help='IN: 比較データ1 イベントID')
  parser_cgfrev.add_argument('event2', help='IN: 比較データ1 イベントID')
  parser_cgfrev.add_argument('outdir', help='OUT: 結果出力フォルダ')
  parser_cgfrev.add_argument('-Q', '--query', help='抽出するJSONクエリ(JMESPath)')
  parser_cgfrev.add_argument('-C', '--config', default='AnalyzeConfig.yml', help='設定ファイル名')
  parser_cgfrev.add_argument('-D', '--debug', help='デバッグログを出力', action='store_true')
  parser_cgfrev.set_defaults(func=command_diff)
  # sql コマンドの parser を作成
  parser_cgfrev = subparsers.add_parser('sql', help='see `sql -h`')
  parser_cgfrev.add_argument('outdir', help='OUT: 結果出力フォルダ')
  parser_cgfrev.add_argument('-Q', '--query', help='IN: 実行するSQLクエリの文字列')
  parser_cgfrev.add_argument('-F', '--file', help='IN: 実行するSQLクエリが書かれたファイル')  
  parser_cgfrev.add_argument('-J', '--json', help='JSONファイルとして出力', action='store_true')
  parser_cgfrev.add_argument('-C', '--config', default='AnalyzeConfig.yml', help='設定ファイル名')
  parser_cgfrev.add_argument('-D', '--debug', help='デバッグログを出力', action='store_true')
  parser_cgfrev.set_defaults(func=command_sql)
  return parser

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
