import numpy as np
from iotdb.Session import Session
from iotdb.utils.IoTDBConstants import TSDataType, TSEncoding, Compressor
from iotdb.utils.Tablet import Tablet
from iotdb.utils.NumpyTablet import NumpyTablet

# 导入统一配置（从环境变量读取）
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))
from ecox.config import config

# 使用配置中的 IoTDB 参数
host = config.IOTDB_CONFIG["host"]
port = config.IOTDB_CONFIG["port"]
username = config.IOTDB_CONFIG["username"]
password = config.IOTDB_CONFIG["password"]

# 创建会话并连接
session = Session(host, port, username, password)
session.open(False)  # 参数False表示不启用RPC压缩
print("连接成功")

# ... (后续操作)

# 操作完成后关闭连接
# session.close()


# 设置存储组（类似于数据库）
session.set_storage_group("root.sg_test1")
# storage_group = "root.sg_test"
# 检查存储组是否已存在，不存在则创建
# if not session.check_storage_group_exists(storage_group):
#     session.set_storage_group(storage_group)
#     print(f"存储组 {storage_group} 创建成功。")
# else:
#     print(f"存储组 {storage_group} 已存在，跳过创建。")
# 定义设备ID和测点（传感器）
device_id = "root.sg_test.d_01"
measurements = ["temperature", "status", "voltage"]
data_types = [TSDataType.FLOAT, TSDataType.BOOLEAN, TSDataType.DOUBLE]
encodings = [TSEncoding.PLAIN, TSEncoding.PLAIN, TSEncoding.PLAIN]
compressors = [Compressor.SNAPPY] * 3  # 使用相同的压缩算法

# 创建多个时间序列
session.create_multi_time_series(
    device_id, 
    measurements, 
    data_types, 
    encodings, 
    compressors
)
print("时间序列创建完成")


# 准备数据：假设有4个时间点的数据
timestamps = np.array([1, 2, 3, 4], dtype=np.int64)
# 分别对应temperature, status, voltage的数据
values = [
    np.array([22.1, 22.3, 22.0, 22.5], dtype=np.float32),  # FLOAT
    np.array([True, True, False, True], dtype=np.bool_),    # BOOLEAN
    np.array([3.7, 3.8, 3.5, 3.9], dtype=np.float64)        # DOUBLE
]

# 创建NumpyTablet
tablet = NumpyTablet(
    device_id, 
    measurements, 
    data_types, 
    values, 
    timestamps
)

# 执行写入
session.insert_tablet(tablet)
print("数据写入完成")

# 执行查询语句
sql = "SELECT temperature, voltage FROM {} WHERE time >= 1 AND time <= 4".format(device_id)
session_data_set = session.execute_query_statement(sql)

# 转换为Pandas DataFrame
df = session_data_set.todf()
print("查询结果：")
print(df)

# 遍历原始结果集（备选方案）
# session_data_set = session.execute_query_statement(sql)
# while session_data_set.has_next():
#     print(session_data_set.next())


session.close()