"""Optional SQL Server load. No credentials in source, logs or notebooks."""
import os
import re
import uuid
import pandas as pd
from sqlalchemy import create_engine,text
from .pipeline import ROOT

TABLES={"securities":("Security",["security_id"]),
        "performance":("MonthlyPerformance",["security_id","date"]),
        "macro":("Macro",["date"]),"pool_performance":("PoolPerformance",["deal_id","date"])}


def merge_sql(table,stage,columns,keys):
    # Only internal identifiers accepted; external values are loaded as bound data.
    for identifier in [table,stage,*columns,*keys]:
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*",identifier):
            raise ValueError("Invalid SQL identifier")
    join=" AND ".join(f"t.[{k}]=s.[{k}]" for k in keys)
    updates=", ".join(f"t.[{c}]=s.[{c}]" for c in columns if c not in keys)
    names=", ".join(f"[{c}]" for c in columns)
    values=", ".join(f"s.[{c}]" for c in columns)
    return f"MERGE dbo.[{table}] WITH (HOLDLOCK) AS t USING dbo.[{stage}] AS s ON {join} WHEN MATCHED THEN UPDATE SET {updates} WHEN NOT MATCHED THEN INSERT ({names}) VALUES ({values});"


def load(root=ROOT):
    url=os.environ.get("ABS_SQLSERVER_URL")
    if not url:
        raise ValueError("Set ABS_SQLSERVER_URL for your dedicated SQL Server database")
    engine=create_engine(url,hide_parameters=True)
    if engine.dialect.name!="mssql":
        raise ValueError("This loader requires Microsoft SQL Server")
    with engine.begin() as conn:
        for statement in re.split(r"^GO\s*$",(root/"sql/01_schema.sql").read_text(),flags=re.M):
            if statement.strip():conn.exec_driver_sql(statement)
        for filename,(table,keys) in TABLES.items():
            df=pd.read_csv(root/f"data/processed/{filename}.csv")
            if "date" in df:df["date"]=pd.to_datetime(df.date)
            stage="stage_abs_"+uuid.uuid4().hex
            df.to_sql(stage,conn,schema="dbo",index=False,chunksize=500)
            conn.execute(text(merge_sql(table,stage,list(df.columns),keys)))
            conn.exec_driver_sql(f"DROP TABLE dbo.[{stage}]")
            count=conn.execute(text(f"SELECT COUNT(*) FROM dbo.[{table}]")).scalar_one()
            if count!=len(df):
                raise ValueError("Unexpected existing rows; use a dedicated database with matching universe")
    engine.dispose()
    print("SQL Server load committed; all row counts reconciled.")

if __name__=="__main__":load()
