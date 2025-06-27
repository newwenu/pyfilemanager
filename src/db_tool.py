import sqlite3
import argparse
from datetime import datetime, timedelta

def connect_db(db_path):
    """连接到数据库（处理异常）"""
    try:
        return sqlite3.connect(db_path)
    except Exception as e:
        print(f"连接数据库失败: {str(e)}")
        return None

def list_db_contents(db_path):
    """格式化输出数据库所有记录"""
    conn = connect_db(db_path)
    if not conn:
        return
    
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT path, size, last_modified, updated_at FROM folder_sizes")
        records = cursor.fetchall()
        
        if not records:
            print("数据库中无缓存记录。")
            return
        
        # 打印表头
        print(f"{'路径':<60} | {'大小':<20} | {'最后修改时间':<20} | {'更新时间':<20}")
        print("-" * 120)
        
        # 格式化每条记录
        for path, size, last_modified, updated_at in records:
            last_modified_str = datetime.fromtimestamp(last_modified).strftime("%Y-%m-%d %H:%M:%S")
            updated_at_str = datetime.fromisoformat(updated_at).strftime("%Y-%m-%d %H:%M:%S")
            print(f"{path[:57]+'...' if len(path)>60 else path:<60} | {size:<20} | {last_modified_str:<20} | {updated_at_str:<20}")
    except Exception as e:
        print(f"查询失败: {str(e)}")
    finally:
        conn.close()

def clean_db(db_path, days=None):
    """清理数据库记录（支持全量清理或按时间清理）"""
    conn = connect_db(db_path)
    if not conn:
        return
    
    try:
        cursor = conn.cursor()
        if days is None:
            # 清理所有记录
            cursor.execute("DELETE FROM folder_sizes")
            msg = "所有"
        else:
            # 清理指定天数前的记录
            cutoff = datetime.now() - timedelta(days=days)
            cursor.execute("DELETE FROM folder_sizes WHERE updated_at < ?", (cutoff.isoformat(),))
            msg = f"超过{days}天未更新的"
        
        deleted_count = cursor.rowcount
        conn.commit()
        print(f"成功清理{msg}缓存记录，共删除{deleted_count}条。")
    except Exception as e:
        print(f"清理失败: {str(e)}")
    finally:
        conn.close()

def main():
    # 命令行参数解析
    parser = argparse.ArgumentParser(description="文件夹大小数据库管理工具")
    parser.add_argument("--db-path", default="userdata/db/folder_size.db", 
                       help="数据库文件路径（默认：userdata/db/folder_size.db）")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--list", action="store_true", help="列出所有缓存记录")
    group.add_argument("--clean", type=int, nargs="?", const=-1, 
                       help="清理缓存（无参数清理所有，带参数清理指定天数前的记录，如--clean 30）")
    
    args = parser.parse_args()
    
    if args.list:
        list_db_contents(args.db_path)
    elif args.clean is not None:
        clean_db(args.db_path, args.clean if args.clean != -1 else None)

if __name__ == "__main__":
    main()
