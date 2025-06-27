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

def list_db_contents(db_path, return_records=False):
    """格式化输出数据库所有记录，并可选返回记录列表"""
    conn = connect_db(db_path)
    if not conn:
        return []
    
    records = []
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT path, size, last_modified, updated_at FROM folder_sizes")
        raw_records = cursor.fetchall()
        
        if not raw_records:
            print("数据库中无缓存记录。")
            return []
        
        # 打印表头（新增序号列）
        print(f"{'序号':<5} | {'路径':<60} | {'大小':<20} | {'最后修改时间':<20} | {'更新时间':<20}")
        print("-" * 130)
        
        # 格式化每条记录并打印（添加序号）
        for idx, (path, size, last_modified, updated_at) in enumerate(raw_records, 1):
            last_modified_str = datetime.fromtimestamp(last_modified).strftime("%Y-%m-%d %H:%M:%S")
            updated_at_str = datetime.fromisoformat(updated_at).strftime("%Y-%m-%d %H:%M:%S")
            print(f"{idx:<5} | {path[:57]+'...' if len(path)>60 else path:<60} | {size:<20} | {last_modified_str:<20} | {updated_at_str:<20}")
            records.append((path, size, last_modified, updated_at))
        
        if return_records:
            return records
    except Exception as e:
        print(f"查询失败: {str(e)}")
    finally:
        conn.close()
    return records

def delete_single_record(db_path, target_path):
    """删除指定路径的单条记录"""
    conn = connect_db(db_path)
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM folder_sizes WHERE path = ?", (target_path,))
        deleted_count = cursor.rowcount
        conn.commit()
        return deleted_count > 0
    except Exception as e:
        print(f"删除失败: {str(e)}")
        return False
    finally:
        conn.close()

def main():
    parser = argparse.ArgumentParser(description="文件夹大小数据库管理工具")
    parser.add_argument("--db-path", default="userdata/db/folder_size.db", 
                       help="数据库文件路径（默认：userdata/db/folder_size.db）")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--list", action="store_true", help="列出所有缓存记录")
    group.add_argument("--clean", type=int, nargs="?", const=-1, 
                       help="清理缓存（无参数清理所有，带参数清理指定天数前的记录，如--clean 30）")
    group.add_argument("--delete", action="store_true", help="逐条选择删除记录")  # 新增参数

    args = parser.parse_args()

    if args.list:
        list_db_contents(args.db_path)
    # elif args.clean is not None:
    #     clean_db(args.db_path, args.clean if args.clean != -1 else None)
    elif args.delete:  # 新增逐条删除逻辑
        records = list_db_contents(args.db_path, return_records=True)
        if not records:
            return
        while True:
            try:
                idx_input = input("\n请输入要删除的记录序号（输入0返回）: ")
                if idx_input.strip() == '0':
                    print("退出逐条删除模式。")
                    break
                idx = int(idx_input)
                if idx < 1 or idx > len(records):
                    print("错误：序号超出范围，请重新输入。")
                    continue
                # 获取目标路径
                target_path = records[idx-1][0]
                # 确认删除
                confirm = input(f"确认删除以下记录？\n路径: {target_path}\n输入 'y' 确认，其他取消: ").strip().lower()
                if confirm == 'y':
                    success = delete_single_record(args.db_path, target_path)
                    if success:
                        print(f"成功删除序号 {idx} 的记录。")
                        # 刷新记录列表（删除后重新查询）
                        records = list_db_contents(args.db_path, return_records=True)
                        if not records:
                            print("数据库已无记录，退出逐条删除模式。")
                            break
                    else:
                        print("删除失败，可能记录已不存在。")
                else:
                    print("已取消删除。")
            except ValueError:
                print("错误：请输入有效的数字序号。")

if __name__ == "__main__":
    main()
