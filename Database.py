from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine, Integer, JSON, Column, DATETIME, Text
from sqlalchemy.orm import sessionmaker
import datetime

EntityBase = declarative_base()

class DbManager(object):
  def __init__(self, dburl):
    self.engine = create_engine(dburl, echo=False)
    Session = sessionmaker(bind=self.engine)
    self.session = Session()
    EntityBase.metadata.create_all(self.engine)

  def InsertEvent(self, category, comment):
    event = Event()
    event.comment = comment
    event.category = category
    self.session.add(event)
    self.session.flush()
    return event.id

  def InsertItem(self, className, indict, eventid, account):
    # classの名前からModelクラスのインスタンスを生成する
    try:
      cls = globals()[className]
      item = cls()
    except Exception:
      raise ModelClassTypeError(className)
    try:
      item.id = eventid
      item.account = account
      item.info = indict
      self.session.add(item)
    except:
      self.session.close()
  
  def SelectItem(self, className, eventid):
    try:
      cls = globals()[className]
    except Exception:
      raise ModelClassTypeError(className)
    try:
      results = self.session.query(cls).filter(cls.id==eventid).all()
      return results[0]
    except Exception as e:
      self.session.close()
      raise DatabaseError(e)

  def ExecuteSql(self, query):
    try:
      results = self.session.execute(query)
    except Exception as e:
      self.session.close()
      raise DatabaseError(e)
    outlist = list()
    for r in results:
      outlist.append(r._asdict())
    return outlist

  def DbCommit(self):
    try:
      self.session.commit()
    except Exception as e:
      raise DatabaseError(e)
    finally:
      self.session.close()

class Event(EntityBase):
  __tablename__ = "Event"
  id = Column(Integer, autoincrement=True, primary_key=True, nullable=False)
  created_date = Column(DATETIME, default=datetime.datetime.now)
  category = Column(Text, nullable=True)
  comment = Column(Text, nullable=True)

class AwsFacts(EntityBase):
  __tablename__ = "AwsFacts"
  id = Column(Integer, primary_key=True, nullable=False)
  account = Column(Text, nullable=True)
  info = Column(JSON, nullable=True)

class ModelClassTypeError(Exception):
  """Modelクラスが未対応であることを知らせる例外クラス"""
  pass

class DatabaseError(Exception):
  """DBの処理に失敗したことを知らせる例外クラス"""
  pass